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
    Gestionnaire centralisé des protocoles de transmission.
    Achemine chaque mesure vers le protocole approprié :
    - MQTT (v1/devices/me/telemetry via MqttManager)
    - HTTP (POST /api/v1/{token}/telemetry via ThingsBoardHttpClient)
    - CoAP (POST UDP coap://.../api/v1/{token}/telemetry via ThingsBoardCoapClient)
    """

    def __init__(
        self,
        storage_repo: StorageRepository,
        mqtt_manager: MqttManager,
        http_client: Optional[ThingsBoardHttpClient] = None,
        coap_client: Optional[ThingsBoardCoapClient] = None,
    ):
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
        Publie une donnée selon le protocole assigné à l'équipement.
        Retourne (succès: bool, protocole_nom: str, info_canal: str)
        """
        global_broker: BrokerConfig = self.storage.get_broker()
        target_protocol = device.protocol if device.platform == PlatformType.THINGSBOARD else TransportProtocol.MQTT

        # Hôte cible : spécifique à l'équipement ou global
        target_host = device.custom_host.strip() if device.custom_host and device.custom_host.strip() else global_broker.host

        if target_protocol == TransportProtocol.HTTP:
            # Mode ThingsBoard HTTP REST
            use_tls = device.use_tls if device.use_tls is not None else global_broker.use_tls
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
            # Mode ThingsBoard CoAP UDP
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
            # Mode standard MQTT
            client = self.mqtt.get_or_create_device_client(device.id, device.token)
            success = False
            if client:
                success = client.publish(topic, payload)
            return success, "MQTT", topic

    async def test_device_communication(self, device: DeviceConfig) -> Dict[str, Any]:
        """
        Exécute un test de communication ciblé pour un équipement spécifique.
        """
        global_broker: BrokerConfig = self.storage.get_broker()
        target_protocol = device.protocol if device.platform == PlatformType.THINGSBOARD else TransportProtocol.MQTT
        target_host = device.custom_host.strip() if device.custom_host and device.custom_host.strip() else global_broker.host

        if target_protocol == TransportProtocol.HTTP:
            use_tls = device.use_tls if device.use_tls is not None else global_broker.use_tls
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
            # Test MQTT
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
