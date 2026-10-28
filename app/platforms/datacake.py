"""
Datacake Platform Adapter.

This adapter formats telemetry for the Datacake cloud platform.
Messages are published to `datacake/{device_id}/telemetry` using JSON dictionaries
keyed by variable ID with seconds-precision Unix timestamps.
"""

import json
from typing import Any, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig
from app.platforms.base import BasePlatformAdapter

class DatacakeAdapter(BasePlatformAdapter):
    """
    Adapter formatting telemetry for Datacake IoT cloud platform.
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        """
        Returns Datacake standard telemetry ingestion topic.

        Args:
            device: Source device.
            variable: Target variable.

        Returns:
            str: 'datacake/{device_id}/telemetry'.
        """
        return f"datacake/{device.id}/telemetry"

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        """
        Formats JSON payload with second-level timestamp for Datacake.

        Args:
            device: Source device.
            variable: Telemetry variable.
            value: Telemetry value.
            timestamp_ms: Millisecond epoch timestamp.

        Returns:
            Tuple[str, str]: (Datacake topic, JSON string).
        """
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)
        payload = json.dumps({
            variable.id: value,
            "timestamp": int(timestamp_ms / 1000)
        })
        return topic, payload

