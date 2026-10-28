"""
Home Assistant Platform Adapter with MQTT Discovery.

This adapter formats data for Home Assistant using the standard MQTT Discovery protocol.
It generates discovery configurations (`homeassistant/sensor/.../config` or `switch/.../config`)
enabling automatic zero-YAML entity detection and state tracking.
"""

import json
from typing import Any, List, Optional, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType
from app.platforms.base import BasePlatformAdapter

class HomeAssistantAdapter(BasePlatformAdapter):
    """
    Home Assistant integration adapter using MQTT Discovery.

    Creates state topics and discovery payloads for sensors and switches.
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        """
        Determines the state topic for a Home Assistant entity.

        Args:
            device: Source device.
            variable: Entity variable.

        Returns:
            str: State topic (e.g., 'homeassistant/sensor/{dev_id}/{var_id}/state').
        """
        prefix = "sensor" if variable.var_type == VariableType.TELEMETRY else "switch"
        return f"homeassistant/{prefix}/{device.id}/{variable.id}/state"

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        """
        Formats state message for Home Assistant entity.

        Args:
            device: Source device.
            variable: Entity variable.
            value: Current value.
            timestamp_ms: Epoch timestamp (unused by simple Home Assistant state topics).

        Returns:
            Tuple[str, str]: (State topic, plain-text string representation of value).
        """
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)
        return topic, str(value)

    def get_discovery_messages(
        self,
        device: DeviceConfig,
        variables: List[VariableConfig],
    ) -> List[Tuple[str, str]]:
        """
        Builds MQTT Discovery configuration payloads for all variables.

        Args:
            device: Source device.
            variables: List of active variables to register.

        Returns:
            List[Tuple[str, str]]: List of (config_topic, config_payload_json).
        """
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
