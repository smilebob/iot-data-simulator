"""
MQTT Client Connection and Multi-Tenant Lifecycle Manager.

This module manages industrial MQTT connections via the Eclipse Paho library.
Features:
- Dual protocol transport support: Raw TCP (ports 1883/8883) and WebSockets (ports 9001/443).
- Automated TLS 1.2+ encryption configuration (CIS Benchmark compliance).
- Multi-client tenant architecture: A primary root client plus dedicated per-device clients
  authenticated with individual ThingsBoard device access tokens.
- Hot re-configuration (`update_global_config`) that tears down and reconnects all active
  broker connections without restarting the Python process.
- Bidirectional subscriptions for RPC commands (`v1/devices/me/rpc/request/+`) and
  shared attribute synchronization (`v1/devices/me/attributes`).
"""

import logging
import ssl
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple
import paho.mqtt.client as mqtt
from app.models.broker import BrokerConfig

logger = logging.getLogger("iot_sim.mqtt")

class MqttConnection:
    """
    Manages a single robust MQTT connection with automatic reconnection.

    Handles connection lifecycle, TLS negotiation, and asynchronous event callbacks
    using Paho MQTT Client (v1.x and v2.x compatible).

    Attributes:
        config: Broker configuration specification.
        on_message_callback: Callback triggered when a message arrives on subscribed topics.
        is_connected: Boolean flag indicating current network connection state.
        last_error: Descriptive error message from the most recent failure, if any.
        messages_published: Total count of successfully published messages.
    """

    def __init__(
        self,
        config: BrokerConfig,
        on_message_callback: Optional[Callable[[str, str], None]] = None,
        client_id_suffix: str = "",
    ) -> None:
        """
        Initializes an MQTT connection instance.

        Args:
            config: BrokerConfig instance specifying host, port, credentials, and TLS flags.
            on_message_callback: Function accepting `(topic: str, payload: str)`.
            client_id_suffix: Suffix appended to the MQTT client identifier for uniqueness.
        """
        self.config: BrokerConfig = config
        self.on_message_callback: Optional[Callable[[str, str], None]] = on_message_callback
        self.is_connected: bool = False
        self.last_error: Optional[str] = None
        self.messages_published: int = 0
        self._lock: threading.Lock = threading.Lock()

        # Build unique Paho client ID
        client_id = f"{config.client_id_prefix}{client_id_suffix}_{int(time.time())}"
        transport_mode = getattr(config, "transport", "tcp").lower()

        try:
            # Paho MQTT v2.x API
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id,
                transport=transport_mode,
                protocol=mqtt.MQTTv311,
            )
        except AttributeError:
            # Paho MQTT v1.x fallback
            self.client = mqtt.Client(
                client_id=client_id,
                transport=transport_mode,
                protocol=mqtt.MQTTv311,
            )

        if transport_mode == "websockets":
            ws_path = getattr(config, "ws_path", "/mqtt") or "/mqtt"
            self.client.ws_set_options(path=ws_path)
            logger.info(f"WebSockets transport active on path: {ws_path}")

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Configure Authentication
        if config.username:
            self.client.username_pw_set(config.username, config.password or "")

        # Configure Secure TLS (CIS benchmark compliant, minimum TLS 1.2)
        if config.use_tls or config.port in (8883, 443):
            self._configure_tls()

    def _configure_tls(self) -> None:
        """Configures SSL context with TLS 1.2+ minimum version requirements."""
        try:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.minimum_version = ssl.TLSVersion.TLSv1_2

            if self.config.ca_cert_path:
                context.load_verify_locations(cafile=self.config.ca_cert_path)
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = True
            else:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            self.client.tls_set_context(context)
            logger.info(f"TLS 1.2+ configured for {self.config.host}:{self.config.port}")
        except Exception as e:
            err_msg = f"TLS configuration error on {self.config.host}: {e}"
            logger.error(err_msg)
            self.last_error = err_msg

    def _on_connect(self, client: Any, userdata: Any, flags: Any, rc: Any, properties: Any = None) -> None:
        """Paho on_connect callback handler."""
        rc_code = rc.value if hasattr(rc, "value") else rc
        if rc_code == 0:
            self.is_connected = True
            self.last_error = None
            logger.info(f"✓ Successfully connected to MQTT broker {self.config.host}:{self.config.port} ({self.config.transport})")
            # Subscribe to ThingsBoard bidirectional topics: RPC and Shared Attributes
            self.client.subscribe([
                ("v1/devices/me/rpc/request/+", 1),
                ("v1/devices/me/attributes", 1),
                ("v1/devices/me/attributes/response/+", 1),
            ])
        else:
            self.is_connected = False
            reasons = {
                1: "Unsupported MQTT protocol version",
                2: "Client identifier rejected",
                3: "MQTT broker unavailable",
                4: "Invalid username, password, or ThingsBoard access token",
                5: "Not authorized",
            }
            reason = reasons.get(rc_code, f"Return code {rc_code}")
            self.last_error = f"Connection refused by {self.config.host}:{self.config.port} ({reason})"
            logger.error(self.last_error)

    def _on_disconnect(self, client: Any, userdata: Any, flags: Any, rc: Any = None, properties: Any = None) -> None:
        """Paho on_disconnect callback handler."""
        self.is_connected = False
        rc_code = rc.value if hasattr(rc, "value") else (rc if rc is not None else 0)
        if rc_code != 0:
            msg = f"Unexpected disconnection from MQTT broker {self.config.host}:{self.config.port} (code {rc_code})"
            self.last_error = msg
            logger.warning(msg)
        else:
            logger.info(f"Disconnected from MQTT broker {self.config.host}:{self.config.port}")

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        """Paho on_message callback handler."""
        try:
            topic = message.topic
            payload = message.payload.decode("utf-8", errors="replace")
            logger.debug(f"Message received on {topic}: {payload}")
            if self.on_message_callback:
                self.on_message_callback(topic, payload)
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")

    def start(self) -> None:
        """Initiates asynchronous non-blocking connection loop in background thread."""
        try:
            logger.info(f"Attempting MQTT connection to {self.config.host}:{self.config.port} (TLS={self.config.use_tls}, transport={self.config.transport})...")
            self.client.connect_async(self.config.host, self.config.port, self.config.keepalive)
            self.client.loop_start()
        except Exception as e:
            self.last_error = f"Failed starting MQTT connection to {self.config.host}:{self.config.port}: {e}"
            logger.error(self.last_error)

    def stop(self) -> None:
        """Stops background network loop and disconnects from the broker."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
        except Exception as e:
            logger.debug(f"Error stopping MQTT client: {e}")

    def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False) -> bool:
        """
        Publishes a payload to an MQTT topic with thread-safe locking.

        Args:
            topic: Destination MQTT topic.
            payload: Message body.
            qos: Quality of Service level (0, 1, or 2). Defaults to 1.
            retain: Retain flag. Defaults to False.

        Returns:
            bool: True if message was successfully published to network buffer, False otherwise.
        """
        if not self.is_connected:
            return False
        with self._lock:
            try:
                res = self.client.publish(topic, payload, qos=qos, retain=retain)
                if res.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.messages_published += 1
                    return True
                else:
                    self.last_error = f"Publish error on {topic}: code {res.rc}"
                    logger.warning(self.last_error)
                    return False
            except Exception as e:
                self.last_error = f"MQTT publish exception: {e}"
                logger.error(self.last_error)
                return False


class MqttManager:
    """
    Multi-client manager for global and device-specific MQTT connections.

    Manages a default root client (for generic MQTT or global simulations)
    along with isolated dedicated clients per ThingsBoard device token.

    Attributes:
        global_config: Primary BrokerConfig specification.
        default_client: Fallback MqttConnection instance.
        device_clients: Dictionary mapping device IDs to dedicated MqttConnection instances.
        on_rpc_callback: Handler for received downstream RPC messages.
    """

    def __init__(self, global_config: BrokerConfig) -> None:
        """
        Initializes the multi-client manager.

        Args:
            global_config: Primary broker configuration.
        """
        self.global_config: BrokerConfig = global_config
        self.default_client: Optional[MqttConnection] = None
        self.device_clients: Dict[str, MqttConnection] = {}
        self.on_rpc_callback: Optional[Callable[[str, str, str], None]] = None

    def start(self) -> None:
        """Starts the default root MQTT client."""
        self.default_client = MqttConnection(
            self.global_config,
            on_message_callback=self._handle_global_message,
            client_id_suffix="main",
        )
        self.default_client.start()

    def update_global_config(self, new_config: BrokerConfig) -> None:
        """
        Applies a new broker configuration dynamically without application restart.

        Gracefully terminates all active connections and reconnects with new settings.

        Args:
            new_config: Updated BrokerConfig instance.
        """
        logger.info(f"🔄 Applying new MQTT Broker configuration -> Host: {new_config.host}:{new_config.port} (TLS={new_config.use_tls}, Transport={new_config.transport})")
        self.global_config = new_config
        self.stop_all()
        self.start()

    def remove_device_client(self, device_id: str) -> None:
        """
        Disconnects and cleans up a device's dedicated MQTT connection.

        Args:
            device_id: Identifier of the device whose connection should be removed.
        """
        if device_id in self.device_clients:
            logger.info(f"Stopping and removing dedicated MQTT client for {device_id}")
            try:
                self.device_clients[device_id].stop()
            except Exception:
                pass
            del self.device_clients[device_id]

    def get_or_create_device_client(
        self,
        device_id: str,
        token: Optional[str],
        device: Optional[Any] = None,
    ) -> MqttConnection:
        """
        Retrieves an existing connection or instantiates a new dedicated client for a device.

        Uses the device's unique ThingsBoard access token as the MQTT username.

        Args:
            device_id: Unique device identifier.
            token: Optional device access token.
            device: Optional DeviceConfig object providing host/port/TLS overrides.

        Returns:
            MqttConnection: Active MQTT connection assigned to this device.
        """
        if not token:
            return self.default_client

        if device_id not in self.device_clients:
            dev_conf = self.global_config.model_copy()
            dev_conf.username = token
            dev_conf.password = ""
            if device:
                if getattr(device, "custom_host", None) and str(device.custom_host).strip():
                    dev_conf.host = str(device.custom_host).strip()
                if getattr(device, "custom_port", None):
                    dev_conf.port = int(device.custom_port)
                if getattr(device, "use_tls", None) is not None:
                    dev_conf.use_tls = bool(device.use_tls)
            logger.info(f"Creating dedicated MQTT client for device '{device_id}' with ThingsBoard token on {dev_conf.host}:{dev_conf.port}")
            client = MqttConnection(
                dev_conf,
                on_message_callback=lambda top, pay: self._handle_device_message(device_id, top, pay),
                client_id_suffix=f"dev_{device_id}",
            )
            client.start()
            self.device_clients[device_id] = client

        return self.device_clients[device_id]

    def _handle_global_message(self, topic: str, payload: str) -> None:
        """Internal callback dispatch for messages received on the default client."""
        if self.on_rpc_callback:
            self.on_rpc_callback("global", topic, payload)

    def _handle_device_message(self, device_id: str, topic: str, payload: str) -> None:
        """Internal callback dispatch for messages received on a device-specific client."""
        if self.on_rpc_callback:
            self.on_rpc_callback(device_id, topic, payload)

    def publish_device_message(self, device_id: str, topic: str, payload: str, qos: int = 1) -> bool:
        """
        Publishes a message through a specific device's client connection.

        Args:
            device_id: Target device identifier.
            topic: Destination MQTT topic.
            payload: Payload string.
            qos: QoS level (default 1).

        Returns:
            bool: True if publish succeeded, False otherwise.
        """
        client = self.device_clients.get(device_id) or self.default_client
        if client:
            return client.publish(topic, payload, qos=qos)
        return False

    def stop_all(self) -> None:
        """Gracefully disconnects and stops all active MQTT clients."""
        if self.default_client:
            self.default_client.stop()
        for dev_id, c in list(self.device_clients.items()):
            try:
                c.stop()
            except Exception:
                pass
        self.device_clients.clear()
