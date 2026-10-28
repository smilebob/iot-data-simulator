"""
Centralized Transport Protocol Dispatcher.

This module provides the unified routing and dispatching layer for outbound telemetry
and attribute publications. Based on each device's configuration and platform type,
traffic is routed across:
- MQTT: Real-time publish/subscribe via `MqttManager` (default port 1883/8883/443).
- HTTP / HTTPS: RESTful JSON payload transmission via `ThingsBoardHttpClient` (port 80/443).
- CoAP: UDP datagram transmission via `ThingsBoardCoapClient` (port 5683).

It also performs automated diagnostic connectivity checks for individual devices.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from app.models.broker import BrokerConfig
from app.models.device import DeviceConfig, PlatformType, TransportProtocol
from app.models.variable import VariableConfig
from app.mqtt.client import MqttManager
from app.platforms import get_adapter
from app.storage.repository import StorageRepository
from app.transports.coap_client import ThingsBoardCoapClient
from app.transports.http_client import ThingsBoardHttpClient

logger = logging.getLogger("iot_sim.transport")

class TransportManager:
    """
    Unified manager routing simulator data to MQTT, HTTP, or CoAP transports.

    Routes messages based on `device.protocol` and `device.platform`.
    Provides targeted connectivity diagnostics per device.

    Attributes:
        storage: Persistent repository containing broker settings and configurations.
        mqtt: Multi-client MQTT connection manager.
        http: HTTP REST client for ThingsBoard communication.
        coap: UDP CoAP client for lightweight transmission.
    """

    def __init__(
        self,
        storage_repo: StorageRepository,
        mqtt_manager: MqttManager,
        http_client: Optional[ThingsBoardHttpClient] = None,
        coap_client: Optional[ThingsBoardCoapClient] = None,
    ) -> None:
        """
        Initializes the transport manager.

        Args:
            storage_repo: Storage repository instance.
            mqtt_manager: MqttManager instance.
            http_client: Optional custom ThingsBoardHttpClient instance.
            coap_client: Optional custom ThingsBoardCoapClient instance.
        """
        self.storage = storage_repo
        self.mqtt = mqtt_manager
        self.http = http_client or ThingsBoardHttpClient()
        self.coap = coap_client or ThingsBoardCoapClient()

    async def publish(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        payload: str,
        topic: str,
        timestamp_ms: int,
    ) -> Tuple[bool, str, str]:
        """
        Dispatches a payload through the device's designated communication protocol.

        Resolves host overrides, TLS settings, and default ports.

        Args:
            device: Source device configuration.
            variable: Specific variable being published.
            payload: Serialized message content (JSON or raw string).
            topic: Pre-formatted MQTT topic or destination path.
            timestamp_ms: Epoch timestamp in milliseconds.

        Returns:
            Tuple[bool, str, str]: (Success flag, protocol name, channel/endpoint details).
        """
        global_broker: BrokerConfig = self.storage.get_broker()
        target_protocol = device.protocol if device.platform == PlatformType.THINGSBOARD else TransportProtocol.MQTT

        # Target host: device custom host or global broker host
        target_host = device.custom_host.strip() if device.custom_host and device.custom_host.strip() else global_broker.host

        if target_protocol == TransportProtocol.HTTP:
            # ThingsBoard HTTP REST mode
            if device.use_tls is not None:
                use_tls = device.use_tls
            elif device.custom_port == 443:
                use_tls = True
            elif device.custom_port == 80:
                use_tls = False
            else:
                # Default to HTTPS (port 443) unless local development host
                is_local = target_host.lower() in ("localhost", "127.0.0.1", "mosquitto", "thingsboard")
                use_tls = False if is_local else True
            default_port = 443 if use_tls else 80
            target_port = device.custom_port or default_port

            adapter = get_adapter(device.platform)
            endpoint = getattr(adapter, "get_http_endpoint", lambda d, v: f"/api/v1/{d.token or 'default'}/telemetry")(device, variable)

            success, detail = await self.http.post_payload(
                host=target_host,
                port=target_port,
                endpoint=endpoint,
                payload=payload,
                use_tls=use_tls,
            )
            return success, "HTTP", f"POST {endpoint}"

        elif target_protocol == TransportProtocol.COAP:
            # ThingsBoard CoAP UDP mode
            target_port = device.custom_port or 5683
            adapter = get_adapter(device.platform)
            segments = getattr(adapter, "get_coap_path_segments", lambda d, v: ["api", "v1", d.token or "default", "telemetry"])(device, variable)

            success, detail = await self.coap.send_payload(
                host=target_host,
                port=target_port,
                path_segments=segments,
                payload=payload,
                wait_response=False,
            )
            return success, "CoAP", f"COAP coap://{target_host}:{target_port}/{'/'.join(segments)}"

        else:
            # Standard MQTT mode
            client = self.mqtt.get_or_create_device_client(device.id, device.token, device)
            success = False
            if client:
                success = client.publish(topic, payload)
            return success, "MQTT", topic

    async def test_device_communication(self, device: DeviceConfig) -> Dict[str, Any]:
        """
        Executes an end-to-end communication diagnostic for a specific device.

        Probes the target endpoint according to the device's selected protocol (HTTP, CoAP, or MQTT)
        and returns detailed diagnostic telemetry including latency and recommendations.

        Args:
            device: DeviceConfig instance to diagnose.

        Returns:
            Dict[str, Any]: Diagnostic report containing connectivity status, latency, and suggestions.
        """
        global_broker: BrokerConfig = self.storage.get_broker()
        target_protocol = device.protocol if device.platform == PlatformType.THINGSBOARD else TransportProtocol.MQTT
        target_host = device.custom_host.strip() if device.custom_host and device.custom_host.strip() else global_broker.host

        if target_protocol == TransportProtocol.HTTP:
            if device.use_tls is not None:
                use_tls = device.use_tls
            elif device.custom_port == 443:
                use_tls = True
            elif device.custom_port == 80:
                use_tls = False
            else:
                is_local = target_host.lower() in ("localhost", "127.0.0.1", "mosquitto", "thingsboard")
                use_tls = False if is_local else True
            default_port = 443 if use_tls else 80
            target_port = device.custom_port or default_port

            return await self.http.test_connectivity(
                host=target_host,
                port=target_port,
                token=device.token,
                use_tls=use_tls,
            )

        elif target_protocol == TransportProtocol.COAP:
            target_port = device.custom_port or 5683
            return await self.coap.test_connectivity(
                host=target_host,
                port=target_port,
                token=device.token,
            )

        else:
            # Test MQTT connectivity
            from app.mqtt.diagnostics import test_broker_connectivity
            test_conf = BrokerConfig(
                host=target_host,
                port=device.custom_port or global_broker.port,
                use_tls=device.use_tls if device.use_tls is not None else global_broker.use_tls,
                username=device.token or global_broker.username,
                password=global_broker.password,
                transport=global_broker.transport,
                ws_path=global_broker.ws_path,
            )
            return test_broker_connectivity(test_conf)
