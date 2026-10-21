import json
from typing import Any, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig
from app.platforms.base import BasePlatformAdapter

class GenericMqttAdapter(BasePlatformAdapter):
    """
    Connecteur MQTT générique et universel.
    Publie sur le topic personnalisé configuré ou un topic hiérarchique {device_id}/{variable_id}.
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        return f"{device.id}/{variable.id}"

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)
        
        # Envoi en format JSON structuré par défaut
        payload = json.dumps({
            "device": device.id,
            "variable": variable.id,
            "value": value,
            "unit": variable.unit,
            "timestamp": timestamp_ms
        })
        return topic, payload
