import math
import random
from typing import Any, Union
from app.models.variable import MathConfig, SimMode, DataType

class MathSignalGenerator:
    """
    Générateur de signaux mathématiques pur et déterministe.
    Conforme aux normes de sécurité (aucun eval() dynamique).
    """

    @staticmethod
    def generate(
        mode: SimMode,
        config: MathConfig,
        elapsed_seconds: float,
        previous_value: Union[float, int, None] = None,
        data_type: DataType = DataType.FLOAT,
    ) -> Any:
        min_v = config.min_val
        max_v = config.max_val
        period = max(config.period, 0.001)
        amplitude = (max_v - min_v) / 2.0
        mid = (max_v + min_v) / 2.0
        offset = config.offset

        # Phase relative dans la période courante [0.0, 1.0[
        phase = (elapsed_seconds % period) / period

        val: float = mid

        if mode == SimMode.CONSTANT:
            return MathSignalGenerator._cast_type(config.constant_val, data_type)

        elif mode == SimMode.SINE:
            val = mid + amplitude * math.sin(2.0 * math.pi * phase) + offset

        elif mode == SimMode.COSINE:
            val = mid + amplitude * math.cos(2.0 * math.pi * phase) + offset

        elif mode == SimMode.TRIANGLE:
            # Triangle symétrique montant puis descendant
            if phase < 0.5:
                val = min_v + (4.0 * amplitude) * phase
            else:
                val = max_v - (4.0 * amplitude) * (phase - 0.5)
            val += offset

        elif mode == SimMode.SQUARE:
            # Signal créneau 50% rapport cyclique
            val = (max_v if phase < 0.5 else min_v) + offset

        elif mode == SimMode.SAWTOOTH:
            # Dent de scie montante
            val = min_v + (max_v - min_v) * phase + offset

        elif mode == SimMode.RAMP:
            # Rampe linéaire
            steps = elapsed_seconds / period
            val = min_v + (steps * config.step) + offset
            if val > max_v:
                val = min_v + (val - min_v) % max(max_v - min_v, 1e-6)

        elif mode == SimMode.RANDOM_WALK:
            curr = float(previous_value) if previous_value is not None else mid
            delta = (random.random() * 2.0 - 1.0) * max(config.step, 0.1)
            val = max(min_v, min(max_v, curr + delta))

        elif mode == SimMode.GAUSSIAN:
            std_dev = max(amplitude / 3.0, 0.1)
            val = random.gauss(mid + offset, std_dev)

        # Ajout du bruit aléatoire optionnel (% d'amplitude)
        if config.noise_percent > 0:
            noise_range = (amplitude * 2.0) * (config.noise_percent / 100.0)
            noise = (random.random() * 2.0 - 1.0) * (noise_range / 2.0)
            val += noise

        # Clamp aux bornes configurées (sauf si mode libre)
        if mode not in (SimMode.CONSTANT,):
            val = max(min_v, min(max_v, val))

        return MathSignalGenerator._cast_type(val, data_type)

    @staticmethod
    def _cast_type(val: Any, data_type: DataType) -> Any:
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
                # FLOAT
                return round(float(val), 3)
        except Exception:
            return val
