import json
from typing import Any, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig
from app.platforms.base import BasePlatformAdapter

class DatacakeAdapter(BasePlatformAdapter):
    """
    Connecteur pour la plateforme Datacake (format JSON horodaté standard).
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        return f"datacake/{device.id}/telemetry"

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)
        payload = json.dumps({
            variable.id: value,
            "timestamp": int(timestamp_ms / 1000)
        })
        return topic, payload
