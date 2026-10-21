from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field

class VariableType(str, Enum):
    TELEMETRY = "telemetry"   # Mesure / Grandeur continue
    ATTRIBUTE = "attribute"   # Propriété, état ou paramètre de contrôle

class DataType(str, Enum):
    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"

class SimMode(str, Enum):
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
    DERIVED = "derived"          # Formule physique liant d'autres grandeurs
    INTEGRATOR = "integrator"    # Intégrateur temporel continu (ex: kWh = ∫ kW dt)

class DerivedConfig(BaseModel):
    formula: str = Field(default="", description="Expression mathématique (ex: 'debit_m3h * delta_t_c * 1.163')")

class IntegratorConfig(BaseModel):
    source_variable_id: str = Field(default="", description="ID de la variable source à intégrer (ex: 'puissance_kw')")
    time_unit: str = Field(default="hour", description="Unité de temps ('second', 'minute', 'hour')")
    multiplier: float = Field(default=1.0, description="Facteur d'échelle (ex: 0.001 pour kW vers MWh)")
    initial_value: float = Field(default=0.0, description="Valeur initiale de l'index cumulé")

class MathConfig(BaseModel):
    min_val: float = Field(default=0.0, description="Valeur minimale")
    max_val: float = Field(default=100.0, description="Valeur maximale")
    period: float = Field(default=60.0, description="Période du cycle en secondes")
    offset: float = Field(default=0.0, description="Décalage vertical / consigne")
    noise_percent: float = Field(default=0.0, description="Bruit aléatoire superposé (en % d'amplitude)")
    step: float = Field(default=1.0, description="Pas d'incrément (pour rampe / marche aléatoire)")
    constant_val: Union[float, int, bool, str] = Field(default=0.0, description="Valeur si mode constant")

class TimestampedPoint(BaseModel):
    offset_seconds: float = Field(..., description="Position temporelle relative en secondes dans le cycle")
    value: Union[float, int, bool, str] = Field(..., description="Valeur du point")

class PointsTableConfig(BaseModel):
    points: List[TimestampedPoint] = Field(default_factory=list, description="Liste ordonnée de points")
    loop: bool = Field(default=True, description="Répéter le cycle indéfiniment")
    playback_speed: float = Field(default=1.0, description="Multiplicateur de vitesse de lecture")
    interpolate: bool = Field(default=True, description="Interpolation linéaire entre les points consécutifs")

class AnomalyType(str, Enum):
    NONE = "none"
    SPIKE = "spike"         # Pic ponctuel anormal
    DRIFT = "drift"         # Dérive continue
    FREEZE = "freeze"       # Valeur gelée
    TIMEOUT = "timeout"     # Silence radio (interruption de publication)

class VariableConfig(BaseModel):
    id: str = Field(..., description="Identifiant unique de la variable (clé)")
    name: str = Field(..., description="Nom lisible de la grandeur")
    device_id: str = Field(..., description="ID de l'équipement auquel appartient cette variable")
    var_type: VariableType = Field(default=VariableType.TELEMETRY, description="Type : telemetry ou attribute")
    data_type: DataType = Field(default=DataType.FLOAT, description="Type de donnée : float, integer, boolean, string")
    unit: str = Field(default="", description="Unité de mesure (ex: °C, %, bar, kW, rpm)")
    topic: str = Field(default="", description="Topic MQTT cible (laissé vide pour topic par défaut de la plateforme)")
    publish_interval: float = Field(default=5.0, description="Intervalle de publication en secondes")
    sim_mode: SimMode = Field(default=SimMode.SINE, description="Mode de simulation")
    math_config: MathConfig = Field(default_factory=MathConfig)
    points_config: PointsTableConfig = Field(default_factory=PointsTableConfig)
    derived_config: DerivedConfig = Field(default_factory=DerivedConfig)
    integrator_config: IntegratorConfig = Field(default_factory=IntegratorConfig)
    enabled: bool = Field(default=True, description="Variable active dans la boucle de simulation")
    
    # Contrôle manuel & forçage
    manual_override: bool = Field(default=False, description="Forcer la valeur manuellement")
    manual_value: Optional[Union[float, int, bool, str]] = Field(default=None, description="Valeur forcée manuellement")
    
    # Injection d'anomalie (Démos ThingsBoard)
    anomaly: AnomalyType = Field(default=AnomalyType.NONE, description="Anomalie injectée")
    anomaly_magnitude: float = Field(default=50.0, description="Amplitude du pic ou de la dérive")

    # État dynamique à l'exécution
    current_value: Optional[Any] = Field(default=None, description="Dernière valeur calculée")
    last_published: Optional[float] = Field(default=None, description="Horodatage du dernier envoi")
