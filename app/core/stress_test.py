"""
ThingsBoard Load & Stress-Test Generator (`msg/s` & `dp/s` Benchmarking).

Clones a virtual device profile into N concurrent virtual streams with randomized jitter
to empirically validate a ThingsBoard server against the Sizing Calculator's `dp/s` projections.
Supports both `dry_run` (local loopback benchmark) and live ThingsBoard HTTP REST v1 ingestion.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.transports.http_client import ThingsBoardHttpClient


class StressTestRequest(BaseModel):
    """Configuration for a bounded-duration multi-device stress test."""
    virtual_devices: int = Field(default=50, ge=1, le=2000, description="Number of simulated cloned devices")
    variables_per_device: int = Field(default=8, ge=1, le=100, description="Telemetry keys per message")
    interval_sec: float = Field(default=1.0, ge=0.1, le=60.0, description="Publish period per virtual device")
    duration_sec: int = Field(default=15, ge=1, le=300, description="Automatic stop duration in seconds")
    dry_run: bool = Field(default=True, description="True = local benchmark without network I/O; False = live HTTP POST")
    target_host: Optional[str] = Field(default=None, description="Target ThingsBoard host (for live mode)")
    target_port: int = Field(default=443, description="Target ThingsBoard port")
    use_tls: bool = Field(default=True, description="Use HTTPS in live mode")
    device_token: Optional[str] = Field(default=None, description="ThingsBoard access token (for live mode)")


class StressTestManager:
    """Manages an asynchronous load/stress test job and exposes live throughput metrics."""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self.running: bool = False
        self.started_at: float = 0.0
        self.finished_at: float = 0.0
        self.total_messages: int = 0
        self.total_data_points: int = 0
        self.errors: int = 0
        self.config: Optional[StressTestRequest] = None

    async def start(self, req: StressTestRequest) -> Dict[str, Any]:
        if self.running:
            await self.stop()
        self.config = req
        self.running = True
        self.started_at = time.time()
        self.finished_at = 0.0
        self.total_messages = 0
        self.total_data_points = 0
        self.errors = 0
        self._task = asyncio.create_task(self._run(req))
        return self.status()

    async def stop(self) -> Dict[str, Any]:
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if not self.finished_at:
            self.finished_at = time.time()
        return self.status()

    def status(self) -> Dict[str, Any]:
        now = time.time()
        elapsed = max(0.001, (self.finished_at or now) - self.started_at) if self.started_at else 0.0
        target_mps = round(self.config.virtual_devices / self.config.interval_sec, 2) if self.config else 0.0
        target_dps = round(target_mps * self.config.variables_per_device, 2) if self.config else 0.0
        achieved_mps = round(self.total_messages / elapsed, 2) if elapsed > 0 and self.started_at else 0.0
        achieved_dps = round(self.total_data_points / elapsed, 2) if elapsed > 0 and self.started_at else 0.0
        return {
            "running": self.running,
            "dry_run": self.config.dry_run if self.config else True,
            "virtual_devices": self.config.virtual_devices if self.config else 0,
            "variables_per_device": self.config.variables_per_device if self.config else 0,
            "duration_sec": self.config.duration_sec if self.config else 0,
            "elapsed_sec": round(elapsed, 2) if self.started_at else 0.0,
            "target_msg_per_sec": target_mps,
            "target_dp_per_sec": target_dps,
            "achieved_msg_per_sec": achieved_mps,
            "achieved_dp_per_sec": achieved_dps,
            "total_messages": self.total_messages,
            "total_data_points": self.total_data_points,
            "errors": self.errors,
        }

    async def _run(self, req: StressTestRequest) -> None:
        deadline = time.time() + req.duration_sec
        client = ThingsBoardHttpClient(timeout=5.0) if not req.dry_run else None
        endpoint = f"/api/v1/{req.device_token}/telemetry" if req.device_token else ""
        # Cap tick granularity at 100ms for smooth batched dispatch
        tick_sec = min(0.2, req.interval_sec)
        expected_per_tick = (req.virtual_devices / req.interval_sec) * tick_sec
        carry = 0.0

        try:
            while self.running and time.time() < deadline:
                t0 = time.time()
                carry += expected_per_tick
                batch_count = int(carry)
                carry -= batch_count

                if batch_count > 0:
                    if req.dry_run or not req.target_host or not req.device_token:
                        # Generate realistic JSON payload to measure serialization + throughput
                        for _ in range(batch_count):
                            payload = {
                                f"var_{k:02d}": round(20.0 + random.uniform(-2.5, 2.5), 2)
                                for k in range(req.variables_per_device)
                            }
                            _ = json.dumps(payload)
                            self.total_messages += 1
                            self.total_data_points += req.variables_per_device
                    else:
                        # Live HTTP POST with bounded concurrency
                        sem = asyncio.Semaphore(20)

                        async def _send_one() -> None:
                            async with sem:
                                payload = json.dumps({
                                    f"var_{k:02d}": round(20.0 + random.uniform(-2.5, 2.5), 2)
                                    for k in range(req.variables_per_device)
                                })
                                ok, _ = await client.post_payload(
                                    host=req.target_host,
                                    port=req.target_port,
                                    endpoint=endpoint,
                                    payload=payload,
                                    use_tls=req.use_tls,
                                )
                                if ok:
                                    self.total_messages += 1
                                    self.total_data_points += req.variables_per_device
                                else:
                                    self.errors += 1

                        await asyncio.gather(*(_send_one() for _ in range(min(batch_count, 50))))

                sleep_time = max(0.01, tick_sec - (time.time() - t0))
                await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            raise
        finally:
            self.running = False
            self.finished_at = time.time()
