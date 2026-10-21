import json
from typing import Any, List, Optional, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType
from app.platforms.base import BasePlatformAdapter

class HomeAssistantAdapter(BasePlatformAdapter):
    """
    Connecteur pour Home Assistant via MQTT Discovery standard.
    Permet l'auto-détection automatique des entités dans Home Assistant sans configuration YAML.
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        prefix = "sensor" if variable.var_type == VariableType.TELEMETRY else "switch"
        return f"homeassistant/{prefix}/{device.id}/{variable.id}/state"

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)
        return topic, str(value)

    def get_discovery_messages(
        self,
        device: DeviceConfig,
        variables: List[VariableConfig],
    ) -> List[Tuple[str, str]]:
        messages: List[Tuple[str, str]] = []
        for var in variables:
            prefix = "sensor" if var.var_type == VariableType.TELEMETRY else "switch"
            config_topic = f"homeassistant/{prefix}/{device.id}/{var.id}/config"
            state_topic = self.get_default_topic(device, var)
            
            payload = {
                "name": f"{device.name} {var.name}",
                "state_topic": state_topic,
                "unique_id": f"{device.id}_{var.id}",
                "device": {
                    "identifiers": [device.id],
                    "name": device.name,
                    "manufacturer": "IoT Data Simulator",
                    "model": "Virtual IoT Device"
                }
            }
            if var.unit:
                payload["unit_of_measurement"] = var.unit

            messages.append((config_topic, json.dumps(payload)))
        return messages
