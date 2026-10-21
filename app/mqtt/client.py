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
    Gestionnaire d'une connexion MQTT sécurisée avec reconnexion automatique.
    Conforme aux standards CIS (chiffrement TLS 1.2/1.3, validation stricte).
    """

    def __init__(
        self,
        config: BrokerConfig,
        on_message_callback: Optional[Callable[[str, str], None]] = None,
        client_id_suffix: str = "",
    ):
        self.config = config
        self.on_message_callback = on_message_callback
        self.is_connected = False
        self.last_error: Optional[str] = None
        self.messages_published = 0
        self._lock = threading.Lock()

        # Construction du client Paho
        client_id = f"{config.client_id_prefix}{client_id_suffix}_{int(time.time())}"
        try:
            # Compatibilité Paho MQTT v2.x
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id,
                protocol=mqtt.MQTTv311,
            )
        except AttributeError:
            # Paho MQTT v1.x fallback
            self.client = mqtt.Client(
                client_id=client_id,
                protocol=mqtt.MQTTv311,
            )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Configuration Authentification
        if config.username:
            self.client.username_pw_set(config.username, config.password)

        # Configuration Sécurisée TLS (CIS standard)
        if config.use_tls or config.port == 8883:
            self._configure_tls()

    def _configure_tls(self):
        try:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            # Recommandation CIS : TLS 1.2 minimum requis
            context.minimum_version = ssl.TLSVersion.TLSv1_2

            if self.config.ca_cert_path:
                context.load_verify_locations(cafile=self.config.ca_cert_path)
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = True
            else:
                # Mode permissif pour les brokers locaux / autosignés en test
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            self.client.tls_set_context(context)
            logger.info("TLS configuré avec succès (TLS 1.2+)")
        except Exception as e:
            logger.error(f"Erreur configuration TLS: {e}")
            self.last_error = str(e)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc.value if hasattr(rc, "value") else rc
        if rc_code == 0:
            self.is_connected = True
            self.last_error = None
            logger.info(f"Connecté au broker MQTT {self.config.host}:{self.config.port}")
            # Souscription automatique aux requêtes RPC ThingsBoard
            self.client.subscribe("v1/devices/me/rpc/request/+")
        else:
            self.is_connected = False
            self.last_error = f"Connexion refusée, code retour: {rc_code}"
            logger.warning(self.last_error)

    def _on_disconnect(self, client, userdata, flags, rc=None, properties=None):
        self.is_connected = False
        logger.info(f"Déconnecté du broker MQTT ({rc})")

    def _on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload = message.payload.decode("utf-8", errors="replace")
            logger.debug(f"Message reçu sur {topic}: {payload}")
            if self.on_message_callback:
                self.on_message_callback(topic, payload)
        except Exception as e:
            logger.error(f"Erreur réception message: {e}")

    def start(self):
        try:
            logger.info(f"Tentative de connexion à {self.config.host}:{self.config.port}...")
            self.client.connect_async(self.config.host, self.config.port, self.config.keepalive)
            self.client.loop_start()
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Impossible de démarrer le client MQTT: {e}")

    def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
        except Exception as e:
            logger.debug(f"Erreur arrêt client: {e}")

    def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False) -> bool:
        if not self.is_connected:
            return False
        with self._lock:
            try:
                res = self.client.publish(topic, payload, qos=qos, retain=retain)
                if res.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.messages_published += 1
                    return True
                else:
                    self.last_error = f"Erreur publication: code {res.rc}"
                    return False
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Exception publication MQTT: {e}")
                return False


class MqttManager:
    """
    Gestionnaire multi-clients : gère le client global ainsi que
    d'éventuels clients dédiés par équipement (ex: ThingsBoard avec tokens séparés).
    """

    def __init__(self, global_config: BrokerConfig):
        self.global_config = global_config
        self.default_client: Optional[MqttConnection] = None
        self.device_clients: Dict[str, MqttConnection] = {}
        self.on_rpc_callback: Optional[Callable[[str, str, str], None]] = None # (device_id, topic, payload)

    def start(self):
        self.default_client = MqttConnection(
            self.global_config,
            on_message_callback=self._handle_global_message,
            client_id_suffix="main",
        )
        self.default_client.start()

    def update_global_config(self, new_config: BrokerConfig):
        self.global_config = new_config
        if self.default_client:
            self.default_client.stop()
        self.start()

    def get_or_create_device_client(self, device_id: str, token: Optional[str]) -> MqttConnection:
        """
        Si un équipement a son propre token ThingsBoard, il utilise son client dédié.
        Sinon, il partage le client global.
        """
        if not token:
            return self.default_client

        if device_id not in self.device_clients:
            dev_conf = self.global_config.model_copy()
            dev_conf.username = token
            dev_conf.password = ""
            client = MqttConnection(
                dev_conf,
                on_message_callback=lambda top, pay: self._handle_device_message(device_id, top, pay),
                client_id_suffix=f"dev_{device_id}",
            )
            client.start()
            self.device_clients[device_id] = client

        return self.device_clients[device_id]

    def _handle_global_message(self, topic: str, payload: str):
        if self.on_rpc_callback:
            self.on_rpc_callback("global", topic, payload)

    def _handle_device_message(self, device_id: str, topic: str, payload: str):
        if self.on_rpc_callback:
            self.on_rpc_callback(device_id, topic, payload)

    def stop_all(self):
        if self.default_client:
            self.default_client.stop()
        for c in self.device_clients.values():
            c.stop()
        self.device_clients.clear()
