"""
Generic Universal MQTT Adapter.

This adapter serves as the fallback standard MQTT connector.
Publishes structured JSON dictionaries containing device ID, variable ID, value,
unit of measurement, and millisecond timestamps to user-defined topics or `{device_id}/{variable_id}`.
"""

import json
from typing import Any, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig
from app.platforms.base import BasePlatformAdapter

class GenericMqttAdapter(BasePlatformAdapter):
    """
    Universal generic MQTT adapter formatting messages into standard JSON objects.
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        """
        Returns hierarchical default topic `{device_id}/{variable_id}`.

        Args:
            device: Source device.
            variable: Telemetry/attribute variable.

        Returns:
            str: Default topic string.
        """
        return f"{device.id}/{variable.id}"

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        """
        Formats universal JSON telemetry message.

        Args:
            device: Source device.
            variable: Telemetry variable.
            value: Telemetry value.
            timestamp_ms: Millisecond epoch timestamp.

        Returns:
            Tuple[str, str]: (Target topic, structured JSON payload).
        """
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)
        
        payload = json.dumps({
            "device": device.id,
            "variable": variable.id,
            "value": value,
            "unit": variable.unit,
            "timestamp": timestamp_ms
        })
        return topic, payload

