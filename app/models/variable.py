"""
Variable and Metric Domain Models.

Defines schemas and enumerations for simulated physical variables, mathematical signals,
derived expressions, continuous energy integrators, points replay, and chaos injection modes.
"""

from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class VariableType(str, Enum):
    """Classification of an IoT metric.

    Attributes:
        TELEMETRY: Continuous time-series sensor measurement.
        ATTRIBUTE: Static property, operating mode, or bidirectional control switch.
    """
    TELEMETRY = "telemetry"
    ATTRIBUTE = "attribute"


class DataType(str, Enum):
    """Primitive data type representation for metric values.

    Attributes:
        FLOAT: Double-precision floating point number.
        INTEGER: Signed 64-bit integer.
        BOOLEAN: Boolean true/false flag.
        STRING: Text string or categorical state label.
    """
    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"


class SimMode(str, Enum):
    """Mathematical and algorithmic simulation modes.

    Attributes:
        SINE: Sinusoidal waveform signal.
        COSINE: Cosinusoidal waveform signal.
        TRIANGLE: Triangular periodic waveform signal.
        SQUARE: Square alternating binary/stepped signal.
        SAWTOOTH: Ramp sawtooth periodic signal.
        RAMP: Continuous linear upward or downward ramp.
        RANDOM_WALK: Stochastic bounded random walk (Brownian-like).
        GAUSSIAN: Normally distributed random noise around mean.
        CONSTANT: Fixed unchanging value.
        POINTS_TABLE: Recorded time-series replay with optional interpolation.
        DERIVED: Safe AST mathematical expression binding other variables.
        INTEGRATOR: Continuous trapezoidal time integration (e.g. Energy kWh = ∫ Power kW dt).
    """
    SINE = "sine"
    COSINE = "cosine"
    TRIANGLE = "triangle"
    SQUARE = "square"
    SAWTOOTH = "sawtooth"
    RAMP = "ramp"
    RANDOM_WALK = "random_walk"
    GAUSSIAN = "gaussian"
    CONSTANT = "constant"
    POINTS_TABLE = "points_table"
    DERIVED = "derived"
    INTEGRATOR = "integrator"


class DerivedConfig(BaseModel):
    """Configuration for physical dependency calculation using AST formula.

    Attributes:
        formula: Mathematical formula referencing sibling variable IDs
            (e.g., '(debit_m3h * delta_t * 1.163)').
    """
    formula: str = Field(default="", description="Mathematical expression using variable IDs")


class IntegratorConfig(BaseModel):
    """Configuration for continuous Riemann/trapezoidal time integration.

    Used for energy accumulators, total flow volume, and cumulative production meters.

    Attributes:
        source_variable_id: Identifier of the rate variable to integrate (e.g., 'puissance_kw').
        time_unit: Base time unit denominator ('second', 'minute', 'hour').
        multiplier: Scaling factor (e.g., 0.001 to convert kW*h into MWh).
        initial_value: Starting accumulator index value.
    """
    source_variable_id: str = Field(default="", description="ID of the rate metric to integrate")
    time_unit: str = Field(default="hour", description="Time unit denominator ('second', 'minute', 'hour')")
    multiplier: float = Field(default=1.0, description="Scale factor applied to integral result")
    initial_value: float = Field(default=0.0, description="Initial accumulator counter index")


class MathConfig(BaseModel):
    """Configuration parameters for deterministic mathematical signal generators.

    Attributes:
        min_val: Lower boundary or baseline minimum value.
        max_val: Upper boundary or baseline maximum value.
        period: Period duration of one full cycle in seconds.
        offset: Vertical offset or constant setpoint baseline.
        noise_percent: Percentage of amplitude added as Gaussian random noise.
        step: Maximum step increment for ramp or random walk algorithms.
        constant_val: Static value used when simulation mode is CONSTANT.
    """
    min_val: float = Field(default=0.0, description="Minimum signal boundary")
    max_val: float = Field(default=100.0, description="Maximum signal boundary")
    period: float = Field(default=60.0, description="Cycle period in seconds")
    offset: float = Field(default=0.0, description="Vertical setpoint offset")
    noise_percent: float = Field(default=0.0, description="Superimposed random noise in % of amplitude")
    step: float = Field(default=1.0, description="Step increment for ramp or random walk")
    constant_val: Union[float, int, bool, str] = Field(default=0.0, description="Value used in constant mode")


class TimestampedPoint(BaseModel):
    """Single discrete point in a time-series replay profile.

    Attributes:
        offset_seconds: Relative elapsed time offset in seconds within the replay sequence.
        value: Metric value recorded at this specific timestamp offset.
    """
    offset_seconds: float = Field(..., description="Relative time offset in seconds")
    value: Union[float, int, bool, str] = Field(..., description="Recorded metric value")


class PointsTableConfig(BaseModel):
    """Configuration for replaying discrete time-series points sequences.

    Attributes:
        points: Chronologically ordered list of timestamped points.
        loop: Whether to loop back to the start when reaching sequence end.
        playback_speed: Playback time multiplier (e.g., 2.0 plays twice as fast).
        interpolate: Flag enabling linear interpolation between consecutive points.
    """
    points: List[TimestampedPoint] = Field(default_factory=list, description="Ordered time-series points")
    loop: bool = Field(default=True, description="Loop the sequence indefinitely")
    playback_speed: float = Field(default=1.0, description="Playback speed multiplier")
    interpolate: bool = Field(default=True, description="Enable linear interpolation between points")


class AnomalyType(str, Enum):
    """Fault and chaos injection types for demonstration and alarm validation.

    Attributes:
        NONE: Normal operation, no anomaly injected.
        SPIKE: Single sharp abnormal measurement excursion.
        DRIFT: Progressive linear bias deviation over time.
        FREEZE: Sensor value frozen at its current value without variation.
        TIMEOUT: Silent omission, publication stops simulating hardware connection loss.
    """
    NONE = "none"
    SPIKE = "spike"
    DRIFT = "drift"
    FREEZE = "freeze"
    TIMEOUT = "timeout"


class VariableConfig(BaseModel):
    """Comprehensive configuration schema for a simulated IoT variable.

    Represents all metadata, mathematical rules, operational states,
    manual overrides, and fault injection properties of a single metric.

    Attributes:
        id: Unique identifier key of the variable (e.g., 'temperature_cuve').
        name: Human-friendly descriptive label (e.g., 'Température Cuve').
        device_id: ID of the parent device owning this metric.
        var_type: Metric nature ('telemetry' or 'attribute').
        data_type: Value primitive type ('float', 'integer', 'boolean', 'string').
        unit: Physical unit symbol (e.g., '°C', 'bar', 'kW', 'rpm').
        topic: Custom MQTT destination topic (defaults to platform convention if empty).
        publish_interval: Individual emission interval in seconds.
        sim_mode: Active mathematical generation or dependency mode.
        math_config: Parameters for mathematical wave generation.
        points_config: Parameters for time-series point replay.
        derived_config: AST formula settings for derived calculations.
        integrator_config: Time accumulation settings for integral meters.
        enabled: Operational flag indicating whether variable is updated and broadcast.
        manual_override: Flag indicating whether operator manually locked value.
        manual_value: Operator-forced value when manual override is active.
        anomaly: Active fault injection mode.
        anomaly_magnitude: Amplitude or bias offset for injected anomaly.
        current_value: Last evaluated metric value stored dynamically in memory.
        last_published: Epoch timestamp of the most recent emission.
    """
    id: str = Field(..., description="Unique variable key")
    name: str = Field(..., description="Human-readable variable label")
    device_id: str = Field(..., description="ID of the owning device")
    var_type: VariableType = Field(default=VariableType.TELEMETRY, description="Telemetry or attribute")
    data_type: DataType = Field(default=DataType.FLOAT, description="Primitive data type")
    unit: str = Field(default="", description="Physical unit symbol (e.g., °C, bar)")
    topic: str = Field(default="", description="Target MQTT topic (defaults to platform standard if empty)")
    publish_interval: float = Field(default=5.0, description="Broadcast cadence in seconds")
    sim_mode: SimMode = Field(default=SimMode.SINE, description="Simulation mode")
    math_config: MathConfig = Field(default_factory=MathConfig)
    points_config: PointsTableConfig = Field(default_factory=PointsTableConfig)
    derived_config: DerivedConfig = Field(default_factory=DerivedConfig)
    integrator_config: IntegratorConfig = Field(default_factory=IntegratorConfig)
    enabled: bool = Field(default=True, description="Whether variable is active")
    
    # Manual control and override properties
    manual_override: bool = Field(default=False, description="Manual override active flag")
    manual_value: Optional[Union[float, int, bool, str]] = Field(default=None, description="Operator-forced value")
    
    # Fault injection properties (ThingsBoard demo scenarios)
    anomaly: AnomalyType = Field(default=AnomalyType.NONE, description="Injected fault mode")
    anomaly_magnitude: float = Field(default=50.0, description="Anomaly excursion magnitude")

    # Dynamic runtime tracking
    current_value: Optional[Any] = Field(default=None, description="Most recent evaluated value")
    last_published: Optional[float] = Field(default=None, description="Timestamp of last broadcast")
