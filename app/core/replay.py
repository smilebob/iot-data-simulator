"""
Time-Series Points Replay and Interpolation Engine.

Provides evaluation of pre-recorded time-series profiles with support for looping,
playback speed scaling, linear interpolation, and CSV profile parsing.
"""

import csv
import io
from typing import Any, List
from app.models.variable import PointsTableConfig, TimestampedPoint, DataType
from app.core.generators import MathSignalGenerator


class ReplayEngine:
    """Evaluates discrete time-series profiles with optional continuous interpolation.

    Calculates simulated values by finding the temporal interval bounding the current
    elapsed simulation time, scaling by playback speed, and linearly interpolating
    between the adjacent points.
    """

    @staticmethod
    def evaluate(
        config: PointsTableConfig,
        elapsed_seconds: float,
        data_type: DataType = DataType.FLOAT,
    ) -> Any:
        """Evaluates the instantaneous value of a time-series replay profile.

        Args:
            config: Points sequence settings (points list, loop flag, speed, interpolation).
            elapsed_seconds: Total elapsed simulation time in seconds.
            data_type: Target data type for output casting.

        Returns:
            Any: Interpolated or discrete point value cast to the requested DataType.

        Example:
            >>> pts = [TimestampedPoint(offset_seconds=0, value=10), TimestampedPoint(offset_seconds=10, value=20)]
            >>> cfg = PointsTableConfig(points=pts, loop=True, interpolate=True)
            >>> ReplayEngine.evaluate(cfg, 5.0)
            15.0
        """
        points = config.points
        if not points:
            return 0.0

        # Ensure points are strictly sorted by chronological offset
        sorted_points = sorted(points, key=lambda p: p.offset_seconds)
        total_duration = sorted_points[-1].offset_seconds

        if total_duration <= 0:
            return MathSignalGenerator._cast_type(sorted_points[0].value, data_type)

        # Apply playback acceleration or deceleration multiplier
        effective_time = elapsed_seconds * max(config.playback_speed, 0.01)

        if config.loop:
            t = effective_time % total_duration
        else:
            t = min(effective_time, total_duration)

        # Locate the bounding interval [p_prev, p_next]
        p_prev = sorted_points[0]
        p_next = sorted_points[-1]

        for i in range(len(sorted_points) - 1):
            if sorted_points[i].offset_seconds <= t <= sorted_points[i + 1].offset_seconds:
                p_prev = sorted_points[i]
                p_next = sorted_points[i + 1]
                break

        # Step evaluation if interpolation is disabled or data type is discrete
        if not config.interpolate or data_type in (DataType.BOOLEAN, DataType.STRING):
            return MathSignalGenerator._cast_type(p_prev.value, data_type)

        # Continuous linear interpolation: y = y0 + α * (y1 - y0) where α = (t - t0) / dt
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
        """Parses a CSV string into a validated list of TimestampedPoints.

        Accepts two-column CSV formats (e.g., 'offset_seconds,value' or 'time,temperature').
        Automatically detects and skips header rows.

        Args:
            content: Raw CSV text string.

        Returns:
            List[TimestampedPoint]: Chronologically ordered list of parsed points.
        """
        points: List[TimestampedPoint] = []
        reader = csv.reader(io.StringIO(content.strip()))
        first_row = True
        
        for row in reader:
            if not row or len(row) < 2:
                continue
            if first_row:
                first_row = False
                # Detect and skip non-numeric header row
                try:
                    float(row[0])
                except ValueError:
                    continue

            try:
                offset_sec = float(row[0].strip())
                val_raw = row[1].strip()
                points.append(TimestampedPoint(offset_seconds=offset_sec, value=val_raw))
            except Exception:
                continue

        points.sort(key=lambda p: p.offset_seconds)
        return points
