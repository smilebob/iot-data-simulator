"""
Device Domain Models and Protocol Enumerations.

Defines configuration schemas and target protocol types for virtual IoT devices
managed by the simulation engine, supporting ThingsBoard, Home Assistant, Datacake,
and generic MQTT platforms.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PlatformType(str, Enum):
    """Supported IoT target platforms for telemetry and RPC formatting.

    Attributes:
        THINGSBOARD: ThingsBoard IoT platform (telemetry, shared attributes, and RPC).
        HOMEASSISTANT: Home Assistant MQTT discovery and sensor payloads.
        DATACAKE: Datacake IoT cloud platform.
        GENERIC: Universal raw JSON telemetry payloads.
    """
    THINGSBOARD = "thingsboard"
    HOMEASSISTANT = "homeassistant"
    DATACAKE = "datacake"
    GENERIC = "generic"


class TransportProtocol(str, Enum):
    """Network transport protocols supported for device communication.

    Attributes:
        MQTT: Message Queuing Telemetry Transport (TCP or WebSockets).
        HTTP: Hypertext Transfer Protocol (REST API v1 / HTTPS).
        COAP: Constrained Application Protocol (RFC 7252 over UDP).
    """
    MQTT = "mqtt"
    HTTP = "http"
    COAP = "coap"


class DeviceConfig(BaseModel):
    """Pydantic model representing a simulated virtual IoT device.

    Encapsulates network settings, credentials, target platform adapters,
    and cadence overrides for a logical grouping of simulated metrics.

    Attributes:
        id: Unique alphanumeric identifier of the device (e.g., 'ind_compressor_01').
        name: Human-readable display label for the device.
        platform: Target IoT platform adapter for message framing.
        token: Device authentication token or API key (e.g., ThingsBoard device token).
        protocol: Network transport protocol to use for dispatching messages.
        custom_host: Optional remote hostname override (defaults to global broker if None).
        custom_port: Optional network port override (deduced from protocol if None).
        use_tls: Flag indicating whether TLS/HTTPS encryption is enforced.
        publish_interval: Optional global broadcast period in seconds; if specified,
            it cascades to and overrides individual variable cadences for this device.
        enabled: Operational flag indicating whether simulation is running for this device.
    """
    id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Display label for the device")
    platform: PlatformType = Field(default=PlatformType.THINGSBOARD, description="Target IoT platform")
    token: Optional[str] = Field(default=None, description="Authentication token or API key")
    protocol: TransportProtocol = Field(default=TransportProtocol.MQTT, description="Network transport protocol")
    custom_host: Optional[str] = Field(default=None, description="Custom hostname override (inherits global host if None)")
    custom_port: Optional[int] = Field(default=None, description="Custom port override (deduced from protocol if None)")
    use_tls: Optional[bool] = Field(default=None, description="Enforce TLS / HTTPS encryption")
    publish_interval: Optional[float] = Field(default=None, description="Global broadcast cadence in seconds (overrides variable intervals)")
    enabled: bool = Field(default=True, description="Whether the device is active in the simulation")
