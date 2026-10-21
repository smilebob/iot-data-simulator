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
    Supporte les transports TCP standard (1883/8883) et WebSockets (443/9001).
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
        transport_mode = getattr(config, "transport", "tcp").lower()

        try:
            # Compatibilité Paho MQTT v2.x
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
            logger.info(f"Transport WebSockets activé sur le path: {ws_path}")

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Configuration Authentification
        if config.username:
            self.client.username_pw_set(config.username, config.password or "")

        # Configuration Sécurisée TLS (CIS standard ou port 8883 / 443)
        if config.use_tls or config.port in (8883, 443):
            self._configure_tls()

    def _configure_tls(self):
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
            logger.info(f"TLS 1.2+ configuré pour {self.config.host}:{self.config.port}")
        except Exception as e:
            err_msg = f"Erreur configuration TLS sur {self.config.host}: {e}"
            logger.error(err_msg)
            self.last_error = err_msg

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc.value if hasattr(rc, "value") else rc
        if rc_code == 0:
            self.is_connected = True
            self.last_error = None
            logger.info(f"✓ Connecté avec succès au broker MQTT {self.config.host}:{self.config.port} ({self.config.transport})")
            # Souscription bidirectionnelle ThingsBoard : RPC et Attributs partagés (Shared Attributes)
            self.client.subscribe([
                ("v1/devices/me/rpc/request/+", 1),
                ("v1/devices/me/attributes", 1),
                ("v1/devices/me/attributes/response/+", 1),
            ])
        else:
            self.is_connected = False
            reasons = {
                1: "Protocole MQTT non supporté",
                2: "Identifiant client rejeté",
                3: "Serveur MQTT indisponible",
                4: "Nom d'utilisateur ou mot de passe / Token ThingsBoard invalide",
                5: "Non autorisé",
            }
            reason = reasons.get(rc_code, f"Code retour {rc_code}")
            self.last_error = f"Connexion refusée par {self.config.host}:{self.config.port} ({reason})"
            logger.error(self.last_error)

    def _on_disconnect(self, client, userdata, flags, rc=None, properties=None):
        self.is_connected = False
        rc_code = rc.value if hasattr(rc, "value") else (rc if rc is not None else 0)
        if rc_code != 0:
            msg = f"Déconnexion inattendue du broker MQTT {self.config.host}:{self.config.port} (code {rc_code})"
            self.last_error = msg
            logger.warning(msg)
        else:
            logger.info(f"Déconnecté du broker MQTT {self.config.host}:{self.config.port}")

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
            logger.info(f"Tentative de connexion MQTT vers {self.config.host}:{self.config.port} (TLS={self.config.use_tls}, transport={self.config.transport})...")
            self.client.connect_async(self.config.host, self.config.port, self.config.keepalive)
            self.client.loop_start()
        except Exception as e:
            self.last_error = f"Échec démarrage connexion vers {self.config.host}:{self.config.port}: {e}"
            logger.error(self.last_error)

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
                    self.last_error = f"Erreur publication sur {topic}: code {res.rc}"
                    logger.warning(self.last_error)
                    return False
            except Exception as e:
                self.last_error = f"Exception publication MQTT: {e}"
                logger.error(self.last_error)
                return False


class MqttManager:
    """
    Gestionnaire multi-clients : gère le client global ainsi que
    les clients dédiés par équipement ThingsBoard (avec Tokens distincts).
    """

    def __init__(self, global_config: BrokerConfig):
        self.global_config = global_config
        self.default_client: Optional[MqttConnection] = None
        self.device_clients: Dict[str, MqttConnection] = {}
        self.on_rpc_callback: Optional[Callable[[str, str, str], None]] = None

    def start(self):
        self.default_client = MqttConnection(
            self.global_config,
            on_message_callback=self._handle_global_message,
            client_id_suffix="main",
        )
        self.default_client.start()

    def update_global_config(self, new_config: BrokerConfig):
        """
        Applique la nouvelle configuration du broker à CHAUD
        en arrêtant ET en reconnectant TOUS les clients (global et par équipement).
        """
        logger.info(f"🔄 Application de la nouvelle configuration Broker MQTT -> Hôte: {new_config.host}:{new_config.port} (TLS={new_config.use_tls}, Transport={new_config.transport})")
        self.global_config = new_config
        self.stop_all()
        self.start()

    def remove_device_client(self, device_id: str):
        """Arrête et supprime le client dédié d'un équipement (ex: lors d'une modification de token)."""
        if device_id in self.device_clients:
            logger.info(f"Arrêt et suppression du client MQTT dédié pour {device_id}")
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
            logger.info(f"Création d'un client MQTT dédié pour l'équipement '{device_id}' avec token ThingsBoard sur {dev_conf.host}:{dev_conf.port}")
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

    def publish_device_message(self, device_id: str, topic: str, payload: str, qos: int = 1) -> bool:
        """Publie un message (ex: acquittement RPC ou synchronisation d'attribut) sur le client MQTT de l'équipement."""
        client = self.device_clients.get(device_id) or self.default_client
        if client:
            return client.publish(topic, payload, qos=qos)
        return False

    def stop_all(self):
        if self.default_client:
            self.default_client.stop()
        for dev_id, c in list(self.device_clients.items()):
            try:
                c.stop()
            except Exception:
                pass
        self.device_clients.clear()
