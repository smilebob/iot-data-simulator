import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, SimMode, AnomalyType, DataType
from app.core.generators import MathSignalGenerator
from app.core.replay import ReplayEngine
from app.platforms import get_adapter
from app.storage.repository import StorageRepository
from app.mqtt.client import MqttManager
from app.transports.manager import TransportManager

logger = logging.getLogger("iot_sim.engine")

class SimulationEngine:
    """
    Moteur de simulation asynchrone non-bloquant.
    Gère le calcul périodique des variables, l'injection de défaillances et la transmission (MQTT, HTTP, CoAP).
    """

    def __init__(
        self,
        repository: StorageRepository,
        mqtt_manager: MqttManager,
        transport_manager: Optional[TransportManager] = None,
    ):
        self.repo = repository
        self.mqtt = mqtt_manager
        self.transports = transport_manager or TransportManager(repository, mqtt_manager)
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time = time.time()
        self._tick_interval = 0.5  # 500ms boucle de résolution
        self._ws_broadcast_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._anomaly_counters: Dict[str, int] = {}
        self._drift_offsets: Dict[str, float] = {}

        # Enregistrement du callback RPC Thingsboard
        self.mqtt.on_rpc_callback = self._handle_rpc

    def register_ws_broadcast(self, callback: Callable[[Dict[str, Any]], None]):
        self._ws_broadcast_callback = callback

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._start_time = time.time()
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Moteur de simulation démarré.")

    def stop(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Moteur de simulation arrêté.")

    async def _run_loop(self):
        while self.is_running:
            try:
                now = time.time()
                elapsed = now - self._start_time
                devices_map = {d.id: d for d in self.repo.get_devices() if d.enabled}
                variables = self.repo.get_variables()

                for var in variables:
                    if not var.enabled:
                        continue
                    device = devices_map.get(var.device_id)
                    if not device:
                        continue

                    # 1. Calcul de la valeur courante
                    new_val = self._compute_value(var, elapsed)
                    var.current_value = new_val

                    # 2. Vérification de l'intervalle de publication
                    should_publish = (
                        var.last_published is None or 
                        (now - var.last_published) >= max(var.publish_interval, 0.1)
                    )

                    published = False
                    topic_used = ""
                    payload_used = ""
                    protocol_used = getattr(device, "protocol", "mqtt")
                    if hasattr(protocol_used, "value"):
                        protocol_used = protocol_used.value.upper()
                    else:
                        protocol_used = str(protocol_used).upper()
                    channel_info = ""

                    if should_publish:
                        # Si anomalie timeout (perte de com), on saute la publication
                        if var.anomaly == AnomalyType.TIMEOUT:
                            continue

                        adapter = get_adapter(device.platform)
                        timestamp_ms = int(now * 1000)
                        topic_used, payload_used = adapter.format_message(
                            device=device,
                            variable=var,
                            value=new_val,
                            timestamp_ms=timestamp_ms,
                        )

                        # Transmission unifiée selon le protocole (MQTT, HTTP, CoAP)
                        published, protocol_used, channel_info = await self.transports.publish(
                            device=device,
                            variable=var,
                            payload=payload_used,
                            topic=topic_used,
                            timestamp_ms=timestamp_ms,
                        )

                        var.last_published = now

                    # 3. Notification WebSocket pour le rafraîchissement temps réel de la GUI
                    if self._ws_broadcast_callback:
                        self._ws_broadcast_callback({
                            "type": "telemetry",
                            "data": {
                                "variable_id": var.id,
                                "device_id": var.device_id,
                                "value": new_val,
                                "unit": var.unit,
                                "timestamp": now,
                                "published": published,
                                "protocol": protocol_used,
                                "topic": channel_info or topic_used,
                                "anomaly": var.anomaly.value,
                            }
                        })

                await asyncio.sleep(self._tick_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur boucle simulation: {e}")
                await asyncio.sleep(1.0)

    def _compute_value(self, var: VariableConfig, elapsed: float) -> Any:
        # Forçage manuel prioritaire
        if var.manual_override and var.manual_value is not None:
            return MathSignalGenerator._cast_type(var.manual_value, var.data_type)

        # Mode Gel
        if var.anomaly == AnomalyType.FREEZE and var.current_value is not None:
            return var.current_value

        # Calcul standard
        val: Any
        if var.sim_mode == SimMode.POINTS_TABLE:
            val = ReplayEngine.evaluate(var.points_config, elapsed, var.data_type)
        else:
            val = MathSignalGenerator.generate(
                mode=var.sim_mode,
                config=var.math_config,
                elapsed_seconds=elapsed,
                previous_value=var.current_value if isinstance(var.current_value, (int, float)) else None,
                data_type=var.data_type,
            )

        # Gestion des anomalies
        if var.anomaly == AnomalyType.SPIKE:
            # Pic ponctuel actif pendant 3 ticks puis réinitialisé
            cnt = self._anomaly_counters.get(var.id, 0)
            if cnt < 3:
                self._anomaly_counters[var.id] = cnt + 1
                if isinstance(val, (int, float)):
                    val = val + var.anomaly_magnitude
            else:
                var.anomaly = AnomalyType.NONE
                self._anomaly_counters[var.id] = 0

        elif var.anomaly == AnomalyType.DRIFT:
            # Dérive progressive
            curr_drift = self._drift_offsets.get(var.id, 0.0)
            curr_drift += (var.anomaly_magnitude / 100.0)
            self._drift_offsets[var.id] = curr_drift
            if isinstance(val, (int, float)):
                val = val + curr_drift
        else:
            self._drift_offsets[var.id] = 0.0

        return MathSignalGenerator._cast_type(val, var.data_type)

    def trigger_anomaly(self, var_id: str, anomaly: AnomalyType, magnitude: float = 50.0):
        """Déclenche une anomalie à la volée (idéal pour déclencher les alertes ThingsBoard)."""
        var = self.repo.get_variable(var_id)
        if var:
            var.anomaly = anomaly
            var.anomaly_magnitude = magnitude
            self._anomaly_counters[var_id] = 0
            if anomaly == AnomalyType.NONE:
                self._drift_offsets[var_id] = 0.0
            logger.info(f"Anomalie '{anomaly.value}' appliquée sur la variable {var_id}")

    def _handle_rpc(self, device_id: str, topic: str, payload: str):
        """Gestion des requêtes de contrôle ThingsBoard / MQTT entrantes."""
        logger.info(f"RPC reçu pour {device_id} sur {topic}: {payload}")
        for var in self.repo.get_variables():
            if var.device_id == device_id or device_id == "global":
                # Si le nom de la variable correspond à la méthode ou paramètre
                pass
