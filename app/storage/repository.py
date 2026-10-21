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
    Gestionnaire de persistance thread-safe pour les équipements, variables et configuration broker.
    Enregistre les données sous forme de fichier JSON dans le volume persistant.
    """

    def __init__(self, file_path: str = "data/simulator_state.json"):
        self.file_path = file_path
        self._lock = threading.Lock()
        self.broker_config = BrokerConfig()
        self.devices: Dict[str, DeviceConfig] = {}
        self.variables: Dict[str, VariableConfig] = {}
        self.load()

    def load(self):
        with self._lock:
            if not os.path.exists(self.file_path):
                # Vérifier si un backup automatique existe
                bak_path = f"{self.file_path}.bak"
                if os.path.exists(bak_path):
                    logger.warning(f"Fichier principal {self.file_path} absent, tentative de restauration depuis {bak_path}")
                    try:
                        import shutil
                        shutil.copy2(bak_path, self.file_path)
                    except Exception as e:
                        logger.error(f"Erreur copie backup: {e}")
                else:
                    logger.info(f"Fichier de configuration inexistant ({self.file_path}), initialisation des démos par défaut.")
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
                        logger.warning(f"Configuration broker invalide, conservation défaut: {e}")

                self.devices.clear()
                for d in data.get("devices", []):
                    try:
                        dev = DeviceConfig.model_validate(d)
                        self.devices[dev.id] = dev
                    except Exception as e:
                        logger.warning(f"Validation stricte échouée pour équipement {d.get('id', 'inconnu')}: {e}. Chargement résilient sans validation pour préserver vos données.")
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
                        logger.warning(f"Validation stricte échouée pour variable {v.get('id', 'inconnue')}: {e}. Chargement résilient sans validation.")
                        try:
                            self.variables[v["id"]] = VariableConfig.model_construct(**v)
                        except Exception:
                            pass

                logger.info(f"✓ Chargé {len(self.devices)} équipement(s) et {len(self.variables)} variable(s) depuis {self.file_path}")

                # Actualisation du backup sécurisé
                try:
                    import shutil
                    shutil.copy2(self.file_path, f"{self.file_path}.bak")
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"Erreur critique lors de la lecture de {self.file_path}: {e}")
                import time
                try:
                    import shutil
                    corrupt_path = f"{self.file_path}.corrupted.{int(time.time())}"
                    shutil.copy2(self.file_path, corrupt_path)
                    logger.warning(f"Copie du fichier d'origine préservée dans {corrupt_path}")
                except Exception:
                    pass

                # Tenter de restaurer depuis le backup .bak
                bak_path = f"{self.file_path}.bak"
                if os.path.exists(bak_path):
                    logger.warning(f"Restauration automatique d'urgence depuis le backup {bak_path}")
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
                        logger.error(f"Échec restauration backup: {be}")

                logger.error("Restauration impossible, initialisation des valeurs par défaut.")
                self._init_defaults()
                self._save_unsafe()

    def _init_defaults(self):
        """Initialise des équipements et variables de démonstration réalistes pour ThingsBoard et d'autres plateformes."""
        self.broker_config = BrokerConfig(
            host=os.getenv("MQTT_BROKER_HOST", "mosquitto"),
            port=int(os.getenv("MQTT_BROKER_PORT", "1883")),
            use_tls=os.getenv("MQTT_USE_TLS", "false").lower() == "true",
            username=os.getenv("MQTT_USERNAME", None),
            password=os.getenv("MQTT_PASSWORD", None),
        )

        # 1. Équipement ThingsBoard de démo
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

        # 2. Équipement Industriel (Table de points / Rejeu)
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

    def _save_unsafe(self):
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

            # Mise à jour du backup persistant
            try:
                import shutil
                shutil.copy2(self.file_path, f"{self.file_path}.bak")
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Erreur sauvegarde fichier: {e}")

    def save(self):
        with self._lock:
            self._save_unsafe()

    # --- Accès Méthodes CRUD ---
    def get_devices(self) -> List[DeviceConfig]:
        with self._lock:
            return list(self.devices.values())

    def get_device(self, device_id: str) -> Optional[DeviceConfig]:
        with self._lock:
            return self.devices.get(device_id)

    def save_device(self, device: DeviceConfig):
        with self._lock:
            self.devices[device.id] = device
            # Si un intervalle d'envoi global est configuré, écraser l'intervalle de toutes ses variables
            if device.publish_interval is not None and device.publish_interval > 0:
                for v in self.variables.values():
                    if v.device_id == device.id:
                        v.publish_interval = device.publish_interval
            self._save_unsafe()

    def delete_device(self, device_id: str):
        with self._lock:
            if device_id in self.devices:
                del self.devices[device_id]
            # Supprimer aussi les variables associées
            to_del = [vid for vid, v in self.variables.items() if v.device_id == device_id]
            for vid in to_del:
                del self.variables[vid]
            self._save_unsafe()

    def get_variables(self, device_id: Optional[str] = None) -> List[VariableConfig]:
        with self._lock:
            if device_id:
                return [v for v in self.variables.values() if v.device_id == device_id]
            return list(self.variables.values())

    def get_variable(self, var_id: str) -> Optional[VariableConfig]:
        with self._lock:
            return self.variables.get(var_id)

    def save_variable(self, variable: VariableConfig):
        with self._lock:
            self.variables[variable.id] = variable
            self._save_unsafe()

    def delete_variable(self, var_id: str):
        with self._lock:
            if var_id in self.variables:
                del self.variables[var_id]
                self._save_unsafe()

    def get_broker(self) -> BrokerConfig:
        with self._lock:
            return self.broker_config

    def save_broker(self, broker: BrokerConfig):
        with self._lock:
            self.broker_config = broker
            self._save_unsafe()

    def export_scenario(self) -> dict:
        with self._lock:
            return {
                "broker": self.broker_config.model_dump(),
                "devices": [d.model_dump() for d in self.devices.values()],
                "variables": [v.model_dump() for v in self.variables.values()],
            }

    def import_scenario(self, data: dict):
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
