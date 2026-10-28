"""
MQTT Broker Configuration Models.

Defines schemas for connecting to embedded Mosquitto brokers or remote IoT platform brokers
with support for TCP, WebSockets (WSS), TLS encryption, and custom credentials.
"""

from typing import Optional
from pydantic import BaseModel, Field


class BrokerConfig(BaseModel):
    """Configuration parameters for global MQTT broker connectivity.

    Attributes:
        host: Hostname or IP address of the broker (default: 'mosquitto' for embedded service).
        port: TCP port of the broker (1883 for plaintext, 8883 for TLS, 9001 for WebSockets).
        use_tls: Flag indicating whether TLS/SSL encryption is enforced.
        ca_cert_path: Optional path to a custom CA root certificate file for verification.
        username: Optional MQTT client username or platform access token.
        password: Optional MQTT client password.
        transport: Underlying transport protocol ('tcp' standard or 'websockets').
        ws_path: WebSocket endpoint path when transport is 'websockets' (default: '/mqtt').
        client_id_prefix: Prefix used when generating unique client identifiers.
        keepalive: Connection keep-alive heartbeat interval in seconds.
    """
    host: str = Field(default="mosquitto", description="IP address or hostname of the MQTT broker")
    port: int = Field(default=1883, description="MQTT port (1883 standard, 8883 TLS, 9001 WS)")
    use_tls: bool = Field(default=False, description="Enable TLS/MQTTS encryption")
    ca_cert_path: Optional[str] = Field(default=None, description="Path to custom root CA certificate")
    username: Optional[str] = Field(default=None, description="MQTT username or ThingsBoard Access Token")
    password: Optional[str] = Field(default=None, description="MQTT password")
    transport: str = Field(default="tcp", description="Transport layer: 'tcp' or 'websockets'")
    ws_path: str = Field(default="/mqtt", description="WebSocket resource path when transport='websockets'")
    client_id_prefix: str = Field(default="iot_sim_", description="Client identifier prefix")
    keepalive: int = Field(default=60, description="Keep-alive ping interval in seconds")
