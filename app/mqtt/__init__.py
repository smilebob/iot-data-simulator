"""
MQTT client connections, thread pool lifecycle, and broker diagnostics.

This package provides:
- `MqttConnection`: Encapsulated single Paho MQTT client with automatic reconnect.
- `MqttManager`: Multi-tenant manager for global and per-device connections.
- `diagnostics`: Network reachability and TLS verification testing utilities.
"""

from app.mqtt.client import MqttConnection, MqttManager

__all__ = ["MqttConnection", "MqttManager"]

