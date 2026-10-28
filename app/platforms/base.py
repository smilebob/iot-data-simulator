"""
Abstract Base Platform Adapter Interface for IoT Gateways.

This module defines the extensible contract for formatting outbound telemetry/attributes,
generating automatic discovery declarations, and parsing incoming platform RPC commands.
Concrete adapters include ThingsBoard, Home Assistant, Datacake, and Generic MQTT.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType

class BasePlatformAdapter(ABC):
    """
    Abstract interface for platform-specific IoT protocol adapters.

    Standardizes message formatting, topic resolution, discovery announcements,
    and downstream payload parsing across heterogeneous cloud/edge IoT systems.
    """

    @abstractmethod
    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        """
        Determines the default destination topic for a variable.

        Args:
            device: Target device configuration.
            variable: Telemetry or attribute variable.

        Returns:
            str: Destination topic string.
        """
        pass

    @abstractmethod
    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        """
        Encodes variable telemetry into a platform-compliant payload.

        Args:
            device: Source device.
            variable: Variable configuration.
            value: Current evaluated value.
            timestamp_ms: Epoch timestamp in milliseconds.

        Returns:
            Tuple[str, str]: (Target topic, formatted payload string).
        """
        pass

    def get_discovery_messages(
        self,
        device: DeviceConfig,
        variables: List[VariableConfig],
    ) -> List[Tuple[str, str]]:
        """
        Constructs automatic discovery announcements (e.g., Home Assistant MQTT Discovery).

        Args:
            device: Target device configuration.
            variables: List of active variables to register.

        Returns:
            List[Tuple[str, str]]: List of (discovery_topic, config_json) tuples.
        """
        return []

    def handle_incoming_message(
        self,
        topic: str,
        payload: str,
    ) -> Optional[Tuple[str, Any]]:
        """
        Parses an incoming platform command or downlink message.

        Args:
            topic: Arrival topic.
            payload: Raw string message body.

        Returns:
            Optional[Tuple[str, Any]]: (method_or_variable_id, parsed_value_or_params) if valid, else None.
        """
        return None
