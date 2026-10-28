"""
Thread-Safe Persistent JSON Storage Repository for Devices and Variables.

This module provides atomic, thread-safe JSON persistence for simulation models:
- Broker connection configuration (`BrokerConfig`).
- Device entities (`DeviceConfig`).
- Telemetry and attribute variables (`VariableConfig`).

Fault Tolerance & Resilience Architecture:
- Thread Safety: Mutex lock (`threading.Lock`) protects all reads, mutations, and serialization.
- Atomic Persistence: Writes to a temporary staging file (`.tmp`) before calling `os.replace`
  to guarantee zero partial/corrupted writes during unexpected power cuts or container crashes.
- Dual Automatic Backup: Updates a secondary `.bak` mirror on every valid save.
  Restores automatically from `.bak` if the main file is missing or corrupted.
- Quarantine: Corrupted files are safely preserved as `.corrupted.<timestamp>` for post-mortem analysis.
- Resilient Deserialization: Validates with Pydantic; falls back to `model_construct` to preserve
  user-defined data even across schema migrations.
"""

import json
import logging
import os
import threading
from typing import Dict, List, Optional
from app.models.broker import BrokerConfig
from app.models.device import DeviceConfig, PlatformType
from app.models.variable import (
    VariableConfig,
    VariableType,
    DataType,
    SimMode,
    MathConfig,
    PointsTableConfig,
    TimestampedPoint,
)

logger = logging.getLogger("iot_sim.storage")

class StorageRepository:
    """
    Thread-safe persistent storage repository managing devices, variables, and broker configuration.

    Attributes:
        file_path: Filesystem path to primary JSON storage file.
        broker_config: Current active BrokerConfig instance.
        devices: In-memory dictionary mapping device IDs to DeviceConfig instances.
        variables: In-memory dictionary mapping variable IDs to VariableConfig instances.
    """

    def __init__(self, file_path: str = "data/simulator_state.json") -> None:
        """
        Initializes the storage repository and loads existing data from disk.

        Args:
            file_path: Path to target JSON state file. Defaults to 'data/simulator_state.json'.
        """
        self.file_path: str = file_path
        self._lock: threading.Lock = threading.Lock()
        self.broker_config: BrokerConfig = BrokerConfig()
        self.devices: Dict[str, DeviceConfig] = {}
        self.variables: Dict[str, VariableConfig] = {}
        self.load()

    def load(self) -> None:
        """
        Loads and validates simulation state from the persistent JSON file.

        Features automated recovery from `.bak` backup if the main file is missing or corrupted.
        Bootstraps initial demo devices if no configuration exists.
        """
        with self._lock:
            if not os.path.exists(self.file_path):
                # Check for automatic backup
                bak_path = f"{self.file_path}.bak"
                if os.path.exists(bak_path):
                    logger.warning(f"Primary file {self.file_path} missing; attempting restoration from {bak_path}")
                    try:
                        import shutil
                        shutil.copy2(bak_path, self.file_path)
                    except Exception as e:
                        logger.error(f"Error copying backup file: {e}")
                else:
                    logger.info(f"State file does not exist ({self.file_path}); initializing default demonstration scenarios.")
                    self._init_defaults()
                    self._save_unsafe()
                    return

            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if "broker" in data and isinstance(data["broker"], dict):
                    try:
                        self.broker_config = BrokerConfig.model_validate(data["broker"])
                    except Exception as e:
                        logger.warning(f"Invalid broker configuration; retaining defaults: {e}")

                self.devices.clear()
                for d in data.get("devices", []):
                    try:
                        dev = DeviceConfig.model_validate(d)
                        self.devices[dev.id] = dev
                    except Exception as e:
                        logger.warning(f"Strict validation failed for device {d.get('id', 'unknown')}: {e}. Loading resiliently.")
                        try:
                            self.devices[d["id"]] = DeviceConfig.model_construct(**d)
                        except Exception:
                            pass

                self.variables.clear()
                for v in data.get("variables", []):
                    try:
                        var = VariableConfig.model_validate(v)
                        self.variables[var.id] = var
                    except Exception as e:
                        logger.warning(f"Strict validation failed for variable {v.get('id', 'unknown')}: {e}. Loading resiliently.")
                        try:
                            self.variables[v["id"]] = VariableConfig.model_construct(**v)
                        except Exception:
                            pass

                logger.info(f"✓ Loaded {len(self.devices)} device(s) and {len(self.variables)} variable(s) from {self.file_path}")

                # Refresh secure backup
                try:
                    import shutil
                    shutil.copy2(self.file_path, f"{self.file_path}.bak")
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"Critical error reading {self.file_path}: {e}")
                import time
                try:
                    import shutil
                    corrupt_path = f"{self.file_path}.corrupted.{int(time.time())}"
                    shutil.copy2(self.file_path, corrupt_path)
                    logger.warning(f"Original corrupted file preserved at {corrupt_path}")
                except Exception:
                    pass

                # Attempt recovery from .bak
                bak_path = f"{self.file_path}.bak"
                if os.path.exists(bak_path):
                    logger.warning(f"Attempting emergency automatic restoration from backup {bak_path}")
                    try:
                        with open(bak_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        self.devices.clear()
                        for d in data.get("devices", []):
                            self.devices[d["id"]] = DeviceConfig.model_construct(**d)
                        self.variables.clear()
                        for v in data.get("variables", []):
                            self.variables[v["id"]] = VariableConfig.model_construct(**v)
                        return
                    except Exception as be:
                        logger.error(f"Backup restoration failed: {be}")

                logger.error("Restoration impossible; initializing default demonstration data.")
                self._init_defaults()
                self._save_unsafe()

    def _init_defaults(self) -> None:
        """Initializes realistic demonstration devices and variables for ThingsBoard and generic MQTT."""
        self.broker_config = BrokerConfig(
            host=os.getenv("MQTT_BROKER_HOST", "mosquitto"),
            port=int(os.getenv("MQTT_BROKER_PORT", "1883")),
            use_tls=os.getenv("MQTT_USE_TLS", "false").lower() == "true",
            username=os.getenv("MQTT_USERNAME", None),
            password=os.getenv("MQTT_PASSWORD", None),
        )

        # 1. ThingsBoard Solar Weather Station
        dev1 = DeviceConfig(
            id="tb_station_01",
            name="Station Météo Solaire",
            platform=PlatformType.THINGSBOARD,
            token="DEMO_TOKEN_WEATHER",
            enabled=True,
        )
        self.devices[dev1.id] = dev1

        var_temp = VariableConfig(
            id="temperature",
            name="Température Ambiante",
            device_id=dev1.id,
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="°C",
            topic="v1/devices/me/telemetry",
            publish_interval=3.0,
            sim_mode=SimMode.SINE,
            math_config=MathConfig(min_val=18.0, max_val=29.0, period=45.0, noise_percent=2.5),
        )
        var_hum = VariableConfig(
            id="humidity",
            name="Humidité Relative",
            device_id=dev1.id,
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="%",
            topic="v1/devices/me/telemetry",
            publish_interval=4.0,
            sim_mode=SimMode.COSINE,
            math_config=MathConfig(min_val=35.0, max_val=75.0, period=60.0, noise_percent=1.0),
        )
        var_status = VariableConfig(
            id="powerMode",
            name="Mode Économie d'énergie",
            device_id=dev1.id,
            var_type=VariableType.ATTRIBUTE,
            data_type=DataType.STRING,
            unit="",
            topic="v1/devices/me/attributes",
            publish_interval=10.0,
            sim_mode=SimMode.CONSTANT,
            math_config=MathConfig(constant_val="SOLAR_OPTIMIZED"),
        )
        self.variables[var_temp.id] = var_temp
        self.variables[var_hum.id] = var_hum
        self.variables[var_status.id] = var_status

        # 2. Workshop Air Compressor
        dev2 = DeviceConfig(
            id="ind_motor_02",
            name="Compresseur Atelier",
            platform=PlatformType.GENERIC,
            enabled=True,
        )
        self.devices[dev2.id] = dev2

        var_rpm = VariableConfig(
            id="vitesse_rpm",
            name="Vitesse de Rotation",
            device_id=dev2.id,
            var_type=VariableType.TELEMETRY,
            data_type=DataType.INTEGER,
            unit="rpm",
            topic="usines/atelier1/compresseur/rpm",
            publish_interval=2.0,
            sim_mode=SimMode.POINTS_TABLE,
            points_config=PointsTableConfig(
                points=[
                    TimestampedPoint(offset_seconds=0.0, value=0),
                    TimestampedPoint(offset_seconds=10.0, value=1200),
                    TimestampedPoint(offset_seconds=25.0, value=2800),
                    TimestampedPoint(offset_seconds=40.0, value=2850),
                    TimestampedPoint(offset_seconds=50.0, value=1000),
                    TimestampedPoint(offset_seconds=60.0, value=0),
                ],
                loop=True,
                playback_speed=1.0,
                interpolate=True,
            ),
        )
        var_pressure = VariableConfig(
            id="pression_bar",
            name="Pression Cuve",
            device_id=dev2.id,
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="bar",
            topic="usines/atelier1/compresseur/pression",
            publish_interval=2.5,
            sim_mode=SimMode.SAWTOOTH,
            math_config=MathConfig(min_val=4.5, max_val=8.2, period=30.0),
        )
        self.variables[var_rpm.id] = var_rpm
        self.variables[var_pressure.id] = var_pressure

    def _save_unsafe(self) -> None:
        """Performs atomic file write to .tmp staging file before renaming."""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            data = {
                "broker": self.broker_config.model_dump(),
                "devices": [d.model_dump() for d in self.devices.values()],
                "variables": [v.model_dump() for v in self.variables.values()],
            }
            temp_path = f"{self.file_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.file_path)

            # Update persistent backup
            try:
                import shutil
                shutil.copy2(self.file_path, f"{self.file_path}.bak")
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error saving state file: {e}")

    def save(self) -> None:
        """Thread-safe state persistence."""
        with self._lock:
            self._save_unsafe()

    # --- CRUD Access Methods ---
    def get_devices(self) -> List[DeviceConfig]:
        """
        Retrieves all registered devices.

        Returns:
            List[DeviceConfig]: List of device configurations.
        """
        with self._lock:
            return list(self.devices.values())

    def get_device(self, device_id: str) -> Optional[DeviceConfig]:
        """
        Retrieves a device by ID.

        Args:
            device_id: Device identifier.

        Returns:
            Optional[DeviceConfig]: DeviceConfig if found, else None.
        """
        with self._lock:
            return self.devices.get(device_id)

    def save_device(self, device: DeviceConfig) -> None:
        """
        Saves or updates a device configuration.

        If `publish_interval` is set on the device, synchronizes it across all its variables.

        Args:
            device: DeviceConfig instance to persist.
        """
        with self._lock:
            self.devices[device.id] = device
            if device.publish_interval is not None and device.publish_interval > 0:
                for v in self.variables.values():
                    if v.device_id == device.id:
                        v.publish_interval = device.publish_interval
            self._save_unsafe()

    def delete_device(self, device_id: str) -> None:
        """
        Deletes a device and cascades deletion to all associated variables.

        Args:
            device_id: Identifier of device to remove.
        """
        with self._lock:
            if device_id in self.devices:
                del self.devices[device_id]
            # Cascade deletion to associated variables
            to_del = [vid for vid, v in self.variables.items() if v.device_id == device_id]
            for vid in to_del:
                del self.variables[vid]
            self._save_unsafe()

    def get_variables(self, device_id: Optional[str] = None) -> List[VariableConfig]:
        """
        Retrieves all variables, optionally filtered by parent device.

        Args:
            device_id: Optional device identifier filter.

        Returns:
            List[VariableConfig]: Filtered or complete list of variables.
        """
        with self._lock:
            if device_id:
                return [v for v in self.variables.values() if v.device_id == device_id]
            return list(self.variables.values())

    def get_variable(self, var_id: str) -> Optional[VariableConfig]:
        """
        Retrieves a single variable configuration by ID.

        Args:
            var_id: Variable identifier.

        Returns:
            Optional[VariableConfig]: Variable configuration or None.
        """
        with self._lock:
            return self.variables.get(var_id)

    def save_variable(self, variable: VariableConfig) -> None:
        """
        Saves or updates a single variable configuration.

        Args:
            variable: VariableConfig instance to persist.
        """
        with self._lock:
            self.variables[variable.id] = variable
            self._save_unsafe()

    def save_variables(self, variables: List[VariableConfig]) -> None:
        """
        Performs a batch save of multiple variables in a single atomic transaction.

        Args:
            variables: List of VariableConfig instances to save.
        """
        with self._lock:
            for v in variables:
                self.variables[v.id] = v
            self._save_unsafe()

    def delete_variable(self, var_id: str) -> None:
        """
        Deletes a variable configuration by ID.

        Args:
            var_id: Variable identifier to remove.
        """
        with self._lock:
            if var_id in self.variables:
                del self.variables[var_id]
                self._save_unsafe()

    def get_broker(self) -> BrokerConfig:
        """
        Retrieves current global MQTT broker configuration.

        Returns:
            BrokerConfig: Active broker configuration.
        """
        with self._lock:
            return self.broker_config

    def save_broker(self, broker: BrokerConfig) -> None:
        """
        Updates and persists global broker configuration.

        Args:
            broker: Updated BrokerConfig instance.
        """
        with self._lock:
            self.broker_config = broker
            self._save_unsafe()

    def export_scenario(self) -> dict:
        """
        Exports the entire simulation scenario (broker, devices, variables) as a serializable dict.

        Returns:
            dict: Complete simulation snapshot.
        """
        with self._lock:
            return {
                "broker": self.broker_config.model_dump(),
                "devices": [d.model_dump() for d in self.devices.values()],
                "variables": [v.model_dump() for v in self.variables.values()],
            }

    def import_scenario(self, data: dict) -> None:
        """
        Restores a complete simulation scenario from an exported dictionary snapshot.

        Args:
            data: Dictionary containing 'broker', 'devices', and 'variables'.
        """
        with self._lock:
            if "broker" in data:
                self.broker_config = BrokerConfig.model_validate(data["broker"])
            if "devices" in data:
                self.devices.clear()
                for d in data["devices"]:
                    dev = DeviceConfig.model_validate(d)
                    self.devices[dev.id] = dev
            if "variables" in data:
                self.variables.clear()
                for v in data["variables"]:
                    var = VariableConfig.model_validate(v)
                    self.variables[var.id] = var
            self._save_unsafe()
