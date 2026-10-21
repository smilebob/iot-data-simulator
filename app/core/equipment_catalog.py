"""
Catalogue des équipements métiers et modèles pré-configurés pour l'IoT Simulator.
Couvre les 4 grands domaines sectoriels :
- Industrie & Automatismes
- Tertiaire & Bâtiment Intelligent (Smart Building / GTB)
- Infrastructures, Réseaux d'Énergie & Mobilité
- Villes Durables, Collectivités & Télécoms
"""

from typing import Dict, List, Optional, Tuple
import secrets
from pydantic import BaseModel, Field
from app.models.device import DeviceConfig, PlatformType, TransportProtocol
from app.models.variable import (
    VariableConfig,
    VariableType,
    DataType,
    SimMode,
    MathConfig,
    PointsTableConfig,
    TimestampedPoint,
)
from app.platforms import get_adapter

class EquipmentPreset(BaseModel):
    id: str = Field(..., description="Identifiant unique du modèle")
    category: str = Field(..., description="Code secteur : industry, building, infrastructure, smart_city")
    category_label: str = Field(..., description="Libellé du secteur")
    name: str = Field(..., description="Nom de l'équipement")
    description: str = Field(..., description="Description technique et cas d'usage")
    icon: str = Field(default="fa-microchip", description="Icône FontAwesome")
    default_protocol: TransportProtocol = Field(default=TransportProtocol.MQTT)
    default_platform: PlatformType = Field(default=PlatformType.THINGSBOARD)
    variables: List[VariableConfig] = Field(default_factory=list)

def get_equipment_catalog() -> List[EquipmentPreset]:
    """Retourne la liste complète des modèles d'équipements pré-configurés."""
    catalog: List[EquipmentPreset] = []

    # =========================================================================
    # 1. INDUSTRIE & AUTOMATISMES
    # =========================================================================
    cat_ind = "industry"
    cat_ind_label = "Industrie & Automatismes"

    # 1.1 Centrale d'Air Comprimé / Compresseur
    catalog.append(EquipmentPreset(
        id="ind_compressor",
        category=cat_ind,
        category_label=cat_ind_label,
        name="Centrale d'Air Comprimé",
        description="Surveillance de pression cuve, température vis d'huile, débit et puissance active pour maintenance prédictive.",
        icon="gauge",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="pression_reseau",
                name="Pression Réseau",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="bar",
                publish_interval=2.0,
                sim_mode=SimMode.SAWTOOTH,
                math_config=MathConfig(min_val=6.2, max_val=8.5, period=45.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="temp_vis_huile",
                name="Température Huile / Vis",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=68.0, max_val=82.0, period=120.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="debit_air",
                name="Débit Massique",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="Nm³/h",
                publish_interval=3.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=120.0, max_val=450.0, step=15.0, noise_percent=5.0),
            ),
            VariableConfig(
                id="puissance_active",
                name="Puissance Électrique Active",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=22.0, max_val=75.0, period=60.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="etat_marche",
                name="État de Fonctionnement",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=True),
            ),
        ]
    ))

    # 1.2 Broche d'Usinage & Moteur Vibrant
    catalog.append(EquipmentPreset(
        id="ind_spindle",
        category=cat_ind,
        category_label=cat_ind_label,
        name="Broche d'Usinage & Moteur",
        description="Mesure vibratoire RMS et thermique pour la détection précoce d'usure des roulements.",
        icon="cog",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="vitesse_rotation",
                name="Vitesse de Rotation",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="rpm",
                publish_interval=1.0,
                sim_mode=SimMode.POINTS_TABLE,
                points_config=PointsTableConfig(
                    points=[
                        TimestampedPoint(offset_seconds=0.0, value=0),
                        TimestampedPoint(offset_seconds=5.0, value=1500),
                        TimestampedPoint(offset_seconds=20.0, value=3000),
                        TimestampedPoint(offset_seconds=40.0, value=3000),
                        TimestampedPoint(offset_seconds=50.0, value=1200),
                        TimestampedPoint(offset_seconds=60.0, value=0),
                    ],
                    loop=True,
                    interpolate=True,
                ),
            ),
            VariableConfig(
                id="vibration_rms",
                name="Vibration Globale RMS",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="mm/s",
                publish_interval=1.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=1.2, max_val=4.8, offset=2.5, noise_percent=8.0),
            ),
            VariableConfig(
                id="temp_palier",
                name="Température Palier Roulement",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=42.0, max_val=65.0, period=90.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="courant_moteur",
                name="Courant Phase Moteur",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="A",
                publish_interval=1.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=8.0, max_val=28.0, period=45.0, noise_percent=4.0),
            ),
        ]
    ))

    # 1.3 Groupe Froid Industriel (Chiller)
    catalog.append(EquipmentPreset(
        id="ind_chiller",
        category=cat_ind,
        category_label=cat_ind_label,
        name="Groupe Froid Industriel",
        description="Surveillance du cycle thermodynamique, COP frigorifique, pressions HP/BP et régulation eau glacée.",
        icon="snowflake",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="temp_eau_depart",
                name="Température Eau Glacée Départ",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=6.5, max_val=8.2, period=60.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="temp_eau_retour",
                name="Température Eau Glacée Retour",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=11.0, max_val=14.0, period=60.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="pression_hp",
                name="Pression Haute Pression (HP)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="bar",
                publish_interval=2.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=14.0, max_val=18.5, period=40.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="cop_instantane",
                name="Coefficient de Performance (COP)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="",
                publish_interval=5.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=3.2, max_val=4.6, offset=3.9, noise_percent=3.0),
            ),
        ]
    ))

    # 1.4 Ligne de Convoyage & Transitique
    catalog.append(EquipmentPreset(
        id="ind_conveyor",
        category=cat_ind,
        category_label=cat_ind_label,
        name="Ligne de Convoyage & Robotique",
        description="Suivi de cadence de production, débit de pièces, vitesse de tapis et indicateurs TRS/OEE.",
        icon="git-branch",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="cadence_pieces",
                name="Cadence Instantanée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="pièces/min",
                publish_interval=2.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=30.0, max_val=85.0, period=50.0, noise_percent=5.0),
            ),
            VariableConfig(
                id="vitesse_bande",
                name="Vitesse Tapis Roulant",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m/s",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=0.4, max_val=1.2, period=30.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="taux_rendement_trs",
                name="Taux de Rendement Synthétique (TRS)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=10.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=78.0, max_val=95.0, offset=88.0, noise_percent=3.0),
            ),
        ]
    ))

    # =========================================================================
    # 2. TERTIAIRE & BÂTIMENT INTELLIGENT (SMART BUILDING / GTB)
    # =========================================================================
    cat_bldg = "building"
    cat_bldg_label = "Tertiaire & Smart Building"

    # 2.1 Centrale de Traitement d'Air (CTA HVAC)
    catalog.append(EquipmentPreset(
        id="bldg_cta",
        category=cat_bldg,
        category_label=cat_bldg_label,
        name="Centrale Traitement d'Air (CTA)",
        description="Gestion du confort aéraulique, température soufflage/reprise, débit et encrassement filtres.",
        icon="fan",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="temp_soufflage",
                name="Température Soufflage",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=4.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=19.5, max_val=22.5, period=80.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="temp_reprise",
                name="Température Reprise",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=4.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=21.0, max_val=24.0, period=80.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="debit_soufflage",
                name="Débit d'Air Soufflé",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m³/h",
                publish_interval=5.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=1500.0, max_val=4200.0, step=80.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="pression_filtre",
                name="Delta Pression Filtre",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="Pa",
                publish_interval=5.0,
                sim_mode=SimMode.RAMP,
                math_config=MathConfig(min_val=120.0, max_val=280.0, period=240.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="registre_air_neuf",
                name="Ouverture Registre Air Neuf",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.INTEGER,
                unit="%",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=35),
            ),
        ]
    ))

    # 2.2 TGBT & Compteur Multi-Fluides
    catalog.append(EquipmentPreset(
        id="bldg_tgbt",
        category=cat_bldg,
        category_label=cat_bldg_label,
        name="TGBT & Compteur Multi-Fluides",
        description="Supervision électrique globale : puissance active, cos phi, tension, index kWh et débit eau.",
        icon="zap",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="puissance_totale_kw",
                name="Puissance Active Triphasée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=45.0, max_val=180.0, period=60.0, noise_percent=4.0),
            ),
            VariableConfig(
                id="facteur_puissance",
                name="Facteur de Puissance (Cos Phi)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="",
                publish_interval=3.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=0.88, max_val=0.98, offset=0.94, noise_percent=1.0),
            ),
            VariableConfig(
                id="tension_l1_l2",
                name="Tension Phase-Neutre L1",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="V",
                publish_interval=2.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=228.0, max_val=234.0, offset=231.0, noise_percent=0.5),
            ),
            VariableConfig(
                id="debit_eau_general",
                name="Débit Eau Générale",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m³/h",
                publish_interval=5.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=0.2, max_val=3.8, step=0.2, noise_percent=3.0),
            ),
        ]
    ))

    # 2.3 Station Qualité d'Air Intérieur (QAI)
    catalog.append(EquipmentPreset(
        id="bldg_qai",
        category=cat_bldg,
        category_label=cat_bldg_label,
        name="Station Qualité d'Air (QAI)",
        description="Surveillance environnementale intérieure et santé : CO2, COV, PM2.5, température et humidité relative.",
        icon="wind",
        default_protocol=TransportProtocol.COAP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="taux_co2",
                name="Concentration CO₂",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="ppm",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=450.0, max_val=1350.0, period=180.0, noise_percent=4.0),
            ),
            VariableConfig(
                id="particules_pm25",
                name="Particules Fines PM2.5",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="µg/m³",
                publish_interval=5.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=4.0, max_val=28.0, offset=12.0, noise_percent=8.0),
            ),
            VariableConfig(
                id="cov_totaux",
                name="Composés Organiques Volatils (COV)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="ppb",
                publish_interval=5.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=80.0, max_val=450.0, step=15.0, noise_percent=5.0),
            ),
            VariableConfig(
                id="temp_ambiante",
                name="Température Ambiante",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=20.0, max_val=23.5, period=120.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="humidite_ambiante",
                name="Humidité Relative",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=42.0, max_val=62.0, period=150.0, noise_percent=2.0),
            ),
        ]
    ))

    # 2.4 Pompe à Chaleur Réversible (PAC)
    catalog.append(EquipmentPreset(
        id="bldg_heatpump",
        category=cat_bldg,
        category_label=cat_bldg_label,
        name="Pompe à Chaleur Réversible (PAC)",
        description="Gestion du chauffage/climatisation tertiaire, températures d'échange, pression circuit et régime.",
        icon="flame",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="temp_depart_eau",
                name="Température Eau Départ PAC",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=4.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=42.0, max_val=48.0, period=70.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="puissance_thermique_kw",
                name="Puissance Thermique Fournie",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=15.0, max_val=55.0, period=90.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="pression_circuit",
                name="Pression Circuit Primaire",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="bar",
                publish_interval=5.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=1.8, max_val=2.3, offset=2.05, noise_percent=1.0),
            ),
            VariableConfig(
                id="mode_chaud",
                name="Mode Fonctionnement Chaud",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=60.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=True),
            ),
        ]
    ))

    # =========================================================================
    # 3. INFRASTRUCTURES, RÉSEAUX D'ÉNERGIE & MOBILITÉ
    # =========================================================================
    cat_infra = "infrastructure"
    cat_infra_label = "Infrastructures & Énergie"

    # 3.1 Poste Source & Transformateur HTA/BT
    catalog.append(EquipmentPreset(
        id="infra_transfo_hta",
        category=cat_infra,
        category_label=cat_infra_label,
        name="Transformateur HTA/BT",
        description="Surveillance thermique du diélectrique, pression de cuve, harmonique THD et protection DGPT2.",
        icon="radio",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="temp_huile_transfo",
                name="Température Huile Diélectrique",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=52.0, max_val=74.0, period=160.0, noise_percent=1.2),
            ),
            VariableConfig(
                id="charge_transfo_pct",
                name="Taux de Charge Transformateur",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=3.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=35.0, max_val=88.0, period=60.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="pression_cuve",
                name="Pression Interne Cuve",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="mbar",
                publish_interval=5.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=140.0, max_val=220.0, offset=180.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="taux_thd",
                name="Taux Harmonique THD-I",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=3.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=2.1, max_val=6.4, offset=3.8, noise_percent=4.0),
            ),
            VariableConfig(
                id="alarme_dgpt2",
                name="Alerte Sécurité DGPT2",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=60.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
        ]
    ))

    # 3.2 Centrale Solaire & Onduleur Photovoltaïque
    catalog.append(EquipmentPreset(
        id="infra_solar_pv",
        category=cat_infra,
        category_label=cat_infra_label,
        name="Onduleur Solaire Photovoltaïque",
        description="Production d'énergie renouvelable, injection réseau, tension/courant DC string et ensoleillement.",
        icon="sun",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="puissance_injection_kw",
                name="Puissance AC Injectée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=0.0, max_val=125.0, period=90.0, noise_percent=4.0),
            ),
            VariableConfig(
                id="ensoleillement",
                name="Irradiation Pyranomètre",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="W/m²",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=50.0, max_val=980.0, period=90.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="tension_dc_string",
                name="Tension DC Chaîne PV",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="V",
                publish_interval=2.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=580.0, max_val=740.0, offset=660.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="rendement_onduleur",
                name="Rendement de Conversion",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=5.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=96.5, max_val=98.8, offset=97.9, noise_percent=0.4),
            ),
        ]
    ))

    # 3.3 Borne de Recharge IRVE (Véhicules Électriques)
    catalog.append(EquipmentPreset(
        id="infra_irve_charger",
        category=cat_infra,
        category_label=cat_infra_label,
        name="Borne de Recharge IRVE",
        description="Surveillance de session de recharge accélérée/rapide (kW délivrés, kWh cumulés, statut prise).",
        icon="battery-charging",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="puissance_charge_kw",
                name="Puissance de Charge Délivrée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=2.0,
                sim_mode=SimMode.POINTS_TABLE,
                points_config=PointsTableConfig(
                    points=[
                        TimestampedPoint(offset_seconds=0.0, value=0.0),
                        TimestampedPoint(offset_seconds=5.0, value=7.4),
                        TimestampedPoint(offset_seconds=15.0, value=22.0),
                        TimestampedPoint(offset_seconds=45.0, value=22.0),
                        TimestampedPoint(offset_seconds=55.0, value=11.0),
                        TimestampedPoint(offset_seconds=60.0, value=2.0),
                    ],
                    loop=True,
                    interpolate=True,
                ),
            ),
            VariableConfig(
                id="energie_session_kwh",
                name="Énergie Consommée Session",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kWh",
                publish_interval=4.0,
                sim_mode=SimMode.RAMP,
                math_config=MathConfig(min_val=0.0, max_val=42.0, period=120.0, noise_percent=0.5),
            ),
            VariableConfig(
                id="courant_charge_a",
                name="Courant Délivré Prise",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="A",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=0.0, max_val=32.0, period=60.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="statut_connecteur",
                name="Statut Prise Type 2",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.STRING,
                unit="",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val="CHARGING"),
            ),
        ]
    ))

    # 3.4 Poste de Relevage Eau & Assainissement
    catalog.append(EquipmentPreset(
        id="infra_water_pump",
        category=cat_infra,
        category_label=cat_infra_label,
        name="Poste de Relevage Assainissement",
        description="Gestion des eaux usées et pluviales : niveau de bâche, débit refoulé, alternance des pompes.",
        icon="droplets",
        default_protocol=TransportProtocol.COAP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="niveau_bache_m",
                name="Niveau d'Eau en Bâche",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m",
                publish_interval=3.0,
                sim_mode=SimMode.SAWTOOTH,
                math_config=MathConfig(min_val=0.6, max_val=3.4, period=60.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="debit_refoulement",
                name="Débit Pompe de Refoulement",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m³/h",
                publish_interval=3.0,
                sim_mode=SimMode.SQUARE,
                math_config=MathConfig(min_val=0.0, max_val=85.0, period=60.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="conso_pompe_kw",
                name="Puissance Électrique Pompe",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=3.0,
                sim_mode=SimMode.SQUARE,
                math_config=MathConfig(min_val=0.0, max_val=18.5, period=60.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="alarme_debordement",
                name="Alerte Trop-Plein / Débordement",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=60.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
        ]
    ))

    # =========================================================================
    # 4. VILLES DURABLES, COLLECTIVITÉS & RÉSEAUX TÉLÉCOMS
    # =========================================================================
    cat_city = "smart_city"
    cat_city_label = "Villes Durables & Télécoms"

    # 4.1 Armoire Éclairage Public Connecté
    catalog.append(EquipmentPreset(
        id="city_lighting",
        category=cat_city,
        category_label=cat_city_label,
        name="Armoire d'Éclairage Public",
        description="Télégestion d'armoire urbaine, gradation nocturne, comptage et détection de défauts d'isolement.",
        icon="lightbulb",
        default_protocol=TransportProtocol.COAP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="puissance_eclairage_kw",
                name="Puissance Circuit Éclairage",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=2.5, max_val=14.0, period=90.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="niveau_gradation_pct",
                name="Niveau Gradation (Abaissement)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="%",
                publish_interval=10.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=30.0, max_val=100.0, period=90.0, noise_percent=0.0),
            ),
            VariableConfig(
                id="courant_fuite_ma",
                name="Courant de Fuite Différentiel",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="mA",
                publish_interval=5.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=12.0, max_val=48.0, offset=22.0, noise_percent=6.0),
            ),
            VariableConfig(
                id="alerte_porte_ouverte",
                name="Contact d'Ouverture Porte",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=60.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
        ]
    ))

    # 4.2 Station Météo Urbaine & Îlot de Chaleur
    catalog.append(EquipmentPreset(
        id="city_weather",
        category=cat_city,
        category_label=cat_city_label,
        name="Station Météo & Climat Urbain",
        description="Surveillance micro-climatique : température, vent, hygrométrie et analyse des îlots de chaleur.",
        icon="cloud-sun",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="temp_ext",
                name="Température sous Abri",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=14.0, max_val=29.0, period=140.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="vitesse_vent_kmh",
                name="Vitesse du Vent",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="km/h",
                publish_interval=3.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=5.0, max_val=45.0, offset=18.0, noise_percent=12.0),
            ),
            VariableConfig(
                id="humidite_ext",
                name="Hygrométrie Extérieure",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=35.0, max_val=80.0, period=140.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="indice_uv",
                name="Indice Rayonnement UV",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=0.0, max_val=8.5, period=140.0, noise_percent=2.0),
            ),
        ]
    ))

    # 4.3 Shelter Télécoms & Salle Serveurs
    catalog.append(EquipmentPreset(
        id="telecom_shelter",
        category=cat_city,
        category_label=cat_city_label,
        name="Shelter Télécoms / Nœud Fibre",
        description="Surveillance d'infrastructure critique : autonomie onduleur UPS, climatisation et détection fuite.",
        icon="server",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="charge_onduleur_pct",
                name="Charge Onduleur ASI/UPS",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=3.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=48.0, max_val=62.0, offset=54.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="autonomie_batterie_min",
                name="Autonomie Batterie Restante",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="min",
                publish_interval=10.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=75.0, max_val=85.0, offset=82.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="temp_baie_serveur",
                name="Température Couloir Chaud",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=4.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=24.5, max_val=29.0, period=60.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="detection_inondation",
                name="Capteur Présence Eau / Fuite",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
        ]
    ))

    # 4.4 Comptage Trafic & Mobilités Douces
    catalog.append(EquipmentPreset(
        id="city_traffic",
        category=cat_city,
        category_label=cat_city_label,
        name="Comptage Trafic & Mobilités",
        description="Analyse des flux urbains : passage véhicules légers, comptage vélos/trottinettes et vitesse moyenne.",
        icon="car",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="debit_vehicules",
                name="Débit Véhicules Légers",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="véh/h",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=120.0, max_val=950.0, period=100.0, noise_percent=5.0),
            ),
            VariableConfig(
                id="debit_cyclistes",
                name="Passage Vélos & Mobilités Douces",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="vélos/h",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=15.0, max_val=180.0, period=80.0, noise_percent=8.0),
            ),
            VariableConfig(
                id="vitesse_moyenne_kmh",
                name="Vitesse Moyenne Mesurée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="km/h",
                publish_interval=3.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=32.0, max_val=48.0, offset=41.0, noise_percent=4.0),
            ),
            VariableConfig(
                id="alerte_congestion",
                name="Seuil de Congestion Dépassé",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
        ]
    ))

    return catalog

class InstantiatePresetRequest(BaseModel):
    preset_id: str = Field(..., description="Identifiant du preset choisi")
    device_id: Optional[str] = Field(default=None, description="Identifiant unique pour l'équipement créé")
    name: Optional[str] = Field(default=None, description="Nom d'affichage de l'équipement")
    token: Optional[str] = Field(default=None, description="Token d'authentification Thingsboard")
    protocol: Optional[TransportProtocol] = Field(default=None, description="Protocole (MQTT, HTTP, CoAP)")
    custom_host: Optional[str] = Field(default=None, description="Hôte spécifique")
    custom_port: Optional[int] = Field(default=None, description="Port spécifique")
    use_tls: Optional[bool] = Field(default=None, description="Chiffrement TLS")

def instantiate_preset(
    req: InstantiatePresetRequest,
    repo,
) -> Tuple[DeviceConfig, List[VariableConfig]]:
    """
    Instancie un modèle d'équipement et crée automatiquement toutes ses variables associées.
    """
    catalog = get_equipment_catalog()
    preset = next((p for p in catalog if p.id == req.preset_id), None)
    if not preset:
        raise ValueError(f"Modèle d'équipement '{req.preset_id}' introuvable dans le catalogue.")

    existing_devices = {d.id for d in repo.get_devices()}

    # Génération d'un ID unique si non spécifié
    device_id = (req.device_id or "").strip()
    if not device_id:
        suffix = secrets.token_hex(2)
        device_id = f"{preset.id}_{suffix}"
        while device_id in existing_devices:
            suffix = secrets.token_hex(2)
            device_id = f"{preset.id}_{suffix}"

    # Détermination du nom lisible
    device_name = (req.name or "").strip()
    if not device_name:
        count = sum(1 for d in repo.get_devices() if d.id.startswith(preset.id))
        device_name = f"{preset.name} #{count + 1}" if count > 0 else preset.name

    # Création et sauvegarde de l'équipement
    device = DeviceConfig(
        id=device_id,
        name=device_name,
        platform=preset.default_platform,
        token=req.token.strip() if req.token and req.token.strip() else None,
        protocol=req.protocol or preset.default_protocol,
        custom_host=req.custom_host.strip() if req.custom_host and req.custom_host.strip() else None,
        custom_port=req.custom_port,
        use_tls=req.use_tls,
        enabled=True,
    )
    repo.save_device(device)

    # Création des variables associées avec topic par défaut
    adapter = get_adapter(device.platform)
    created_variables: List[VariableConfig] = []
    for orig_var in preset.variables:
        var = orig_var.model_copy(deep=True)
        var.device_id = device.id
        var.id = f"{device.id}_{orig_var.id}"
        if not var.topic:
            var.topic = adapter.get_default_topic(device, var)
        repo.save_variable(var)
        created_variables.append(var)

    return device, created_variables

