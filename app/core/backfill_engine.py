"""
Historical Time-Series Backfill Engine for ThingsBoard 4.3 Demonstrations.

Generates realistic retroactive telemetry (7 / 30 / 90 days) with:
- Diurnal (day/night) & weekday/weekend industrial modulation curves,
- Deterministic 3-pass causal physics evaluation (derived AST & continuous integrators),
- Optional historical anomaly spikes for retrospective root-cause demos,
- Batched ThingsBoard REST v1 ingestion (`POST /api/v1/{token}/telemetry` with `ts` epochs).
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.generators import MathSignalGenerator
from app.core.physics import SafeExpressionEvaluator
from app.core.scada_synoptics import get_clean_var_key
from app.models.device import DeviceConfig
from app.models.variable import DataType, SimMode, VariableConfig, VariableType
from app.storage.repository import StorageRepository
from app.transports.http_client import ThingsBoardHttpClient


class BackfillRequest(BaseModel):
    """Parameters for generating and pushing historical telemetry."""
    days: int = Field(default=7, ge=1, le=90, description="Number of past days to backfill (1 to 90)")
    step_minutes: int = Field(default=15, ge=1, le=60, description="Sampling interval in minutes")
    include_anomalies: bool = Field(default=True, description="Inject 1-2 realistic historical spikes")
    batch_size: int = Field(default=200, ge=10, le=500, description="Points per ThingsBoard HTTP batch")
    dry_run: bool = Field(default=False, description="Generate points without sending HTTP requests")


def _calendar_modulation(ts_sec: float) -> float:
    """Returns a smooth industrial activity factor (~0.70 night/weekend to ~1.10 daytime peak)."""
    dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
    hour_frac = dt.hour + dt.minute / 60.0
    # Diurnal curve peaking around 14:00 UTC, lowest around 03:00 UTC
    diurnal = 0.88 + 0.16 * math.sin(((hour_frac - 8.0) / 24.0) * 2.0 * math.pi)
    # Weekend slowdown (Saturday=5, Sunday=6)
    weekend_factor = 0.82 if dt.weekday() >= 5 else 1.0
    return diurnal * weekend_factor


def generate_historical_points(
    device: DeviceConfig,
    variables: List[VariableConfig],
    days: int = 7,
    step_minutes: int = 15,
    include_anomalies: bool = True,
    now_ts: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Computes chronological ThingsBoard telemetry records `[{"ts": ms, "values": {...}}]`."""
    end_ts = now_ts if now_ts is not None else time.time()
    step_sec = step_minutes * 60
    total_steps = max(1, int((days * 86400) // step_sec))
    start_ts = end_ts - total_steps * step_sec

    tel_vars = [v for v in variables if v.var_type == VariableType.TELEMETRY and v.enabled]
    if not tel_vars:
        return []

    base_vars = [v for v in tel_vars if v.sim_mode not in (SimMode.DERIVED, SimMode.INTEGRATOR)]
    derived_vars = [v for v in tel_vars if v.sim_mode == SimMode.DERIVED]
    integrator_vars = [v for v in tel_vars if v.sim_mode == SimMode.INTEGRATOR]

    # Pre-select up to 2 anomaly step indices (at ~35% and ~78% of timeline)
    anomaly_steps = set()
    if include_anomalies and total_steps >= 20:
        anomaly_steps.add(int(total_steps * 0.35))
        anomaly_steps.add(int(total_steps * 0.78))

    integrator_acc: Dict[str, float] = {
        v.id: float(v.integrator_config.initial_value) for v in integrator_vars
    }
    prev_source_vals: Dict[str, float] = {}
    records: List[Dict[str, Any]] = []

    for step_idx in range(total_steps + 1):
        ts_sec = start_ts + step_idx * step_sec
        elapsed = step_idx * step_sec
        cal_mod = _calendar_modulation(ts_sec)
        is_anomaly = step_idx in anomaly_steps

        values_by_id: Dict[str, Any] = {}
        values_clean: Dict[str, Any] = {}

        # Pass 1: Independent / mathematical signals
        for v in base_vars:
            clean_key = get_clean_var_key(v)
            raw_val = MathSignalGenerator.generate(
                v.sim_mode,
                v.math_config,
                elapsed,
                data_type=v.data_type,
            )
            if isinstance(raw_val, (int, float)) and not isinstance(raw_val, bool):
                mc = v.math_config
                mid = (mc.min_val + mc.max_val) / 2.0 if mc.max_val > mc.min_val else float(raw_val)
                span = max(0.1, (mc.max_val - mc.min_val))
                # Apply smooth calendar modulation around midpoint
                val = float(raw_val) * (0.35 + 0.65 * cal_mod)
                if is_anomaly:
                    val = mc.max_val + 0.25 * span if mc.max_val > mc.min_val else val * 1.35
                if v.data_type == DataType.INTEGER:
                    val = int(round(val))
                else:
                    val = round(val, 2)
            else:
                val = raw_val
            values_by_id[v.id] = val
            values_by_id[clean_key] = val
            values_clean[clean_key] = val

        # Pass 2: Derived variables (safe AST formulas)
        for v in derived_vars:
            clean_key = get_clean_var_key(v)
            formula = v.derived_config.formula.strip() if v.derived_config else ""
            if not formula:
                continue
            try:
                num_ctx = {
                    k: float(val)
                    for k, val in values_by_id.items()
                    if isinstance(val, (int, float)) and not isinstance(val, bool)
                }
                res = SafeExpressionEvaluator.evaluate(formula, num_ctx)
                val = int(round(res)) if v.data_type == DataType.INTEGER else round(float(res), 2)
                values_by_id[v.id] = val
                values_by_id[clean_key] = val
                values_clean[clean_key] = val
            except Exception:
                continue

        # Pass 3: Trapezoidal integrators (kWh, MWh, m³, etc.)
        for v in integrator_vars:
            clean_key = get_clean_var_key(v)
            src_id = v.integrator_config.source_variable_id
            src_val = values_by_id.get(src_id)
            if isinstance(src_val, (int, float)) and not isinstance(src_val, bool):
                prev = prev_source_vals.get(v.id, float(src_val))
                avg_rate = (prev + float(src_val)) / 2.0
                time_div = {"second": 1.0, "minute": 60.0, "hour": 3600.0}.get(
                    v.integrator_config.time_unit, 3600.0
                )
                delta = avg_rate * (step_sec / time_div) * float(v.integrator_config.multiplier)
                if step_idx > 0:
                    integrator_acc[v.id] += max(0.0, delta)
                prev_source_vals[v.id] = float(src_val)
            acc_val = round(integrator_acc[v.id], 3)
            values_by_id[v.id] = acc_val
            values_by_id[clean_key] = acc_val
            values_clean[clean_key] = acc_val

        records.append({
            "ts": int(ts_sec * 1000),
            "values": values_clean,
        })

    return records


async def execute_device_backfill(
    device_id: str,
    req: BackfillRequest,
    repo: Optional[StorageRepository] = None,
    http_client: Optional[ThingsBoardHttpClient] = None,
) -> Dict[str, Any]:
    """Generates and pushes batched historical telemetry to ThingsBoard HTTP REST v1."""
    storage = repo or StorageRepository()
    device = storage.get_device(device_id)
    if not device:
        raise ValueError(f"Équipement '{device_id}' introuvable.")

    variables = [v for v in storage.get_variables() if v.device_id == device_id]
    records = generate_historical_points(
        device=device,
        variables=variables,
        days=req.days,
        step_minutes=req.step_minutes,
        include_anomalies=req.include_anomalies,
    )

    if req.dry_run:
        return {
            "status": "dry_run",
            "device_id": device_id,
            "days": req.days,
            "step_minutes": req.step_minutes,
            "points_generated": len(records),
            "batches_sent": 0,
            "sample_first": records[0] if records else None,
            "sample_last": records[-1] if records else None,
        }

    if not device.token:
        raise ValueError(
            f"L'équipement '{device.name}' ne possède pas de Token ThingsBoard. "
            "Configurez un token ou utilisez 'Push ThingsBoard 1 clic' avant le backfill."
        )

    broker = storage.get_broker()
    host = device.custom_host or broker.host
    use_tls = device.use_tls if device.use_tls is not None else True
    port = device.custom_port or (443 if use_tls else 80)
    endpoint = f"/api/v1/{device.token}/telemetry"

    client = http_client or ThingsBoardHttpClient(timeout=15.0)
    batches_sent = 0
    errors: List[str] = []

    for i in range(0, len(records), req.batch_size):
        chunk = records[i : i + req.batch_size]
        ok, info = await client.post_payload(
            host=host,
            port=port,
            endpoint=endpoint,
            payload=json.dumps(chunk),
            use_tls=use_tls,
        )
        if ok:
            batches_sent += 1
        else:
            errors.append(f"Lot {i // req.batch_size + 1}: {info}")
            if len(errors) >= 3:
                break

    return {
        "status": "completed" if not errors else "partial_error",
        "device_id": device_id,
        "device_name": device.name,
        "days": req.days,
        "step_minutes": req.step_minutes,
        "points_generated": len(records),
        "batches_sent": batches_sent,
        "target_host": host,
        "errors": errors,
    }
