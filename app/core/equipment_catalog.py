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

    # 1.5 Chambre Froide Négative & Chaîne du Froid
    catalog.append(EquipmentPreset(
        id="ind_cold_room",
        category=cat_ind,
        category_label=cat_ind_label,
        name="Chambre Froide Négative",
        description="Surveillance continue de la chaîne du froid (normes HACCP), température d'évaporateur et dégivrage.",
        icon="snowflake",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="temp_chambre_froide",
                name="Température Ambiante Négative",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=-22.0, max_val=-18.0, period=150.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="temp_evaporateur",
                name="Température Évaporateur",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=-28.0, max_val=-23.0, period=150.0, noise_percent=1.2),
            ),
            VariableConfig(
                id="puissance_groupe_kw",
                name="Puissance Groupe Frigorifique",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=3.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=3.5, max_val=12.0, period=80.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="porte_ouverte",
                name="Alerte Porte Ouverte",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
            VariableConfig(
                id="statut_degivrage",
                name="Cycle Dégivrage Actif",
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

    # 1.6 Chaudière Industrielle Vapeur & Cogénération
    catalog.append(EquipmentPreset(
        id="ind_steam_boiler",
        category=cat_ind,
        category_label=cat_ind_label,
        name="Chaudière Industrielle Vapeur",
        description="Production de vapeur haute pression pour utilités d'usines chimiques, agroalimentaires et process.",
        icon="flame",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="pression_vapeur_bar",
                name="Pression Vapeur Vive",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="bar",
                publish_interval=3.0,
                sim_mode=SimMode.SAWTOOTH,
                math_config=MathConfig(min_val=12.5, max_val=16.8, period=60.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="debit_vapeur_th",
                name="Débit Massique Vapeur",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="t/h",
                publish_interval=4.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=4.5, max_val=14.0, offset=9.5, noise_percent=3.0),
            ),
            VariableConfig(
                id="temp_fumees",
                name="Température des Fumées",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=145.0, max_val=185.0, period=120.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="rendement_combustion_pct",
                name="Rendement de Combustion",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=10.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=89.0, max_val=94.5, offset=92.5, noise_percent=0.5),
            ),
            VariableConfig(
                id="taux_o2_residuel",
                name="Teneur O₂ Résiduel",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=5.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=2.8, max_val=4.5, offset=3.4, noise_percent=2.0),
            ),
        ]
    ))

    # 1.7 Traitement d'Air Salle Blanche ISO 5-8
    catalog.append(EquipmentPreset(
        id="ind_cleanroom_cta",
        category=cat_ind,
        category_label=cat_ind_label,
        name="Salle Blanche & CTA Stérile (ISO)",
        description="Contrôle d'atmosphère contrôlée (pharma, microélectronique) : cascade de surpression, renouvellement et comptage particulaire.",
        icon="shield-alert",
        default_protocol=TransportProtocol.COAP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="surpression_salle_pa",
                name="Cascade Surpression Salle",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="Pa",
                publish_interval=2.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=22.0, max_val=35.0, offset=28.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="renouvellement_air_volh",
                name="Taux de Renouvellement",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="vol/h",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=18.0, max_val=24.0, period=90.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="comptage_particules_05",
                name="Particules ≥ 0.5 µm",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="part/m³",
                publish_interval=5.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=150.0, max_val=850.0, step=25.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="humidite_absolue_gkg",
                name="Humidité Absolue Précision",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="g/kg",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=6.2, max_val=8.5, period=120.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="alarme_depressurisation",
                name="Alerte Rupture Surpression",
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

    # 1.8 Four de Traitement Thermique Métallurgique
    catalog.append(EquipmentPreset(
        id="ind_thermal_furnace",
        category=cat_ind,
        category_label=cat_ind_label,
        name="Four de Traitement Thermique",
        description="Surveillance multi-zones de température haute intensité, rampe de chauffe et régulation brûleurs.",
        icon="thermometer-sun",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="temp_zone_1",
                name="Température Zone 1 (Préchauffe)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=780.0, max_val=850.0, period=100.0, noise_percent=0.8),
            ),
            VariableConfig(
                id="temp_zone_2",
                name="Température Zone 2 (Maintien)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=820.0, max_val=890.0, period=100.0, noise_percent=0.8),
            ),
            VariableConfig(
                id="temp_zone_3",
                name="Température Zone 3 (Homogénéisation)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=850.0, max_val=920.0, period=100.0, noise_percent=0.8),
            ),
            VariableConfig(
                id="debit_gaz_combustible",
                name="Débit Gaz Combustible",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="Nm³/h",
                publish_interval=4.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=25.0, max_val=75.0, period=80.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="puissance_bruleurs_pct",
                name="Modulation Puissance Brûleurs",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=40.0, max_val=95.0, period=60.0, noise_percent=2.5),
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

    # 2.5 Centrale Sécurité Incendie (SSI) & Désenfumage
    catalog.append(EquipmentPreset(
        id="bldg_fire_ssi",
        category=cat_bldg,
        category_label=cat_bldg_label,
        name="Centrale Sécurité Incendie (SSI)",
        description="Système de sécurité incendie ERP/IGH : opacité des fumées, clapets coupe-feu, déclencheurs et ventilateurs de désenfumage.",
        icon="bell-ring",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="opacite_fumee_obsm",
                name="Opacité Détection Fumée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="obs/m",
                publish_interval=2.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=0.01, max_val=0.08, offset=0.03, noise_percent=5.0),
            ),
            VariableConfig(
                id="debit_desenfumage_m3h",
                name="Débit Extracteur Désenfumage",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m³/h",
                publish_interval=5.0,
                sim_mode=SimMode.SQUARE,
                math_config=MathConfig(min_val=0.0, max_val=12000.0, period=120.0, noise_percent=0.0),
            ),
            VariableConfig(
                id="tension_alim_secours",
                name="Tension Alimentation Secourue (AES)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="V",
                publish_interval=10.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=26.8, max_val=27.5, offset=27.2, noise_percent=0.3),
            ),
            VariableConfig(
                id="declencheur_manuel",
                name="Déclencheur Manuel Enclenché",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
            VariableConfig(
                id="statut_clapets_coupe_feu",
                name="Statut Clapets Coupe-Feu",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.STRING,
                unit="",
                publish_interval=60.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val="ARMED_OPEN"),
            ),
        ]
    ))

    # 2.6 Gestion d'Éclairage DALI & Détection Présence
    catalog.append(EquipmentPreset(
        id="bldg_dali_lighting",
        category=cat_bldg,
        category_label=cat_bldg_label,
        name="Gestion d'Éclairage DALI & Présence",
        description="Efficacité énergétique BACS & Confort visuel : luxmètre asservi, détecteur de présence PIR et gradation DALI.",
        icon="lamp",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="eclairement_lux",
                name="Éclairement Mesuré Plan Travail",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="lux",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=220.0, max_val=580.0, period=90.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="taux_presence_zone_pct",
                name="Taux d'Occupation de Zone",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="%",
                publish_interval=5.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=0.0, max_val=100.0, period=75.0, noise_percent=0.0),
            ),
            VariableConfig(
                id="gradation_dali_pct",
                name="Gradation Sortie Ballast DALI",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="%",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=15.0, max_val=85.0, period=90.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="puissance_eclairage_w",
                name="Puissance Électrique Circuit",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="W",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=120.0, max_val=680.0, period=90.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="heures_fonctionnement_h",
                name="Heures d'Allumage Cumulées",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="h",
                publish_interval=30.0,
                sim_mode=SimMode.RAMP,
                math_config=MathConfig(min_val=1200.0, max_val=1250.0, period=300.0, noise_percent=0.0),
            ),
        ]
    ))

    # 2.7 Compteur d'Énergie Calorifique / Frigorifique
    catalog.append(EquipmentPreset(
        id="bldg_thermal_meter",
        category=cat_bldg,
        category_label=cat_bldg_label,
        name="Compteur d'Énergie Thermique (Calories)",
        description="Sous-comptage calorifique MID pour audits énergétiques et GTB : delta T, débit massique et cumul MWh.",
        icon="activity",
        default_protocol=TransportProtocol.COAP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="debit_volumique_m3h",
                name="Débit Volumique Fluide",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m³/h",
                publish_interval=4.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=1.2, max_val=8.5, step=0.3, noise_percent=2.0),
            ),
            VariableConfig(
                id="delta_t_deg",
                name="Écart Température Aller/Retour",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=4.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=5.0, max_val=18.0, period=80.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="puissance_thermique_kw",
                name="Puissance Thermique Instantanée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="kW",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=25.0, max_val=140.0, period=80.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="energie_cumulee_mwh",
                name="Énergie Calorifique Cumulée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="MWh",
                publish_interval=10.0,
                sim_mode=SimMode.RAMP,
                math_config=MathConfig(min_val=142.0, max_val=155.0, period=400.0, noise_percent=0.2),
            ),
            VariableConfig(
                id="temp_depart_eau",
                name="Température Départ Eau Chaude",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=4.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=65.0, max_val=78.0, period=100.0, noise_percent=0.8),
            ),
        ]
    ))

    # 2.8 Contrôle d'Accès & Hypervision Flux Bâtiment
    catalog.append(EquipmentPreset(
        id="bldg_access_flow",
        category=cat_bldg,
        category_label=cat_bldg_label,
        name="Contrôle d'Accès & Flux Bâtiment",
        description="Sécurité physique et jauges d'occupation : cadences tourniquets, tentatives refusées et statut d'issues de secours.",
        icon="users",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="flux_entrees_min",
                name="Cadence Entrées Visiteurs/Employés",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="pers/min",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=2.0, max_val=35.0, period=60.0, noise_percent=6.0),
            ),
            VariableConfig(
                id="flux_sorties_min",
                name="Cadence Sorties Tourniquets",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="pers/min",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=1.0, max_val=28.0, period=60.0, noise_percent=6.0),
            ),
            VariableConfig(
                id="jauge_occupation_pct",
                name="Jauge d'Occupation Globale Site",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="%",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=25.0, max_val=88.0, period=120.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="tentatives_refusees_h",
                name="Tentatives Accès Refusées",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="rejets/h",
                publish_interval=10.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=0.0, max_val=6.0, offset=1.0, noise_percent=10.0),
            ),
            VariableConfig(
                id="issues_secours_verrouillees",
                name="Issues de Secours Sous Contrôle",
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

    # 3.5 Éolienne / Aérogénérateur Mégawatt
    catalog.append(EquipmentPreset(
        id="infra_wind_turbine",
        category=cat_infra,
        category_label=cat_infra_label,
        name="Aérogénérateur / Éolienne MW",
        description="Parc éolien terrestre/offshore : vitesse du vent, rotation rotor, puissance injectée et orientation yaw.",
        icon="wind",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="vitesse_vent_ms",
                name="Vitesse Vent Anémomètre",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m/s",
                publish_interval=2.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=4.5, max_val=18.5, offset=9.8, noise_percent=6.0),
            ),
            VariableConfig(
                id="vitesse_rotor_rpm",
                name="Vitesse de Rotation Rotor",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="rpm",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=8.0, max_val=17.5, period=60.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="puissance_active_mw",
                name="Puissance Électrique Active",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="MW",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=0.4, max_val=2.8, period=60.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="angle_nacelle_yaw_deg",
                name="Orientation Nacelle (Yaw)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°",
                publish_interval=10.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=45.0, max_val=315.0, step=5.0, noise_percent=0.5),
            ),
            VariableConfig(
                id="temp_generatrice",
                name="Température Génératrice",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=55.0, max_val=82.0, period=140.0, noise_percent=1.0),
            ),
        ]
    ))

    # 3.6 Système de Stockage d'Énergie par Batteries (BESS)
    catalog.append(EquipmentPreset(
        id="infra_bess_storage",
        category=cat_infra,
        category_label=cat_infra_label,
        name="Système Stockage Batteries (BESS)",
        description="Conteneur de stockage stationnaire (stabilisation réseau, effacement de pointes) : SoC, SoH, tension pack et thermique cellules.",
        icon="battery-medium",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="soc_pct",
                name="État de Charge (SoC)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=5.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=20.0, max_val=95.0, period=200.0, noise_percent=0.5),
            ),
            VariableConfig(
                id="tension_pack_v",
                name="Tension Bus Continu DC",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="V",
                publish_interval=2.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=720.0, max_val=810.0, offset=765.0, noise_percent=0.8),
            ),
            VariableConfig(
                id="courant_charge_decharge_a",
                name="Courant Charge / Décharge",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="A",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=-120.0, max_val=120.0, period=90.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="temp_max_cellule",
                name="Température Cellule Critique",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=24.0, max_val=38.0, period=110.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="soh_pct",
                name="État de Santé Batterie (SoH)",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.FLOAT,
                unit="%",
                publish_interval=60.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=97.4),
            ),
        ]
    ))

    # 3.7 Signalisation & Aiguillage Ferroviaire
    catalog.append(EquipmentPreset(
        id="infra_rail_switch",
        category=cat_infra,
        category_label=cat_infra_label,
        name="Aiguillage & Signalisation Ferroviaire",
        description="Surveillance de moteur d'aiguille, courant d'effort, réchauffage de rail hivernal et présence essieu.",
        icon="train",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="courant_moteur_aiguille_a",
                name="Courant d'Effort Manœuvre",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="A",
                publish_interval=2.0,
                sim_mode=SimMode.SQUARE,
                math_config=MathConfig(min_val=0.0, max_val=8.2, period=45.0, noise_percent=4.0),
            ),
            VariableConfig(
                id="temps_manoeuvre_ms",
                name="Durée de Manœuvre Moteur",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="ms",
                publish_interval=10.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=2800.0, max_val=3400.0, offset=3100.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="temp_rail_rechauffage",
                name="Température Rail Détectée",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=2.0, max_val=14.0, period=120.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="presence_essieu",
                name="Pédale Détection Essieu",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=10.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
            VariableConfig(
                id="position_aiguille",
                name="Contrôle Position Verrouillée",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.STRING,
                unit="",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val="DIRECTE"),
            ),
        ]
    ))

    # 3.8 Station d'Épuration (STEP) - Bassin d'Aération
    catalog.append(EquipmentPreset(
        id="infra_water_treatment",
        category=cat_infra,
        category_label=cat_infra_label,
        name="Bassin d'Aération & Traitement STEP",
        description="Assainissement et traitement biologique : oxygène dissous O₂, potentiel redox, pH et insufflation surpresseurs.",
        icon="droplet",
        default_protocol=TransportProtocol.COAP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="oxygene_dissous_mgl",
                name="Taux Oxygène Dissous (O₂)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="mg/l",
                publish_interval=3.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=1.4, max_val=3.2, period=70.0, noise_percent=2.5),
            ),
            VariableConfig(
                id="potentiel_redox_mv",
                name="Potentiel d'Oxydoréduction (Redox)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="mV",
                publish_interval=4.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=-120.0, max_val=180.0, offset=45.0, noise_percent=4.0),
            ),
            VariableConfig(
                id="ph_eau",
                name="Acidité / Basicité pH",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="pH",
                publish_interval=4.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=6.8, max_val=7.6, offset=7.2, noise_percent=0.8),
            ),
            VariableConfig(
                id="turbidite_ntu",
                name="Indice Turbidité Eau",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="NTU",
                publish_interval=5.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=8.0, max_val=42.0, step=2.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="debit_insufflation_nm3h",
                name="Débit Air Surpresseurs",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="Nm³/h",
                publish_interval=3.0,
                sim_mode=SimMode.TRIANGLE,
                math_config=MathConfig(min_val=400.0, max_val=1200.0, period=60.0, noise_percent=2.0),
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

    # 4.5 Conteneur Déchets & Point d'Apport Volontaire (PAV)
    catalog.append(EquipmentPreset(
        id="city_waste_bin",
        category=cat_city,
        category_label=cat_city_label,
        name="Conteneur Déchets & PAV Connecté",
        description="Optimisation des tournées de collecte des déchets : niveau ultrason, sonde thermique anti-incendie et basculement.",
        icon="trash-2",
        default_protocol=TransportProtocol.COAP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="taux_remplissage_pct",
                name="Taux Remplissage Cuve",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="%",
                publish_interval=10.0,
                sim_mode=SimMode.RAMP,
                math_config=MathConfig(min_val=15.0, max_val=98.0, period=300.0, noise_percent=0.5),
            ),
            VariableConfig(
                id="temp_interne_cuve",
                name="Température Interne Cuve",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=10.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=12.0, max_val=28.0, period=120.0, noise_percent=1.0),
            ),
            VariableConfig(
                id="batterie_autonomie_pct",
                name="Niveau Batterie Capteur",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.INTEGER,
                unit="%",
                publish_interval=60.0,
                sim_mode=SimMode.RAMP,
                math_config=MathConfig(min_val=70.0, max_val=99.0, period=600.0, noise_percent=0.0),
            ),
            VariableConfig(
                id="alerte_incendie",
                name="Détection Fumée / Feu Bac",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=30.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
            VariableConfig(
                id="alerte_basculement",
                name="Capteur Choc / Basculement",
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

    # 4.6 Réseau d'Arrosage Intelligent & Espaces Verts
    catalog.append(EquipmentPreset(
        id="city_smart_irrigation",
        category=cat_city,
        category_label=cat_city_label,
        name="Arrosage Intelligent Espaces Verts",
        description="Gestion raisonnée de la ressource en eau : tensiométrie du sol, température à -10cm, débitmètre et vanne asservie.",
        icon="sprout",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="tension_matricielle_sol_cbar",
                name="Tension Hydrique Sol (Tensiomètre)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="cbar",
                publish_interval=5.0,
                sim_mode=SimMode.SAWTOOTH,
                math_config=MathConfig(min_val=15.0, max_val=65.0, period=120.0, noise_percent=2.0),
            ),
            VariableConfig(
                id="temp_sol_10cm",
                name="Température Sol (-10cm)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=5.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=14.0, max_val=22.0, period=150.0, noise_percent=0.8),
            ),
            VariableConfig(
                id="debit_arrosage_lmin",
                name="Débit Injecté Électrovanne",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="l/min",
                publish_interval=3.0,
                sim_mode=SimMode.SQUARE,
                math_config=MathConfig(min_val=0.0, max_val=45.0, period=60.0, noise_percent=1.5),
            ),
            VariableConfig(
                id="conso_eau_session_m3",
                name="Volume Arrosage Session",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="m³",
                publish_interval=10.0,
                sim_mode=SimMode.RAMP,
                math_config=MathConfig(min_val=0.0, max_val=1.8, period=60.0, noise_percent=0.0),
            ),
            VariableConfig(
                id="vanne_secteur_ouverte",
                name="État Électrovanne Secteur",
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

    # 4.7 Sonde Acoustique & Nuisances Sonores Urbaines
    catalog.append(EquipmentPreset(
        id="city_acoustic_sensor",
        category=cat_city,
        category_label=cat_city_label,
        name="Sonde Acoustique & Nuisances Sonores",
        description="Surveillance environnementale du bruit urbain et de chantiers : niveaux LAeq, LCpeak et alertes de dépassement.",
        icon="volume-2",
        default_protocol=TransportProtocol.HTTP,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="niveau_laeq_dba",
                name="Pression Acoustique Équivalente LAeq",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="dB(A)",
                publish_interval=2.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=48.0, max_val=78.0, offset=62.0, noise_percent=5.0),
            ),
            VariableConfig(
                id="niveau_lcpeak_dbc",
                name="Niveau Crête Instantané LCpeak",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="dB(C)",
                publish_interval=1.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=65.0, max_val=102.0, offset=82.0, noise_percent=8.0),
            ),
            VariableConfig(
                id="batterie_solaire_v",
                name="Tension Batterie Solaire",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="V",
                publish_interval=15.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=12.4, max_val=13.8, offset=13.1, noise_percent=0.5),
            ),
            VariableConfig(
                id="depassement_seuil_nocturne",
                name="Alerte Dépassement Seuil Bruit",
                device_id="",
                var_type=VariableType.ATTRIBUTE,
                data_type=DataType.BOOLEAN,
                unit="",
                publish_interval=10.0,
                sim_mode=SimMode.CONSTANT,
                math_config=MathConfig(constant_val=False),
            ),
        ]
    ))

    # 4.8 Surveillance Structurelle Ponts & Ouvrages d'Art (SHM)
    catalog.append(EquipmentPreset(
        id="city_structure_shm",
        category=cat_city,
        category_label=cat_city_label,
        name="Surveillance Ouvrage d'Art (SHM)",
        description="Instrumentation structurelle (ponts, viaducs, tunnels) : inclinométrie mrad, fissuromètre, déformation et résonance.",
        icon="git-commit",
        default_protocol=TransportProtocol.MQTT,
        default_platform=PlatformType.THINGSBOARD,
        variables=[
            VariableConfig(
                id="inclinometrie_mrad",
                name="Inclinaison Piles / Tablier",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="mrad",
                publish_interval=2.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=-1.2, max_val=1.2, offset=0.1, noise_percent=2.0),
            ),
            VariableConfig(
                id="ecartement_fissure_mm",
                name="Écartement Fissuromètre",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="mm",
                publish_interval=5.0,
                sim_mode=SimMode.RANDOM_WALK,
                math_config=MathConfig(min_val=1.42, max_val=1.58, step=0.005, noise_percent=0.5),
            ),
            VariableConfig(
                id="deformation_microstrain",
                name="Contrainte Déformation (Jauge)",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="µε",
                publish_interval=2.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=-85.0, max_val=140.0, period=45.0, noise_percent=3.0),
            ),
            VariableConfig(
                id="frequence_propre_hz",
                name="Fréquence Fondamentale Propre",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="Hz",
                publish_interval=5.0,
                sim_mode=SimMode.GAUSSIAN,
                math_config=MathConfig(min_val=2.15, max_val=2.35, offset=2.24, noise_percent=0.3),
            ),
            VariableConfig(
                id="temp_acier_beton",
                name="Température Interne Béton/Acier",
                device_id="",
                var_type=VariableType.TELEMETRY,
                data_type=DataType.FLOAT,
                unit="°C",
                publish_interval=10.0,
                sim_mode=SimMode.SINE,
                math_config=MathConfig(min_val=8.0, max_val=26.0, period=160.0, noise_percent=0.5),
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

