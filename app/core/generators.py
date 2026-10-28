"""
Deterministic Mathematical Signal Generators.

Provides pure, safe, and deterministic generation of mathematical waveforms
(sine, cosine, triangle, square, sawtooth, ramp, random walk, Gaussian)
without any dynamic code execution (eval/exec) conforming strictly to CIS Docker Benchmark rules.
"""

import math
import random
from typing import Any, Union
from app.models.variable import MathConfig, SimMode, DataType


class MathSignalGenerator:
    """Mathematical signal engine evaluating periodic waves and stochastic processes.

    Computes deterministic metric values based on elapsed simulation time, configured
    waveforms, frequency periods, amplitudes, setpoint offsets, and optional Gaussian noise.
    """

    @staticmethod
    def generate(
        mode: SimMode,
        config: MathConfig,
        elapsed_seconds: float,
        previous_value: Union[float, int, None] = None,
        data_type: DataType = DataType.FLOAT,
    ) -> Any:
        """Generates a discrete simulated value at a given time offset.

        Calculates the instantaneous waveform phase and evaluates the corresponding
        mathematical function, superimposing configured noise, clamping to boundaries,
        and casting the final result to the target primitive data type.

        Args:
            mode: Desired mathematical waveform (sine, cosine, triangle, etc.).
            config: Mathematical boundaries, period, offset, and step parameters.
            elapsed_seconds: Total elapsed running time in seconds since start.
            previous_value: Last evaluated value, used for random walk recursion.
            data_type: Target primitive type for the generated value.

        Returns:
            Any: Computed metric value cast to the requested DataType (float, int, bool, or str).

        Example:
            >>> cfg = MathConfig(min_val=0.0, max_val=10.0, period=60.0)
            >>> MathSignalGenerator.generate(SimMode.SINE, cfg, 15.0)
            10.0
        """
        min_v = config.min_val
        max_v = config.max_val
        period = max(config.period, 0.001)
        amplitude = (max_v - min_v) / 2.0
        mid = (max_v + min_v) / 2.0
        offset = config.offset

        # Relative periodic phase normalized to the interval [0.0, 1.0)
        phase = (elapsed_seconds % period) / period

        val: float = mid

        if mode == SimMode.CONSTANT:
            # Fixed static setpoint or categorical label
            return MathSignalGenerator._cast_type(config.constant_val, data_type)

        elif mode == SimMode.SINE:
            # Sinusoidal periodic cycle: y = mid + A * sin(2π * phase) + offset
            val = mid + amplitude * math.sin(2.0 * math.pi * phase) + offset

        elif mode == SimMode.COSINE:
            # Cosinusoidal periodic cycle: y = mid + A * cos(2π * phase) + offset
            val = mid + amplitude * math.cos(2.0 * math.pi * phase) + offset

        elif mode == SimMode.TRIANGLE:
            # Symmetric triangle wave rising linearly then descending
            if phase < 0.5:
                val = min_v + (4.0 * amplitude) * phase
            else:
                val = max_v - (4.0 * amplitude) * (phase - 0.5)
            val += offset

        elif mode == SimMode.SQUARE:
            # Symmetrical square wave with 50% duty cycle
            val = (max_v if phase < 0.5 else min_v) + offset

        elif mode == SimMode.SAWTOOTH:
            # Linear upward sawtooth ramp resetting abruptly at phase boundary
            val = min_v + (max_v - min_v) * phase + offset

        elif mode == SimMode.RAMP:
            # Continuous progressive ramp incrementing by step per period
            steps = elapsed_seconds / period
            val = min_v + (steps * config.step) + offset
            if val > max_v:
                # Wrap around within defined boundaries
                val = min_v + (val - min_v) % max(max_v - min_v, 1e-6)

        elif mode == SimMode.RANDOM_WALK:
            # Bounded stochastic Brownian-like walk around previous state
            curr = float(previous_value) if previous_value is not None else mid
            delta = (random.random() * 2.0 - 1.0) * max(config.step, 0.1)
            val = max(min_v, min(max_v, curr + delta))

        elif mode == SimMode.GAUSSIAN:
            # Normally distributed random variations centered around setpoint
            std_dev = max(amplitude / 3.0, 0.1)
            val = random.gauss(mid + offset, std_dev)

        # Superimpose optional random white noise (% of total peak-to-peak amplitude)
        if config.noise_percent > 0:
            noise_range = (amplitude * 2.0) * (config.noise_percent / 100.0)
            noise = (random.random() * 2.0 - 1.0) * (noise_range / 2.0)
            val += noise

        # Clamp strictly between configured operational boundaries
        if mode not in (SimMode.CONSTANT,):
            val = max(min_v, min(max_v, val))

        return MathSignalGenerator._cast_type(val, data_type)

    @staticmethod
    def _cast_type(val: Any, data_type: DataType) -> Any:
        """Casts an evaluated numeric or raw value to the designated output DataType.

        Args:
            val: Raw numeric or text value to convert.
            data_type: Target data type specification.

        Returns:
            Any: Value converted to float (rounded to 3 decimals), integer, boolean, or string.
        """
        try:
            if data_type == DataType.INTEGER:
                return int(round(float(val)))
            elif data_type == DataType.BOOLEAN:
                if isinstance(val, str):
                    return val.lower() in ("true", "1", "yes", "on")
                return bool(val)
            elif data_type == DataType.STRING:
                return str(val)
            else:
                # Default floating-point precision rounded to 3 decimal places
                return round(float(val), 3)
        except Exception:
            return val
