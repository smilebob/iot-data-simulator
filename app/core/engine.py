import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from app.models.device import DeviceConfig, PlatformType, TransportProtocol
from app.models.variable import VariableConfig, SimMode, AnomalyType, DataType
from app.core.generators import MathSignalGenerator
from app.core.replay import ReplayEngine
from app.core.physics import SafeExpressionEvaluator
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
        self._integrator_accumulators: Dict[str, float] = {}
        self._last_tick_time: float = time.time()
        self._http_rpc_tasks: Dict[str, asyncio.Task] = {}

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
        for dev_id, t in list(self._http_rpc_tasks.items()):
            if not t.done():
                t.cancel()
        self._http_rpc_tasks.clear()
        logger.info("Moteur de simulation arrêté.")

    def _sync_device_listeners(self, devices_map: Dict[str, DeviceConfig]):
        """Synchronise les abonnements de contrôle bidirectionnel (MQTT et Long-Polling HTTP)."""
        active_http_ids = set()
        for dev_id, dev in devices_map.items():
            try:
                platform_str = getattr(dev.platform, "value", str(dev.platform)).lower()
                is_thingsboard = (platform_str == PlatformType.THINGSBOARD.value)
                if is_thingsboard and dev.token:
                    proto_str = getattr(dev.protocol, "value", str(dev.protocol)).lower()
                    if proto_str == TransportProtocol.HTTP.value:
                        active_http_ids.add(dev_id)
                        if dev_id not in self._http_rpc_tasks or self._http_rpc_tasks[dev_id].done():
                            self._http_rpc_tasks[dev_id] = asyncio.create_task(
                                self._poll_http_rpc_worker(dev)
                            )
                    elif proto_str == TransportProtocol.MQTT.value:
                        # Pré-connexion du client MQTT pour écouter les ordres dès le démarrage
                        self.mqtt.get_or_create_device_client(dev.id, dev.token, dev)
            except Exception as e:
                logger.error(f"Erreur initialisation listener pour '{dev_id}': {e}")

        # Nettoyage des tâches HTTP orphelines
        for old_id in list(self._http_rpc_tasks.keys()):
            if old_id not in active_http_ids:
                task = self._http_rpc_tasks.pop(old_id, None)
                if task and not task.done():
                    task.cancel()

    async def _poll_http_rpc_worker(self, device: DeviceConfig):
        """Boucle de Long-Polling HTTP pour recevoir les ordres RPC ThingsBoard en continu."""
        token = device.token
        if not token:
            return

        global_broker = self.repo.get_broker()
        host = (device.custom_host or global_broker.host or "localhost").strip()
        use_tls = device.use_tls if device.use_tls is not None else True
        port = device.custom_port or (443 if use_tls else 80)

        logger.info(f"✓ Listener RPC HTTP activé pour '{device.id}' ({host}:{port}, token: {token[:4]}***)")

        while self.is_running and device.enabled:
            try:
                rpc_data = await self.transports.http.poll_rpc(
                    host=host,
                    port=port,
                    token=token,
                    timeout_sec=15,
                    use_tls=use_tls,
                )
                if rpc_data and isinstance(rpc_data, dict):
                    req_id = rpc_data.get("id")
                    logger.info(f"📥 Commande RPC HTTP reçue pour '{device.id}' (ID #{req_id}) : {rpc_data}")

                    # 1. Traitement de la commande par la logique commune
                    resp_val = self._handle_rpc(device.id, f"v1/devices/me/rpc/request/{req_id}", json.dumps(rpc_data))

                    # 2. Réponse synchrone HTTP POST /api/v1/{token}/rpc/{req_id}
                    if req_id is not None:
                        resp_payload = json.dumps({"status": "SUCCESS", "value": resp_val if resp_val is not None else True})
                        await self.transports.http.respond_rpc(
                            host=host,
                            port=port,
                            token=token,
                            req_id=req_id,
                            resp_payload=resp_payload,
                            use_tls=use_tls,
                        )

                    # 3. Synchronisation immédiate de l'attribut client sur ThingsBoard
                    method_name = rpc_data.get("method", "")
                    clean_name = method_name.replace("set_", "").replace("toggle_", "")
                    if clean_name and resp_val is not None:
                        attr_payload = json.dumps({clean_name: resp_val})
                        await self.transports.http.post_payload(
                            host=host,
                            port=port,
                            endpoint=f"/api/v1/{token}/attributes",
                            payload=attr_payload,
                            use_tls=use_tls,
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Tick polling RPC HTTP pour '{device.id}': {e}")
                await asyncio.sleep(2.0)

    async def _run_loop(self):
        while self.is_running:
            try:
                now = time.time()
                elapsed = now - self._start_time
                dt = max(0.01, min(now - self._last_tick_time, 2.0))
                self._last_tick_time = now

                devices_map = {d.id: d for d in self.repo.get_devices() if d.enabled}
                self._sync_device_listeners(devices_map)
                variables = self.repo.get_variables()

                # 1. Organisation du contexte de calcul par équipement
                device_contexts: Dict[str, Dict[str, Any]] = {}
                for dev_id in devices_map:
                    device_contexts[dev_id] = {}

                # Séparation des variables en 3 passes d'évaluation causale
                primary_vars: List[VariableConfig] = []
                derived_vars: List[VariableConfig] = []
                integrator_vars: List[VariableConfig] = []

                for var in variables:
                    if not var.enabled or var.device_id not in devices_map:
                        continue
                    if var.sim_mode == SimMode.DERIVED:
                        derived_vars.append(var)
                    elif var.sim_mode == SimMode.INTEGRATOR:
                        integrator_vars.append(var)
                    else:
                        primary_vars.append(var)

                # Passe 1 : Évaluation des grandeurs motrices indépendantes
                for var in primary_vars:
                    val = self._compute_primary_value(var, elapsed)
                    var.current_value = val
                    self._update_context(device_contexts, var, val)

                # Passe 2 : Évaluation des grandeurs dérivées (formules physiques couplées)
                for var in derived_vars:
                    ctx = device_contexts.get(var.device_id, {})
                    val = self._compute_derived_value(var, ctx)
                    var.current_value = val
                    self._update_context(device_contexts, var, val)

                # Passe 3 : Évaluation des intégrateurs temporels continus (énergie = ∫ P dt)
                for var in integrator_vars:
                    ctx = device_contexts.get(var.device_id, {})
                    val = self._compute_integrator_value(var, dt, ctx)
                    var.current_value = val
                    self._update_context(device_contexts, var, val)

                # 2. Publication et streaming WebSocket pour toutes les variables actives
                all_active_vars = primary_vars + derived_vars + integrator_vars
                for var in all_active_vars:
                    device = devices_map.get(var.device_id)
                    if not device:
                        continue

                    new_val = var.current_value
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
                                "anomaly": getattr(var.anomaly, "value", str(var.anomaly)),
                            }
                        })

                await asyncio.sleep(self._tick_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur boucle simulation: {e}")
                await asyncio.sleep(1.0)

    def _update_context(self, device_contexts: Dict[str, Dict[str, Any]], var: VariableConfig, val: Any):
        ctx = device_contexts.setdefault(var.device_id, {})
        ctx[var.id] = val
        # Clé courte (ex: si var.id == 'comp_01_pression', on enregistre aussi 'pression')
        if "_" in var.id:
            parts = var.id.split("_")
            short_key = "_".join(parts[1:])
            ctx[short_key] = val
            # Dernière partie comme clé directe (ex: 'pression')
            ctx[parts[-1]] = val
        ctx[var.name] = val

    def _compute_primary_value(self, var: VariableConfig, elapsed: float) -> Any:
        if var.manual_override and var.manual_value is not None:
            return MathSignalGenerator._cast_type(var.manual_value, var.data_type)

        if var.anomaly == AnomalyType.FREEZE and var.current_value is not None:
            return var.current_value

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
        return self._apply_anomalies(var, val)

    def _compute_derived_value(self, var: VariableConfig, context: Dict[str, Any]) -> Any:
        if var.manual_override and var.manual_value is not None:
            return MathSignalGenerator._cast_type(var.manual_value, var.data_type)

        if var.anomaly == AnomalyType.FREEZE and var.current_value is not None:
            return var.current_value

        formula = getattr(var.derived_config, "formula", "")
        raw_val = SafeExpressionEvaluator.evaluate(formula, context)
        val = self._apply_anomalies(var, raw_val)
        return MathSignalGenerator._cast_type(val, var.data_type)

    def _compute_integrator_value(self, var: VariableConfig, dt: float, context: Dict[str, Any]) -> Any:
        if var.manual_override and var.manual_value is not None:
            return MathSignalGenerator._cast_type(var.manual_value, var.data_type)

        if var.anomaly == AnomalyType.FREEZE and var.current_value is not None:
            return var.current_value

        source_id = getattr(var.integrator_config, "source_variable_id", "")
        source_val = 0.0
        if source_id in context:
            try:
                source_val = float(context[source_id])
            except Exception:
                pass
        else:
            # Recherche par suffixe
            for k, v in context.items():
                if k.endswith(f"_{source_id}") or k == source_id:
                    try:
                        source_val = float(v)
                        break
                    except Exception:
                        pass

        # Facteur temporel (heures, minutes, secondes)
        time_unit = getattr(var.integrator_config, "time_unit", "hour").lower()
        if time_unit == "hour":
            dt_unit = dt / 3600.0
        elif time_unit == "minute":
            dt_unit = dt / 60.0
        else:
            dt_unit = dt

        multiplier = getattr(var.integrator_config, "multiplier", 1.0)
        increment = source_val * dt_unit * multiplier

        acc = self._integrator_accumulators.get(var.id)
        if acc is None:
            init_v = getattr(var.integrator_config, "initial_value", 0.0)
            acc = float(init_v if init_v is not None else (var.current_value if var.current_value is not None else 0.0))

        acc += increment
        self._integrator_accumulators[var.id] = acc

        val = self._apply_anomalies(var, acc)
        return MathSignalGenerator._cast_type(val, var.data_type)

    def _apply_anomalies(self, var: VariableConfig, val: Any) -> Any:
        if var.anomaly == AnomalyType.SPIKE:
            cnt = self._anomaly_counters.get(var.id, 0)
            if cnt < 3:
                self._anomaly_counters[var.id] = cnt + 1
                if isinstance(val, (int, float)):
                    val = val + var.anomaly_magnitude
            else:
                var.anomaly = AnomalyType.NONE
                self._anomaly_counters[var.id] = 0

        elif var.anomaly == AnomalyType.DRIFT:
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
        """Gestion bidirectionnelle des requêtes ThingsBoard / MQTT entrantes (RPC et Shared Attributes)."""
        logger.info(f"Message de contrôle reçu pour '{device_id}' sur {topic}: {payload}")
        try:
            data = json.loads(payload) if payload else {}
        except Exception as e:
            logger.warning(f"Payload de contrôle non JSON reçu sur {topic}: {payload} ({e})")
            return

        variables = self.repo.get_variables()
        dev_vars = [v for v in variables if v.device_id == device_id or device_id == "global"]

        def get_clean_key(v: VariableConfig) -> str:
            if v.device_id and v.id.startswith(f"{v.device_id}_"):
                return v.id[len(v.device_id) + 1:]
            return v.id

        # CAS 1 : Mise à jour d'Attributs Partagés (Shared Attributes)
        # ThingsBoard publie directement les modifications sur 'v1/devices/me/attributes'
        if topic == "v1/devices/me/attributes" or "attributes" in topic:
            if isinstance(data, dict):
                modified = False
                for key, val in data.items():
                    for var in dev_vars:
                        ck = get_clean_key(var)
                        if ck == key or var.id == key or var.name.lower() == key.lower():
                            cast_val = MathSignalGenerator._cast_type(val, var.data_type)
                            var.current_value = cast_val
                            var.manual_override = True
                            var.manual_value = cast_val
                            if var.math_config and var.sim_mode == SimMode.CONSTANT:
                                var.math_config.constant_val = cast_val
                            modified = True
                            logger.info(f"✓ Attribut partagé ThingsBoard appliqué pour '{device_id}' : {ck} = {cast_val}")
                if modified:
                    self.repo.save_variables(variables)
                    if self._ws_broadcast_callback:
                        for var in dev_vars:
                            self._ws_broadcast_callback({
                                "type": "telemetry",
                                "data": {
                                    "variable_id": var.id,
                                    "device_id": var.device_id,
                                    "value": var.current_value,
                                    "unit": var.unit,
                                    "timestamp": time.time(),
                                    "published": True,
                                    "protocol": "MQTT",
                                    "topic": "v1/devices/me/attributes",
                                    "anomaly": getattr(var.anomaly, "value", str(var.anomaly)),
                                }
                            })
            return

        # CAS 2 : Requête RPC ThingsBoard (Boutons, Switches, Sliders)
        # Topic format : v1/devices/me/rpc/request/{request_id}
        if "rpc/request/" in topic:
            req_id = topic.split("/")[-1]
            method = data.get("method", "")
            params = data.get("params")

            target_var: Optional[VariableConfig] = None
            new_val: Any = None

            # Normalisation de la méthode RPC
            norm_method = method.lower().replace("-", "_").replace(" ", "_")

            # 1. Recherche par correspondance de nom de variable dans la méthode
            for var in dev_vars:
                ck = get_clean_key(var).lower()
                if norm_method in (f"set_{ck}", f"set{ck}", ck, f"toggle_{ck}", f"toggle{ck}"):
                    target_var = var
                    break

            # 2. Si la méthode est générique (ex: 'setValue', 'set', 'toggle', 'write')
            if not target_var and norm_method in ("setvalue", "set", "toggle", "write"):
                if isinstance(params, dict):
                    # params contient un dictionnaire clé/valeur ex: {"mode_chaud": false}
                    for k, v in params.items():
                        for var in dev_vars:
                            if get_clean_key(var).lower() == k.lower():
                                target_var = var
                                params = v
                                break
                        if target_var:
                            break
                elif len(dev_vars) == 1:
                    target_var = dev_vars[0]
                else:
                    # Préférer la première variable de type ATTRIBUTE de l'équipement
                    attr_vars = [v for v in dev_vars if v.var_type.value == "attribute"]
                    if attr_vars:
                        target_var = attr_vars[0]

            # 3. Si la méthode est une lecture d'état ('getValue', 'get_<key>')
            if norm_method.startswith("get"):
                read_var = target_var
                if not read_var:
                    for var in dev_vars:
                        ck = get_clean_key(var).lower()
                        if norm_method in (f"get_{ck}", f"get{ck}", "getvalue"):
                            read_var = var
                            break
                cur_val = read_var.current_value if read_var else True
                resp = json.dumps({"value": cur_val, "status": "SUCCESS"})
                self.mqtt.publish_device_message(device_id, f"v1/devices/me/rpc/response/{req_id}", resp)
                logger.info(f"✓ Réponse RPC GET émise pour '{device_id}' (req #{req_id}) : {resp}")
                return

            if target_var:
                if norm_method.startswith("toggle"):
                    # Bascule booléenne
                    cur = bool(target_var.current_value)
                    new_val = not cur
                elif params is not None:
                    new_val = MathSignalGenerator._cast_type(params, target_var.data_type)
                else:
                    new_val = True

                target_var.current_value = new_val
                target_var.manual_override = True
                target_var.manual_value = new_val
                if target_var.math_config and target_var.sim_mode == SimMode.CONSTANT:
                    target_var.math_config.constant_val = new_val

                self.repo.save_variables(variables)
                logger.info(f"✓ Commande RPC exécutée avec succès pour '{device_id}' : {get_clean_key(target_var)} = {new_val}")

                # Réponse RPC obligatoire pour valider la bascule du switch ThingsBoard
                resp_payload = json.dumps({"status": "SUCCESS", "value": new_val})
                self.mqtt.publish_device_message(device_id, f"v1/devices/me/rpc/response/{req_id}", resp_payload)

                # Synchronisation d'attribut retour pour acquitter ThingsBoard
                clean_name = get_clean_key(target_var)
                self.mqtt.publish_device_message(device_id, "v1/devices/me/attributes", json.dumps({clean_name: new_val}))

                # Actualisation immédiate du dashboard web local du simulateur
                if self._ws_broadcast_callback:
                    self._ws_broadcast_callback({
                        "type": "telemetry",
                        "data": {
                            "variable_id": target_var.id,
                            "device_id": target_var.device_id,
                            "value": target_var.current_value,
                            "unit": target_var.unit,
                            "timestamp": time.time(),
                            "published": True,
                            "protocol": "MQTT",
                            "topic": "v1/devices/me/attributes",
                            "anomaly": getattr(target_var.anomaly, "value", str(target_var.anomaly)),
                        }
                    })
                return new_val
            else:
                # Répondre tout de même pour éviter le timeout de ThingsBoard
                self.mqtt.publish_device_message(device_id, f"v1/devices/me/rpc/response/{req_id}", json.dumps({"status": "NOT_FOUND"}))
                logger.warning(f"Commande RPC ignorée : aucune variable correspondante pour {method} sur '{device_id}'")
                return None
