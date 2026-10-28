"""
Network transport adapters and protocol managers.

This package encapsulates connectivity implementations across multiple industrial protocols:
- `manager`: Centralized transport dispatcher routing device payloads to MQTT, HTTP, or CoAP.
- `http_client`: Asynchronous REST API client for ThingsBoard telemetry, RPC, and attributes.
- `coap_client`: Native RFC 7252 binary UDP datagram client.
"""

from app.transports.coap_client import ThingsBoardCoapClient
from app.transports.http_client import ThingsBoardHttpClient
from app.transports.manager import TransportManager

__all__ = ["ThingsBoardHttpClient", "ThingsBoardCoapClient", "TransportManager"]

