"""
Lightweight Pure-Python Asyncio Modbus TCP Slave Server & ThingsBoard IoT Gateway Exporter.

Exposes active simulator devices and variables as standard Modbus TCP registers
on a non-privileged user port (default: 127.0.0.1:5020, zero admin rights required):
- Numeric telemetry variables -> Holding / Input Registers (IEEE-754 Float32 Big-Endian, 2 registers each)
- Boolean / controllable attributes -> Coils (Read/Write 0x01 / 0x05)

Also generates a ready-to-import `modbus.json` configuration for ThingsBoard IoT Gateway.
"""

from __future__ import annotations

import asyncio
import logging
import struct
from typing import Any, Dict, List, Optional, Tuple

from app.core.scada_synoptics import get_clean_var_key
from app.models.device import DeviceConfig
from app.models.variable import DataType, VariableConfig, VariableType
from app.storage.repository import StorageRepository

logger = logging.getLogger("iot_sim.modbus")


def build_modbus_register_map(
    devices: List[DeviceConfig],
    variables: List[VariableConfig],
) -> Dict[str, Any]:
    """Builds a deterministic Modbus TCP register & coil address map for all devices."""
    vars_by_dev: Dict[str, List[VariableConfig]] = {}
    for v in variables:
        vars_by_dev.setdefault(v.device_id, []).append(v)

    device_maps: Dict[int, Dict[str, Any]] = {}
    var_lookup: Dict[str, Dict[str, Any]] = {}

    for idx, dev in enumerate(devices, start=1):
        unit_id = idx
        d_vars = vars_by_dev.get(dev.id, [])
        holding_regs: List[Dict[str, Any]] = []
        coils: List[Dict[str, Any]] = []
        next_reg = 0
        next_coil = 0

        for v in d_vars:
            clean_key = get_clean_var_key(v)
            if v.data_type == DataType.BOOLEAN:
                entry = {
                    "unit_id": unit_id,
                    "variable_id": v.id,
                    "tag": clean_key,
                    "name": v.name,
                    "kind": "coil",
                    "address": next_coil,
                    "modbus_ref": f"0x{next_coil:04X} (Coil {next_coil + 1:05d})",
                    "objects_count": 1,
                    "data_type": "bits",
                }
                coils.append(entry)
                var_lookup[v.id] = entry
                next_coil += 1
            elif v.data_type in (DataType.FLOAT, DataType.INTEGER):
                entry = {
                    "unit_id": unit_id,
                    "variable_id": v.id,
                    "tag": clean_key,
                    "name": v.name,
                    "kind": "holding_register",
                    "address": next_reg,
                    "modbus_ref": f"HR {40001 + next_reg} (Float32, 2 regs)",
                    "objects_count": 2,
                    "data_type": "32float",
                    "unit": v.unit or "",
                }
                holding_regs.append(entry)
                var_lookup[v.id] = entry
                next_reg += 2

        device_maps[unit_id] = {
            "unit_id": unit_id,
            "device_id": dev.id,
            "device_name": dev.name,
            "holding_registers": holding_regs,
            "coils": coils,
        }

    return {"units": device_maps, "by_variable_id": var_lookup}


def generate_tb_gateway_modbus_config(
    devices: List[DeviceConfig],
    variables: List[VariableConfig],
    host: str = "127.0.0.1",
    port: int = 5020,
) -> Dict[str, Any]:
    """Generates a ready-to-import ThingsBoard IoT Gateway `modbus.json` connector config."""
    reg_map = build_modbus_register_map(devices, variables)
    slaves = []

    for unit_id, unit_info in reg_map["units"].items():
        timeseries = [
            {
                "tag": r["tag"],
                "type": r["data_type"],
                "functionCode": 3,
                "objectsCount": r["objects_count"],
                "address": r["address"],
            }
            for r in unit_info["holding_registers"]
        ]
        attributes = [
            {
                "tag": c["tag"],
                "type": "bits",
                "functionCode": 1,
                "objectsCount": 1,
                "address": c["address"],
            }
            for c in unit_info["coils"]
        ]
        rpc = [
            {
                "tag": f"set_{c['tag']}",
                "type": "bits",
                "functionCode": 5,
                "objectsCount": 1,
                "address": c["address"],
            }
            for c in unit_info["coils"]
        ]
        slaves.append({
            "host": host,
            "port": port,
            "type": "tcp",
            "method": "socket",
            "unitId": unit_id,
            "deviceName": unit_info["device_name"],
            "deviceType": "default",
            "pollPeriod": 5000,
            "byteOrder": "BIG",
            "wordOrder": "BIG",
            "timeseries": timeseries,
            "attributes": attributes,
            "rpc": rpc,
        })

    return {"master": {"slaves": slaves}}


class AsyncModbusTcpServer:
    """Pure-Python asyncio Modbus TCP slave server backed live by StorageRepository."""

    def __init__(self, repo: StorageRepository) -> None:
        self.repo = repo
        self._server: Optional[asyncio.AbstractServer] = None
        self.host: str = "127.0.0.1"
        self.port: int = 5020
        self.requests_served: int = 0

    @property
    def is_running(self) -> bool:
        return self._server is not None and self._server.is_serving()

    async def start(self, host: str = "127.0.0.1", port: int = 5020) -> Dict[str, Any]:
        if self.is_running:
            return self.status()
        self.host = host
        self.port = port
        self._server = await asyncio.start_server(self._handle_client, host, port)
        # Resolve actual bound port if port=0 was passed
        sockets = self._server.sockets or []
        if sockets:
            self.port = int(sockets[0].getsockname()[1])
        logger.info(f"Modbus TCP server started on {self.host}:{self.port}")
        return self.status()

    async def stop(self) -> Dict[str, Any]:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            logger.info("Modbus TCP server stopped.")
        return self.status()

    def status(self) -> Dict[str, Any]:
        devices = self.repo.get_devices()
        variables = self.repo.get_variables()
        reg_map = build_modbus_register_map(devices, variables)
        return {
            "running": self.is_running,
            "host": self.host,
            "port": self.port,
            "requests_served": self.requests_served,
            "units_count": len(reg_map["units"]),
            "mapped_variables": len(reg_map["by_variable_id"]),
        }

    def _build_register_words(self, unit_id: int) -> Tuple[List[int], List[bool], Dict[int, str], Dict[int, str]]:
        devices = self.repo.get_devices()
        variables = self.repo.get_variables()
        var_by_id = {v.id: v for v in variables}
        reg_map = build_modbus_register_map(devices, variables)
        unit = reg_map["units"].get(unit_id)
        if not unit:
            return [], [], {}, {}

        max_reg = sum(r["objects_count"] for r in unit["holding_registers"])
        words = [0] * max(2, max_reg)
        reg_var_owner: Dict[int, str] = {}
        for r in unit["holding_registers"]:
            v = var_by_id.get(r["variable_id"])
            val = 0.0
            if v is not None:
                if v.current_value is not None and isinstance(v.current_value, (int, float)):
                    val = float(v.current_value)
                elif v.math_config:
                    val = (v.math_config.min_val + v.math_config.max_val) / 2.0
            packed = struct.pack(">f", val)
            hi, lo = struct.unpack(">HH", packed)
            addr = r["address"]
            words[addr] = hi
            words[addr + 1] = lo
            reg_var_owner[addr] = r["variable_id"]

        coils: List[bool] = []
        coil_var_owner: Dict[int, str] = {}
        for c in unit["coils"]:
            v = var_by_id.get(c["variable_id"])
            bit = bool(v.current_value) if (v and v.current_value is not None) else False
            coils.append(bit)
            coil_var_owner[c["address"]] = c["variable_id"]

        return words, coils, reg_var_owner, coil_var_owner

    def process_adu(self, adu: bytes) -> bytes:
        """Processes a single raw Modbus TCP ADU (MBAP + PDU) and returns the response ADU."""
        if len(adu) < 8:
            return b""
        tx_id, proto_id, _length, unit_id = struct.unpack(">HHHB", adu[:7])
        pdu = adu[7:]
        fc = pdu[0]
        self.requests_served += 1

        words, coils, reg_owner, coil_owner = self._build_register_words(unit_id)

        def _wrap(resp_pdu: bytes) -> bytes:
            return struct.pack(">HHHB", tx_id, proto_id, len(resp_pdu) + 1, unit_id) + resp_pdu

        # 0x01 Read Coils
        if fc == 0x01 and len(pdu) >= 5:
            start_addr, count = struct.unpack(">HH", pdu[1:5])
            byte_count = (count + 7) // 8
            out = bytearray(byte_count)
            for i in range(count):
                idx = start_addr + i
                if idx < len(coils) and coils[idx]:
                    out[i // 8] |= 1 << (i % 8)
            return _wrap(struct.pack(">BB", fc, byte_count) + bytes(out))

        # 0x03 Read Holding Registers / 0x04 Read Input Registers
        if fc in (0x03, 0x04) and len(pdu) >= 5:
            start_addr, count = struct.unpack(">HH", pdu[1:5])
            slice_words = [words[start_addr + i] if (start_addr + i) < len(words) else 0 for i in range(count)]
            payload = struct.pack(f">{len(slice_words)}H", *slice_words)
            return _wrap(struct.pack(">BB", fc, len(payload)) + payload)

        # 0x05 Write Single Coil
        if fc == 0x05 and len(pdu) >= 5:
            coil_addr, raw_val = struct.unpack(">HH", pdu[1:5])
            new_bool = raw_val == 0xFF00
            var_id = coil_owner.get(coil_addr)
            if var_id:
                v = self.repo.get_variable(var_id)
                if v:
                    v.manual_override = True
                    v.manual_value = new_bool
                    v.current_value = new_bool
                    self.repo.save_variable(v)
            return _wrap(pdu[:5])

        # 0x06 Write Single Register (integer setpoint)
        if fc == 0x06 and len(pdu) >= 5:
            reg_addr, raw_val = struct.unpack(">HH", pdu[1:5])
            var_id = reg_owner.get(reg_addr)
            if var_id:
                v = self.repo.get_variable(var_id)
                if v:
                    v.manual_override = True
                    v.manual_value = float(raw_val)
                    v.current_value = float(raw_val)
                    self.repo.save_variable(v)
            return _wrap(pdu[:5])

        # 0x10 Write Multiple Registers (Float32 Big-Endian)
        if fc == 0x10 and len(pdu) >= 7:
            start_addr, count, byte_count = struct.unpack(">HHB", pdu[1:6])
            reg_bytes = pdu[6 : 6 + byte_count]
            var_id = reg_owner.get(start_addr)
            if var_id and len(reg_bytes) >= 4:
                float_val = round(struct.unpack(">f", reg_bytes[:4])[0], 3)
                v = self.repo.get_variable(var_id)
                if v:
                    v.manual_override = True
                    v.manual_value = float_val
                    v.current_value = float_val
                    self.repo.save_variable(v)
            return _wrap(struct.pack(">BHH", fc, start_addr, count))

        # Illegal function exception (0x01)
        return _wrap(struct.pack(">BB", fc | 0x80, 0x01))

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                header = await reader.readexactly(6)
                _tx, _proto, length = struct.unpack(">HHH", header)
                body = await reader.readexactly(length)
                resp = self.process_adu(header + body)
                if resp:
                    writer.write(resp)
                    await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionResetError, OSError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
