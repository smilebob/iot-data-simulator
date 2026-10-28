"""
Real-Time Asynchronous Simulation Engine.

Orchestrates multi-device physical simulation loops, deterministic mathematical generation,
3-pass causal dependency evaluation, continuous trapezoidal energy integration, fault injection,
bidirectional ThingsBoard 4.3 control (MQTT RPC, Shared Attributes, and HTTP Long-Polling),
and real-time WebSocket GUI streaming.
"""

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
    """Non-blocking asynchronous simulation coordinator.

    Runs periodic evaluation ticks (default: 500ms) calculating metrics, managing
    device listeners across multiple network protocols (MQTT, HTTP REST v1, CoAP),
    routing outbound telemetry, and servicing bidirectional inbound RPC commands.
    """

    def __init__(
        self,
        repository: StorageRepository,
        mqtt_manager: MqttManager,
        transport_manager: Optional[TransportManager] = None,
    ):
        """Initializes the simulation engine with repositories and transport managers.

        Args:
            repository: Thread-safe persistent configuration and state storage.
            mqtt_manager: Active Paho-MQTT connection coordinator.
            transport_manager: Optional unified transport router (MQTT, HTTP, CoAP).
        """
        self.repo = repository
        self.mqtt = mqtt_manager
        self.transports = transport_manager or TransportManager(repository, mqtt_manager)
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time = time.time()
        self._tick_interval = 0.5  # 500ms core resolution loop cadence
        self._ws_broadcast_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._anomaly_counters: Dict[str, int] = {}
        self._drift_offsets: Dict[str, float] = {}
        self._integrator_accumulators: Dict[str, float] = {}
        self._last_tick_time: float = time.time()
        self._http_rpc_tasks: Dict[str, asyncio.Task] = {}
        self._http_attr_tasks: Dict[str, asyncio.Task] = {}
        self._last_rpc_modified_key: Optional[str] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Register inbound MQTT RPC and shared attribute callback
        self.mqtt.on_rpc_callback = self._handle_rpc

    def register_ws_broadcast(self, callback: Callable[[Dict[str, Any]], None]):
        """Registers a callback handler to receive live telemetry and log packets for WebSockets.

        Args:
            callback: Callable accepting a JSON-serializable dictionary.
        """
        self._ws_broadcast_callback = callback

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Starts the asynchronous simulation background loop.

        Args:
            loop: Optional explicit asyncio event loop to attach background task.
        """
        if not self.is_running:
            self.is_running = True
            self._start_time = time.time()
            try:
                active_loop = loop or asyncio.get_running_loop()
                self._loop = active_loop
                self._task = active_loop.create_task(self._run_loop())
            except RuntimeError:
                # Handle cases where get_running_loop() is called from another thread
                if hasattr(self, "_loop") and self._loop and self._loop.is_running():
                    self._task = asyncio.run_coroutine_threadsafe(self._run_loop(), self._loop)
                else:
                    logger.error("Unable to start simulation: no active event loop found.")
                    self.is_running = False
                    return
            logger.info("Simulation engine started successfully.")

    def stop(self):
        """Stops the simulation loop and gracefully cancels all active polling worker tasks."""
        self.is_running = False
        if self._task:
            if hasattr(self._task, "cancel"):
                try:
                    self._task.cancel()
                except Exception:
                    pass
        # Cancel all active HTTP RPC long-polling workers
        for dev_id, t in list(self._http_rpc_tasks.items()):
            if not t.done():
                t.cancel()
        self._http_rpc_tasks.clear()

        # Cancel all active HTTP Shared Attributes polling workers
        for dev_id, t in list(self._http_attr_tasks.items()):
            if not t.done():
                t.cancel()
        self._http_attr_tasks.clear()
        logger.info("Simulation engine stopped.")

    def _sync_device_listeners(self, devices_map: Dict[str, DeviceConfig]):
        """Synchronizes bidirectional control listeners for active devices.

        Provisions or cleans up background listeners for:
        1. ThingsBoard HTTP Downstream RPC Long-Polling (GET /api/v1/{token}/rpc).
        2. ThingsBoard HTTP Shared Attributes Long-Polling (GET /api/v1/{token}/attributes/updates).
        3. ThingsBoard MQTT RPC and attribute subscription routing.

        Args:
            devices_map: Map of device IDs to their corresponding active DeviceConfig objects.
        """
        active_http_ids = set()
        for dev_id, dev in devices_map.items():
            try:
                platform_str = getattr(dev.platform, "value", str(dev.platform)).lower()
                is_thingsboard = (platform_str == PlatformType.THINGSBOARD.value)
                if is_thingsboard and dev.token:
                    proto_str = getattr(dev.protocol, "value", str(dev.protocol)).lower()
                    if proto_str == TransportProtocol.HTTP.value:
                        active_http_ids.add(dev_id)
                        # 1. Downstream RPC listener (One-way / Two-way control)
                        if dev_id not in self._http_rpc_tasks or self._http_rpc_tasks[dev_id].done():
                            self._http_rpc_tasks[dev_id] = asyncio.create_task(
                                self._poll_http_rpc_worker(dev)
                            )
                        # 2. Downstream Shared Attributes listener
                        if dev_id not in self._http_attr_tasks or self._http_attr_tasks[dev_id].done():
                            self._http_attr_tasks[dev_id] = asyncio.create_task(
                                self._poll_http_attributes_worker(dev)
                            )
                    elif proto_str == TransportProtocol.MQTT.value:
                        # Pre-connect dedicated MQTT client to start listening for control orders immediately
                        self.mqtt.get_or_create_device_client(dev.id, dev.token, dev)
            except Exception as e:
                logger.error(f"Error initializing bidirectional listener for '{dev_id}': {e}")

        # Clean up orphaned HTTP background workers for deleted or disabled devices
        for old_id in list(self._http_rpc_tasks.keys()):
            if old_id not in active_http_ids:
                task = self._http_rpc_tasks.pop(old_id, None)
                if task and not task.done():
                    task.cancel()
        for old_id in list(self._http_attr_tasks.keys()):
            if old_id not in active_http_ids:
                task = self._http_attr_tasks.pop(old_id, None)
                if task and not task.done():
                    task.cancel()

    async def _poll_http_rpc_worker(self, device: DeviceConfig):
        """Long-polling worker coroutine for ThingsBoard HTTP RPC commands.

        Continuously listens on `GET /api/v1/{token}/rpc?timeout=15000`. When a command
        is received, executes the control action, emits the mandatory synchronous
        response to `POST /api/v1/{token}/rpc/{id}`, and syncs the client-side attribute.

        Args:
            device: Target virtual device configuration.
        """
        token = device.token
        if not token:
            return

        global_broker = self.repo.get_broker()
        host = (device.custom_host or global_broker.host or "localhost").strip()
        if device.use_tls is not None:
            use_tls = device.use_tls
        elif device.custom_port == 443:
            use_tls = True
        elif device.custom_port == 80:
            use_tls = False
        else:
            is_local = host.lower().replace("http://", "").replace("https://", "").split(":")[0] in (
                "localhost", "127.0.0.1", "mosquitto", "thingsboard"
            )
            use_tls = False if is_local else True
        port = device.custom_port or (443 if use_tls else 80)

        clean_host_part = host.lower().replace("http://", "").replace("https://", "").split(":")[0]
        if clean_host_part in ("mosquitto", "localhost", "127.0.0.1"):
            logger.warning(
                f"⚠️ [HTTP RPC] Device '{device.id}' targets local '{host}:{port}'. "
                f"For remote ThingsBoard instances, configure custom host in device settings."
            )

        logger.info(f"✓ Active HTTP RPC listener for '{device.id}' ({host}:{port}, token: {token[:4]}***)")

        while self.is_running and device.enabled:
            try:
                t0 = time.time()
                rpc_data = await self.transports.http.poll_rpc(
                    host=host,
                    port=port,
                    token=token,
                    timeout_sec=15,
                    use_tls=use_tls,
                )
                if rpc_data and isinstance(rpc_data, dict):
                    req_id = rpc_data.get("id")
                    logger.info(f"📥 Received HTTP RPC command for '{device.id}' (ID #{req_id}): {rpc_data}")

                    # 1. Process command through unified simulation control logic
                    self._last_rpc_modified_key = None
                    resp_val = self._handle_rpc(device.id, f"v1/devices/me/rpc/request/{req_id}", json.dumps(rpc_data))

                    # 2. Mandatory synchronous response (POST /api/v1/{token}/rpc/{req_id})
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

                    # 3. Synchronize client-side attribute on ThingsBoard to confirm state toggle
                    method_name = rpc_data.get("method", "")
                    clean_name = self._last_rpc_modified_key or method_name.replace("set_", "").replace("toggle_", "")
                    if clean_name and resp_val is not None:
                        attr_payload = json.dumps({clean_name: resp_val})
                        await self.transports.http.post_payload(
                            host=host,
                            port=port,
                            endpoint=f"/api/v1/{token}/attributes",
                            payload=attr_payload,
                            use_tls=use_tls,
                        )
                else:
                    # Guard against tight loop on immediate network failure (< 1s)
                    if (time.time() - t0) < 1.0:
                        await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"HTTP RPC polling tick error for '{device.id}': {e}")
                await asyncio.sleep(2.0)

    async def _poll_http_attributes_worker(self, device: DeviceConfig):
        """Long-polling worker coroutine for ThingsBoard Shared Attributes updates.

        Synchronizes initial shared attributes on boot and continuously listens on
        `GET /api/v1/{token}/attributes/updates?timeout=20000` to apply dashboard switch toggles.

        Args:
            device: Target virtual device configuration.
        """
        token = device.token
        if not token:
            return

        global_broker = self.repo.get_broker()
        host = (device.custom_host or global_broker.host or "localhost").strip()
        if device.use_tls is not None:
            use_tls = device.use_tls
        elif device.custom_port == 443:
            use_tls = True
        elif device.custom_port == 80:
            use_tls = False
        else:
            is_local = host.lower().replace("http://", "").replace("https://", "").split(":")[0] in (
                "localhost", "127.0.0.1", "mosquitto", "thingsboard"
            )
            use_tls = False if is_local else True
        port = device.custom_port or (443 if use_tls else 80)

        logger.info(f"✓ Active HTTP Shared Attributes listener for '{device.id}' ({host}:{port}, token: {token[:4]}***)")

        # 1. Fetch initial shared attributes snapshot upon startup
        try:
            initial_shared = await self.transports.http.get_shared_attributes(host, port, token, use_tls=use_tls)
            if initial_shared and isinstance(initial_shared, dict) and len(initial_shared) > 0:
                logger.info(f"📋 Initial shared attributes synchronized for '{device.id}': {initial_shared}")
                self._handle_rpc(device.id, "v1/devices/me/attributes", json.dumps(initial_shared))
        except Exception as e:
            logger.debug(f"Initial get_shared_attributes failed for '{device.id}': {e}")

        # 2. Continuous long-polling loop (/api/v1/{token}/attributes/updates)
        while self.is_running and device.enabled:
            try:
                t0 = time.time()
                attr_data = await self.transports.http.poll_attribute_updates(
                    host=host,
                    port=port,
                    token=token,
                    timeout_sec=20,
                    use_tls=use_tls,
                )
                if attr_data and isinstance(attr_data, dict) and len(attr_data) > 0:
                    logger.info(f"📥 Received Shared Attribute update for '{device.id}': {attr_data}")
                    self._handle_rpc(device.id, "v1/devices/me/attributes", json.dumps(attr_data))

                    # Acknowledge back as client-side attribute
                    try:
                        await self.transports.http.post_payload(
                            host=host,
                            port=port,
                            endpoint=f"/api/v1/{token}/attributes",
                            payload=json.dumps(attr_data),
                            use_tls=use_tls,
                        )
                    except Exception as pe:
                        logger.debug(f"Failed to post client attribute echo: {pe}")
                else:
                    if (time.time() - t0) < 1.0:
                        await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"HTTP Attribute polling tick error for '{device.id}': {e}")
                await asyncio.sleep(2.0)

    async def _run_loop(self):
        """Primary periodic evaluation loop running every tick (500ms).

        Performs:
        1. Context assembly and 3-pass causal evaluation:
           - Pass 1: Primary driving signals (math waveforms, replays, constants).
           - Pass 2: Derived variables via sandboxed AST formulas.
           - Pass 3: Cumulative energy integrators (Riemann trapezoidal integration).
        2. Cadence check and telemetry dispatching across protocol transports.
        3. Real-time WebSocket streaming to frontend UI.
        """
        while self.is_running:
            try:
                now = time.time()
                elapsed = now - self._start_time
                dt = max(0.01, min(now - self._last_tick_time, 2.0))
                self._last_tick_time = now

                devices_map = {d.id: d for d in self.repo.get_devices() if d.enabled}
                self._sync_device_listeners(devices_map)
                variables = self.repo.get_variables()

                # Group evaluation contexts by device ID
                device_contexts: Dict[str, Dict[str, Any]] = {}
                for dev_id in devices_map:
                    device_contexts[dev_id] = {}

                # Segregate metrics into 3 causal dependency passes
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

                # Pass 1: Independent driving metrics (sine, square, ramp, replay)
                for var in primary_vars:
                    val = self._compute_primary_value(var, elapsed)
                    var.current_value = val
                    self._update_context(device_contexts, var, val)

                # Pass 2: Coupled physical formulas (AST evaluation)
                for var in derived_vars:
                    ctx = device_contexts.get(var.device_id, {})
                    val = self._compute_derived_value(var, ctx)
                    var.current_value = val
                    self._update_context(device_contexts, var, val)

                # Pass 3: Continuous time integrators (Energy = ∫ Power dt)
                for var in integrator_vars:
                    ctx = device_contexts.get(var.device_id, {})
                    val = self._compute_integrator_value(var, dt, ctx)
                    var.current_value = val
                    self._update_context(device_contexts, var, val)

                # Transmission and WebSocket emission across all active variables
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
                        # Skip publication if TIMEOUT anomaly is active (simulates network outage)
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

                        # Unified protocol transmission (MQTT, HTTP, CoAP)
                        published, protocol_used, channel_info = await self.transports.publish(
                            device=device,
                            variable=var,
                            payload=payload_used,
                            topic=topic_used,
                            timestamp_ms=timestamp_ms,
                        )

                        var.last_published = now

                    # Stream live update to frontend GUI over WebSockets
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
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(1.0)

    def _update_context(self, device_contexts: Dict[str, Dict[str, Any]], var: VariableConfig, val: Any):
        """Indexes variable values in multiple identifier formats for convenient formula resolution.

        Maps:
        - Exact full ID (e.g., 'comp_01_pressure')
        - Suffix key (e.g., 'pressure')
        - Human-readable name (e.g., 'Pression Réseau')
        """
        ctx = device_contexts.setdefault(var.device_id, {})
        ctx[var.id] = val
        if "_" in var.id:
            parts = var.id.split("_")
            short_key = "_".join(parts[1:])
            ctx[short_key] = val
            ctx[parts[-1]] = val
        ctx[var.name] = val

    def _compute_primary_value(self, var: VariableConfig, elapsed: float) -> Any:
        """Evaluates an independent primary metric value."""
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
        """Evaluates a physical dependent metric value using AST expression parsing."""
        if var.manual_override and var.manual_value is not None:
            return MathSignalGenerator._cast_type(var.manual_value, var.data_type)

        if var.anomaly == AnomalyType.FREEZE and var.current_value is not None:
            return var.current_value

        formula = getattr(var.derived_config, "formula", "")
        raw_val = SafeExpressionEvaluator.evaluate(formula, context)
        val = self._apply_anomalies(var, raw_val)
        return MathSignalGenerator._cast_type(val, var.data_type)

    def _compute_integrator_value(self, var: VariableConfig, dt: float, context: Dict[str, Any]) -> Any:
        """Computes continuous time integration: accumulator += source_rate * dt * scale."""
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
            # Fallback search by key suffix
            for k, v in context.items():
                if k.endswith(f"_{source_id}") or k == source_id:
                    try:
                        source_val = float(v)
                        break
                    except Exception:
                        pass

        # Temporal scale denominator (hours, minutes, seconds)
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
        """Applies configured fault injection (spikes, drift) on an evaluated metric."""
        if var.anomaly == AnomalyType.SPIKE:
            # Inject abnormal spike for exactly 3 ticks before automatically resetting
            cnt = self._anomaly_counters.get(var.id, 0)
            if cnt < 3:
                self._anomaly_counters[var.id] = cnt + 1
                if isinstance(val, (int, float)):
                    val = val + var.anomaly_magnitude
            else:
                var.anomaly = AnomalyType.NONE
                self._anomaly_counters[var.id] = 0

        elif var.anomaly == AnomalyType.DRIFT:
            # Progressive linear drift increment
            curr_drift = self._drift_offsets.get(var.id, 0.0)
            curr_drift += (var.anomaly_magnitude / 100.0)
            self._drift_offsets[var.id] = curr_drift
            if isinstance(val, (int, float)):
                val = val + curr_drift
        else:
            self._drift_offsets[var.id] = 0.0

        return MathSignalGenerator._cast_type(val, var.data_type)

    def trigger_anomaly(self, var_id: str, anomaly: AnomalyType, magnitude: float = 50.0):
        """Triggers a real-time fault or chaos injection on a specific variable.

        Args:
            var_id: Unique variable identifier.
            anomaly: Fault injection mode (SPIKE, DRIFT, FREEZE, TIMEOUT, or NONE).
            magnitude: Magnitude amplitude or bias deviation.
        """
        var = self.repo.get_variable(var_id)
        if var:
            var.anomaly = anomaly
            var.anomaly_magnitude = magnitude
            self._anomaly_counters[var_id] = 0
            if anomaly == AnomalyType.NONE:
                self._drift_offsets[var_id] = 0.0
            logger.info(f"Anomaly '{anomaly.value}' triggered on variable '{var_id}' (magnitude={magnitude})")

    def _handle_rpc(self, device_id: str, topic: str, payload: str):
        """Dispatches bidirectional control orders from ThingsBoard (MQTT RPC and Shared Attributes).

        Supports:
        - ThingsBoard Shared Attributes updates on `v1/devices/me/attributes`.
        - ThingsBoard Two-way / One-way RPC requests on `v1/devices/me/rpc/request/{id}`.
        - Direct method bindings (`setValue`, `toggle`, `set_<variable_name>`).
        - Immediate synchronous response and attribute acknowledgment.

        Args:
            device_id: Target device identifier.
            topic: Inbound destination topic.
            payload: Raw JSON string received from broker or long-poll HTTP.

        Returns:
            Any: Result value applied or returned to caller.
        """
        logger.info(f"Control command received for '{device_id}' on {topic}: {payload}")
        try:
            data = json.loads(payload) if payload else {}
        except Exception as e:
            logger.warning(f"Non-JSON control payload received on {topic}: {payload} ({e})")
            return

        variables = self.repo.get_variables()
        dev_vars = [v for v in variables if v.device_id == device_id or device_id == "global"]

        def get_clean_key(v: VariableConfig) -> str:
            """Strips device ID prefix to resolve short metric identifier."""
            if v.device_id and v.id.startswith(f"{v.device_id}_"):
                return v.id[len(v.device_id) + 1:]
            return v.id

        # Case 1: ThingsBoard Shared Attributes updates
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
                            logger.info(f"✓ ThingsBoard shared attribute applied for '{device_id}': {ck} = {cast_val}")
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

        # Case 2: ThingsBoard RPC request (round switches, buttons, sliders)
        if "rpc/request/" in topic:
            req_id = topic.split("/")[-1]
            method = data.get("method", "")
            params = data.get("params")

            target_var: Optional[VariableConfig] = None
            new_val: Any = None

            # Normalize method name for fuzzy matching
            norm_method = method.lower().replace("-", "_").replace(" ", "_")

            # 1. Direct variable name match in method name
            for var in dev_vars:
                ck = get_clean_key(var).lower()
                var_id_low = var.id.lower()
                var_name_low = var.name.lower().replace(" ", "_")
                candidates = {
                    f"set_{ck}", f"set{ck}", ck, f"toggle_{ck}", f"toggle{ck}",
                    f"set_{var_id_low}", f"set{var_id_low}", var_id_low,
                    f"set_{var_name_low}", f"set{var_name_low}", var_name_low,
                }
                if norm_method in candidates:
                    target_var = var
                    break

            # 2. Generic control methods (e.g. 'setValue', 'set', 'toggle', 'write')
            if not target_var and norm_method in ("setvalue", "set", "toggle", "write"):
                if isinstance(params, dict):
                    # Key-value dictionary passed in params (e.g., {"heater_mode": false})
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
                    # Prefer first ATTRIBUTE type metric
                    attr_vars = [v for v in dev_vars if v.var_type.value == "attribute"]
                    if attr_vars:
                        target_var = attr_vars[0]

            # 3. Getter read queries ('getValue', 'get_<key>')
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
                logger.info(f"✓ Emitted RPC GET response for '{device_id}' (req #{req_id}): {resp}")
                return cur_val

            if target_var:
                self._last_rpc_modified_key = get_clean_key(target_var)
                if norm_method.startswith("toggle"):
                    # Boolean flip
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
                logger.info(f"✓ Executed RPC command for '{device_id}': {get_clean_key(target_var)} = {new_val}")

                # Mandatory synchronous response preventing ThingsBoard switch timeout
                resp_payload = json.dumps({"status": "SUCCESS", "value": new_val})
                self.mqtt.publish_device_message(device_id, f"v1/devices/me/rpc/response/{req_id}", resp_payload)

                # Client-side attribute echo to finalize UI toggle state
                clean_name = get_clean_key(target_var)
                self.mqtt.publish_device_message(device_id, "v1/devices/me/attributes", json.dumps({clean_name: new_val}))

                # Immediately notify local simulator frontend via WebSocket
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
                # Emit NOT_FOUND response to prevent client hang
                self.mqtt.publish_device_message(device_id, f"v1/devices/me/rpc/response/{req_id}", json.dumps({"status": "NOT_FOUND"}))
                logger.warning(f"Ignored RPC command: no matching variable for method '{method}' on '{device_id}'")
                return None
