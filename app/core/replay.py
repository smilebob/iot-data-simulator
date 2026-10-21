import csv
import io
from typing import Any, List
from app.models.variable import PointsTableConfig, TimestampedPoint, DataType
from app.core.generators import MathSignalGenerator

class ReplayEngine:
    """
    Moteur de rejeu de tables de points horodatés et séries temporelles.
    Supporte la répétition (boucle), l'interpolation et le multiplicateur de vitesse.
    """

    @staticmethod
    def evaluate(
        config: PointsTableConfig,
        elapsed_seconds: float,
        data_type: DataType = DataType.FLOAT,
    ) -> Any:
        points = config.points
        if not points:
            return 0.0

        # Tri des points par offset_seconds
        sorted_points = sorted(points, key=lambda p: p.offset_seconds)
        total_duration = sorted_points[-1].offset_seconds

        if total_duration <= 0:
            return MathSignalGenerator._cast_type(sorted_points[0].value, data_type)

        # Application du multiplicateur de vitesse
        effective_time = elapsed_seconds * max(config.playback_speed, 0.01)

        if config.loop:
            t = effective_time % total_duration
        else:
            t = min(effective_time, total_duration)

        # Trouver les deux points encadrants
        p_prev = sorted_points[0]
        p_next = sorted_points[-1]

        for i in range(len(sorted_points) - 1):
            if sorted_points[i].offset_seconds <= t <= sorted_points[i + 1].offset_seconds:
                p_prev = sorted_points[i]
                p_next = sorted_points[i + 1]
                break

        if not config.interpolate or data_type in (DataType.BOOLEAN, DataType.STRING):
            return MathSignalGenerator._cast_type(p_prev.value, data_type)

        # Interpolation linéaire
        dt = p_next.offset_seconds - p_prev.offset_seconds
        if dt <= 1e-6:
            return MathSignalGenerator._cast_type(p_prev.value, data_type)

        alpha = (t - p_prev.offset_seconds) / dt
        try:
            v_prev = float(p_prev.value)
            v_next = float(p_next.value)
            interpolated = v_prev + alpha * (v_next - v_prev)
            return MathSignalGenerator._cast_type(interpolated, data_type)
        except (ValueError, TypeError):
            return MathSignalGenerator._cast_type(p_prev.value, data_type)

    @staticmethod
    def parse_csv_points(content: str) -> List[TimestampedPoint]:
        """
        Analyse sécurisée d'un flux CSV (colonnes offset_seconds, value ou time, value)
        """
        points: List[TimestampedPoint] = []
        reader = csv.reader(io.StringIO(content.strip()))
        first_row = True
        
        for row in reader:
            if not row or len(row) < 2:
                continue
            if first_row:
                first_row = False
                # Vérifier si c'est un en-tête
                try:
                    float(row[0])
                except ValueError:
                    continue  # C'est un en-tête (ex: 'time,val')

            try:
                offset_sec = float(row[0].strip())
                val_raw = row[1].strip()
                points.append(TimestampedPoint(offset_seconds=offset_sec, value=val_raw))
            except Exception:
                continue

        points.sort(key=lambda p: p.offset_seconds)
        return points
