"""
Comprehensive Non-Regression Test Suite for v3.0 Extensions (Lots A, B, C, D, E):
- Lot A: Full ThingsBoard Provisioning (Site Assets, Contains Relations, ISA-101 Alarm Profiles, 70 Widgets Push)
- Lot B: Historical Time-Series Backfill (7/30/90 days, 3-pass causal physics, batched REST ingestion)
- Lot C: Pure-Python Asyncio Modbus TCP Server (0x01/0x03/0x05/0x10) & ThingsBoard IoT Gateway modbus.json
- Lot D: Visual ISA-101 Synoptic Studio (custom_synoptic_nodes override & live preview)
- Lot E: 1-Click Bid Pack (.ZIP) & Multi-Device Stress-Test (`dp/s` benchmark)
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import struct
import tempfile
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.backfill_engine import (
    BackfillRequest,
    execute_device_backfill,
    generate_historical_points,
)
from app.core.bid_deliverables import generate_io_list_csv
from app.core.bid_package import build_bid_pack_zip
from app.core.dashboard_generator import generate_thingsboard_dashboard
from app.core.scada_synoptics import get_scada_synoptic_html, render_custom_synoptic_preview
from app.core.stress_test import StressTestManager, StressTestRequest
from app.core.tb_provisioner import (
    TbProvisionRequest,
    build_isa101_device_profile,
    tb_provision_stack,
)
from app.models.device import DeviceConfig, PlatformType, TransportProtocol
from app.models.variable import (
    DataType,
    DerivedConfig,
    IntegratorConfig,
    MathConfig,
    SimMode,
    VariableConfig,
    VariableType,
)
from app.storage.repository import StorageRepository
from app.transports.modbus_server import (
    AsyncModbusTcpServer,
    build_modbus_register_map,
    generate_tb_gateway_modbus_config,
)


def _sample_device_and_vars():
    dev = DeviceConfig(
        id="ind_comp_01",
        name="Compresseur Atelier 1",
        protocol=TransportProtocol.HTTP,
        platform=PlatformType.THINGSBOARD,
        token="TB_DEMO_TOKEN_123",
        custom_host="tb.example.com",
        custom_port=443,
        use_tls=True,
    )
    vars_list = [
        VariableConfig(
            id="ind_comp_01_puissance_kw",
            name="Puissance Active",
            device_id=dev.id,
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="kW",
            sim_mode=SimMode.SINE,
            math_config=MathConfig(min_val=20.0, max_val=60.0, period=3600.0),
            current_value=42.5,
        ),
        VariableConfig(
            id="ind_comp_01_cout_horaire",
            name="Coût Horaire",
            device_id=dev.id,
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="€/h",
            sim_mode=SimMode.DERIVED,
            derived_config=DerivedConfig(formula="puissance_kw * 0.18"),
        ),
        VariableConfig(
            id="ind_comp_01_energie_kwh",
            name="Énergie Cumulée",
            device_id=dev.id,
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="kWh",
            sim_mode=SimMode.INTEGRATOR,
            integrator_config=IntegratorConfig(source_variable_id="puissance_kw", time_unit="hour", multiplier=1.0),
        ),
        VariableConfig(
            id="ind_comp_01_etat_marche",
            name="Marche / Arrêt",
            device_id=dev.id,
            var_type=VariableType.ATTRIBUTE,
            data_type=DataType.BOOLEAN,
            sim_mode=SimMode.CONSTANT,
            current_value=True,
        ),
    ]
    return dev, vars_list


# =========================================================================
# LOT A: Full ThingsBoard Provisioning (Assets, Alarm Profiles, 70 Widgets)
# =========================================================================

def test_lot_a_isa101_alarm_profile_and_full_tb_provisioning():
    dev, vars_list = _sample_device_and_vars()
    profile = build_isa101_device_profile(dev, vars_list)
    assert profile is not None
    assert profile["name"] == f"ISA101_Profile_{dev.id}"
    alarms = profile["profileData"]["alarms"]
    assert len(alarms) == 1
    assert "WARNING" in alarms[0]["createRules"]
    assert "CRITICAL" in alarms[0]["createRules"]
    assert alarms[0]["propagate"] is True

    tmp_dir = tempfile.mkdtemp()
    repo = StorageRepository(file_path=os.path.join(tmp_dir, "lot_a_db.json"))
    repo.save_device(dev)
    for v in vars_list:
        repo.save_variable(v)

    def _resp(code: int, body: dict):
        m = MagicMock()
        m.status_code = code
        m.json.return_value = body
        m.text = json.dumps(body)
        return m

    posted_paths = []

    async def _run():
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        async def _post(url, **kwargs):
            posted_paths.append(url)
            if url.endswith("/api/asset"):
                return _resp(200, {"id": {"id": "asset_uuid_01"}})
            if url.endswith("/api/deviceProfile"):
                return _resp(200, {"id": {"id": "prof_uuid_01"}})
            if url.endswith("/api/device"):
                return _resp(200, {"id": {"id": "dev_uuid_01"}})
            if url.endswith("/api/relation"):
                return _resp(200, {})
            if url.endswith("/api/widgetsBundle"):
                return _resp(200, {"alias": "scada_isa101_modular"})
            if url.endswith("/api/widgetType"):
                return _resp(200, {"id": {"id": "wt_uuid"}})
            if url.endswith("/api/dashboard"):
                return _resp(200, {"id": {"id": "dash_uuid_01"}})
            return _resp(200, {})

        async def _get(url, **kwargs):
            if "/api/tenant/devices" in url:
                return _resp(404, {})
            if "/credentials" in url:
                return _resp(200, {"credentialsId": "SYNCED_TOK_A"})
            return _resp(404, {})

        mock_client.post.side_effect = _post
        mock_client.get.side_effect = _get

        with patch("app.core.tb_provisioner.httpx.AsyncClient", return_value=mock_client, create=True):
            res = await tb_provision_stack(
                TbProvisionRequest(
                    tb_url="https://tb.example.com",
                    access_token="jwt_tok",
                    device_ids=[dev.id],
                    create_site_asset=True,
                    site_asset_name="Usine Pilote",
                    create_alarm_profiles=True,
                    push_isa101_widgets=True,
                    push_dashboards=True,
                ),
                repo=repo,
            )
            assert res["site_asset_id"] == "asset_uuid_01"
            assert res["alarm_profiles_count"] == 1
            assert res["widgets_pushed_count"] == 70
            assert any(p.endswith("/api/relation") for p in posted_paths)

    asyncio.run(_run())


# =========================================================================
# LOT B: Historical Time-Series Backfill (7/30/90 days + 3-pass physics)
# =========================================================================

def test_lot_b_historical_backfill_physics_and_batch_ingestion():
    dev, vars_list = _sample_device_and_vars()
    records = generate_historical_points(dev, vars_list, days=2, step_minutes=60, include_anomalies=True)
    assert len(records) == 49  # 48h / 1h + 1
    assert records[0]["ts"] < records[-1]["ts"]
    # Verify derived variable & monotonic trapezoidal integrator
    assert "cout_horaire" in records[-1]["values"]
    assert records[-1]["values"]["energie_kwh"] > records[0]["values"]["energie_kwh"]

    tmp_dir = tempfile.mkdtemp()
    repo = StorageRepository(file_path=os.path.join(tmp_dir, "lot_b_db.json"))
    repo.save_device(dev)
    for v in vars_list:
        repo.save_variable(v)

    mock_http = AsyncMock()
    mock_http.post_payload.return_value = (True, "HTTP 200 OK")

    async def _run():
        dry = await execute_device_backfill(
            dev.id,
            BackfillRequest(days=2, step_minutes=60, dry_run=True),
            repo=repo,
        )
        assert dry["status"] == "dry_run"
        assert dry["points_generated"] == 49

        live = await execute_device_backfill(
            dev.id,
            BackfillRequest(days=2, step_minutes=60, batch_size=20, dry_run=False),
            repo=repo,
            http_client=mock_http,
        )
        assert live["status"] == "completed"
        assert live["batches_sent"] == 3  # 20 + 20 + 9
        assert mock_http.post_payload.call_count == 3

    asyncio.run(_run())


# =========================================================================
# LOT C: Pure-Python Asyncio Modbus TCP Server & Gateway Config
# =========================================================================

def test_lot_c_modbus_tcp_server_live_read_write_and_gateway_export():
    dev, vars_list = _sample_device_and_vars()
    reg_map = build_modbus_register_map([dev], vars_list)
    assert 1 in reg_map["units"]
    assert len(reg_map["units"][1]["holding_registers"]) == 3
    assert len(reg_map["units"][1]["coils"]) == 1

    gw_cfg = generate_tb_gateway_modbus_config([dev], vars_list, host="127.0.0.1", port=5020)
    assert len(gw_cfg["master"]["slaves"]) == 1
    assert gw_cfg["master"]["slaves"][0]["unitId"] == 1
    assert len(gw_cfg["master"]["slaves"][0]["timeseries"]) == 3
    assert len(gw_cfg["master"]["slaves"][0]["rpc"]) == 1

    # Verify IO List CSV includes Modbus TCP column
    csv_out = generate_io_list_csv([dev], vars_list)
    assert "Registre Modbus TCP" in csv_out
    assert "HR 40001" in csv_out

    tmp_dir = tempfile.mkdtemp()
    repo = StorageRepository(file_path=os.path.join(tmp_dir, "lot_c_db.json"))
    for existing in repo.get_devices():
        repo.delete_device(existing.id)
    repo.save_device(dev)
    for v in vars_list:
        repo.save_variable(v)

    async def _run():
        server = AsyncModbusTcpServer(repo)
        st = await server.start(host="127.0.0.1", port=0)
        assert st["running"] is True
        bound_port = st["port"]

        reader, writer = await asyncio.open_connection("127.0.0.1", bound_port)
        try:
            # 1. Read Holding Registers (FC 0x03, Unit 1, Addr 0, Count 2 -> Float32 = 42.5)
            req_hr = struct.pack(">HHHBBHH", 1, 0, 6, 1, 0x03, 0, 2)
            writer.write(req_hr)
            await writer.drain()
            hdr = await reader.readexactly(6)
            _, _, length = struct.unpack(">HHH", hdr)
            body = await reader.readexactly(length)
            assert body[1] == 0x03
            val_f32 = struct.unpack(">f", body[3:7])[0]
            assert abs(val_f32 - 42.5) < 0.01

            # 2. Write Single Coil (FC 0x05, Unit 1, Coil 0 -> OFF = 0x0000)
            req_coil = struct.pack(">HHHBBHH", 2, 0, 6, 1, 0x05, 0, 0x0000)
            writer.write(req_coil)
            await writer.drain()
            hdr2 = await reader.readexactly(6)
            _, _, length2 = struct.unpack(">HHH", hdr2)
            await reader.readexactly(length2)

            updated_var = repo.get_variable("ind_comp_01_etat_marche")
            assert updated_var.current_value is False
            assert updated_var.manual_override is True
        finally:
            writer.close()
            await writer.wait_closed()
            await server.stop()

    asyncio.run(_run())


# =========================================================================
# LOT D: Visual ISA-101 Synoptic Studio (Custom Layouts)
# =========================================================================

def test_lot_d_synoptic_studio_custom_layout_override():
    dev, vars_list = _sample_device_and_vars()
    custom_nodes = [
        {"component_id": "proc_screw_compressor", "var_key": "puissance_kw", "label": "Compresseur Custom"},
        {"component_id": "elec_power_analyzer", "var_key": "cout_horaire", "label": "Coût Élec"},
    ]
    preview_html = render_custom_synoptic_preview("APERÇU STUDIO", custom_nodes, vars_list)
    assert "Compresseur Custom" in preview_html
    assert "#E5E7EB" in preview_html
    assert "<svg" in preview_html

    dev.custom_synoptic_nodes = custom_nodes
    synoptic_html = get_scada_synoptic_html(dev, vars_list)
    assert "SYNOPTIQUE STUDIO ISA-101" in synoptic_html
    assert "Compresseur Custom" in synoptic_html

    dash = generate_thingsboard_dashboard(dev, vars_list)
    assert "Compresseur Custom" in json.dumps(dash)


# =========================================================================
# LOT E: 1-Click Bid Pack (.ZIP) & Multi-Device Stress-Test (`dp/s`)
# =========================================================================

def test_lot_e_bid_pack_zip_and_stress_test():
    dev, vars_list = _sample_device_and_vars()
    zip_bytes = build_bid_pack_zip([dev], vars_list)

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        names = set(zf.namelist())
        assert "01_IO_List_Points.csv" in names
        assert "02_Dossier_Architecture_IoT.md" in names
        assert "03_ThingsBoard_IoT_Gateway_modbus.json" in names
        assert "04_Widgets_ISA101_Bundle_70.json" in names
        assert f"dashboards/{dev.id}_dashboard.json" in names

    async def _run_stress():
        mgr = StressTestManager()
        await mgr.start(
            StressTestRequest(
                virtual_devices=50,
                variables_per_device=8,
                interval_sec=0.5,
                duration_sec=1,
                dry_run=True,
            )
        )
        await asyncio.sleep(0.45)
        st = await mgr.stop()
        assert st["running"] is False
        assert st["total_messages"] > 0
        assert st["total_data_points"] == st["total_messages"] * 8
        assert st["achieved_dp_per_sec"] > 0
        assert st["errors"] == 0

    asyncio.run(_run_stress())
