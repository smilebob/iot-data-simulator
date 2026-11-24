#!/usr/bin/env python3
"""
Générateur du Catalogue Commercial PDF des 35 Cas d'Usage IoT & SCADA (ANSI/ISA-101).

Produit `Documentation/user/catalogue_commercial_cas_usage.pdf` à destination des
commerciaux, avant-ventes et porteurs d'offres numériques (Eiffage Énergie Systèmes).

Usage:
    uv run --with weasyprint --with-requirements requirements.txt \
        python3 scripts/generate_commercial_use_cases_pdf.py
"""

import html
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import weasyprint  # noqa: E402

from app.core.equipment_catalog import EquipmentPreset, get_builtin_catalog  # noqa: E402
from app.core.scada_synoptics import SYNOPTIC_COMPONENT_MAP  # noqa: E402
from app.core.site_blueprints import get_site_blueprints  # noqa: E402
from app.core.svg_components import (  # noqa: E402
    ISA101_NOMINAL_COLOR,
    _resolve_static_body,
    get_svg_components_catalog,
)
from app.models.variable import DataType, SimMode, VariableConfig, VariableType  # noqa: E402

OUTPUT_PDF = ROOT_DIR / "Documentation" / "user" / "catalogue_commercial_cas_usage.pdf"

SECTOR_META: Dict[str, Dict[str, str]] = {
    "industry": {
        "title": "Industrie & Automatismes",
        "subtitle": "Performance industrielle, maintenance prédictive, utilités décarbonées et conformité ISO 50001 / HACCP.",
        "badge": "INDUSTRIE",
    },
    "building": {
        "title": "Tertiaire & Smart Building",
        "subtitle": "Conformité Décret BACS & Décret Tertiaire, confort occupants, efficacité énergétique CVC et sécurité ERP/IGH.",
        "badge": "SMART BUILDING",
    },
    "infrastructure": {
        "title": "Infrastructures & Énergie",
        "subtitle": "Réseaux électriques HTA/BT, énergies renouvelables, stockage BESS, mobilité IRVE, eau, RCU et ferroviaire.",
        "badge": "INFRA & ÉNERGIE",
    },
    "smart_city": {
        "title": "Villes Durables & Télécoms",
        "subtitle": "Éclairage public intelligent, mobilité urbaine, gestion de l'eau, déchets connectés, télécoms et ouvrages d'art.",
        "badge": "SMART CITY",
    },
}

SECTOR_ORDER = ["industry", "building", "infrastructure", "smart_city"]

# Argumentaires commerciaux sur-mesure pour les 35 cas d'usage intégrés
COMMERCIAL_PITCHES: Dict[str, Dict[str, object]] = {
    # =========================================================================
    # 1. INDUSTRIE & AUTOMATISMES (9)
    # =========================================================================
    "ind_compressor": {
        "accroche": "Réduisez jusqu'à 20 % la facture d'air comprimé — l'utilité la plus énergivore de l'usine — tout en anticipant les pannes de compression.",
        "benefices": [
            "Détection précoce des fuites réseau et des dérives thermiques d'huile avant l'arrêt de ligne.",
            "Optimisation des cycles charge/marche à vide et suivi en temps réel du coût spécifique (kWh/Nm³).",
            "Pilotage à distance de la consigne de pression et de l'arrêt week-end / hors production.",
        ],
        "cibles": "Directeurs d'Usine • Responsables Utilités & Maintenance • Énergéticiens Industriels",
        "roi": "ROI typique : 6 à 12 mois",
    },
    "ind_spindle": {
        "accroche": "Passez de la maintenance curative à la maintenance prédictive sur vos machines-outils critiques grâce à l'analyse vibratoire et thermique continue.",
        "benefices": [
            "Alerte précoce sur l'usure des roulements (seuil RMS mm/s) évitant la casse broche et les rebuts qualité.",
            "Suivi de la dérive thermique palier et du courant moteur pour détecter l'usure d'outil.",
            "Réduction de 30 à 50 % des arrêts non planifiés sur centres d'usinage CNC.",
        ],
        "cibles": "Responsables Maintenance Industrielle • Chefs d'Atelier Usinage • Aéronautique & Automobile",
        "roi": "ROI typique : 1 casse broche évitée",
    },
    "ind_chiller": {
        "accroche": "Sécurisez le refroidissement de vos procédés industriels tout en maximisant le rendement frigorifique (COP) de vos groupes froids.",
        "benefices": [
            "Supervision continue du cycle thermodynamique (départ/retour eau glacée, HP/BP, COP instantané).",
            "Détection rapide d'encrassement condenseur ou de fuite de fluide frigorigène (conformité F-Gaz).",
            "Ajustement dynamique de la consigne d'eau glacée selon la charge process réelle.",
        ],
        "cibles": "Industrie Agroalimentaire • Plasturgie • Chimie / Pharma • Data Centers",
        "roi": "Gain énergétique : 10 à 18 %",
    },
    "ind_conveyor": {
        "accroche": "Pilotez votre TRS/OEE en temps réel et éliminez les micro-arrêts sur vos lignes de convoyage et cellules robotisées.",
        "benefices": [
            "Visibilité instantanée sur les cadences, vitesses de bande et compteurs de pièces produites.",
            "Identification immédiate des bourrages, goulots d'étranglement et dérives de temps de cycle.",
            "Tableau de bord atelier clair pour animer les rituels de performance quotidienne (AIC).",
        ],
        "cibles": "Directeurs de Production • Responsables Logistique & Intralogistique • Agroalimentaire",
        "roi": "Gain TRS : +3 à +8 points",
    },
    "ind_cold_room": {
        "accroche": "Garantissez une traçabilité 100 % conforme HACCP de la chaîne du froid et prévenez toute perte de marchandise stockée.",
        "benefices": [
            "Enregistrement continu des températures chambre/évaporateur avec alertes immédiates en cas d'excursion.",
            "Détection automatique d'ouverture de porte prolongée ou de défaut de cycle de dégivrage.",
            "Auditabilité réglementaire simplifiée et réduction de la consommation frigorifique nocturne.",
        ],
        "cibles": "Agroalimentaire • Grande Distribution • Entrepôts Frigorifiques • Santé / Pharma",
        "roi": "Zéro perte de stock critique",
    },
    "ind_steam_boiler": {
        "accroche": "Optimisez le rendement de combustion de vos chaufferies vapeur industrielles tout en renforçant la sécurité d'exploitation haute pression.",
        "benefices": [
            "Suivi en temps réel de la pression vapeur, température fumées et débit vapeur distribué.",
            "Détection des dérives de combustion et réduction directe de la consommation de gaz et des émissions CO₂.",
            "Traçabilité réglementaire des paramètres de sécurité chaufferie et aide à la conduite opérateur.",
        ],
        "cibles": "Chimie • Papeterie • Agroalimentaire • Blanchisseries Industrielles • Pharma",
        "roi": "Économie combustible : 5 à 12 %",
    },
    "ind_cleanroom_cta": {
        "accroche": "Maîtrisez en continu la conformité ISO 14644 / BPF de vos salles blanches : cascade de surpression, particules et hygiène aéraulique.",
        "benefices": [
            "Surveillance permanente des différentiels de pression inter-zones pour prévenir toute contamination croisée.",
            "Suivi du comptage particulaire, température et hygrométrie avec journalisation prête pour audit qualité.",
            "Optimisation du taux de renouvellement d'air en mode veille hors production (économie CVC majeure).",
        ],
        "cibles": "Industrie Pharmaceutique • Microélectronique • Hôpitaux (Blocs Opératoires) • Cosmétique",
        "roi": "Conformité audit & -15 % CVC",
    },
    "ind_thermal_furnace": {
        "accroche": "Sécurisez la qualité métallurgique de vos traitements thermiques grâce à un contrôle multi-zones précis des rampes de chauffe.",
        "benefices": [
            "Supervision simultanée des zones de chauffe haute température et de la régulation PID des brûleurs.",
            "Détection précoce des dérives de thermocouples évitant les lots non conformes et rebuts coûteux.",
            "Suivi de l'intensité énergétique par fournée pour réduire l'empreinte carbone du procédé.",
        ],
        "cibles": "Métallurgie • Fonderie • Aéronautique • Verre & Céramique",
        "roi": "Réduction rebuts & -8 % gaz",
    },
    "ind_iso50001_multifluid": {
        "accroche": "Structurez votre plan de comptage multi-fluides (Élec, Gaz, Eau, Air) et pilotez vos Indicateurs de Performance Énergétique (IPE) selon ISO 50001.",
        "benefices": [
            "Consolidation temps réel des 4 fluides majeurs traduits instantanément en coût horaire (€/h) et tCO₂.",
            "Calcul automatique de l'IPE par unité produite pour détecter les dérives de talon énergétique.",
            "Socle clé en main pour obtenir ou renouveler la certification ISO 50001 et les aides CEE.",
        ],
        "cibles": "Directeurs RSE / Énergie • Industriels Énergo-Intensifs • Multi-Sites Industriels",
        "roi": "Éligible fiches CEE • -10 à -15 %",
    },
    # =========================================================================
    # 2. TERTIAIRE & SMART BUILDING (9)
    # =========================================================================
    "bldg_cta": {
        "accroche": "Alliez confort thermique des occupants et sobriété énergétique sur vos Centrales de Traitement d'Air grâce à une supervision fine.",
        "benefices": [
            "Détection de l'encrassement des filtres par perte de charge différentielle pour planifier la maintenance.",
            "Suivi des températures soufflage/reprise et détection des fonctionnements simultanés chaud/froid.",
            "Pilotage à distance des consignes et régimes de ventilation selon l'occupation réelle.",
        ],
        "cibles": "Facility Managers • Directeurs Immobiliers • Exploitants CVC • Bureaux & Hôpitaux",
        "roi": "Économie CVC : 15 à 25 %",
    },
    "bldg_tgbt": {
        "accroche": "Prenez le contrôle total de votre distribution électrique BT : qualité de réseau, pointes de puissance et sous-comptage multi-fluides.",
        "benefices": [
            "Prévention des dépassements de puissance souscrite et des pénalités d'énergie réactive (cos φ).",
            "Visibilité instantanée sur les déséquilibres de phases, la tension et les index de consommation.",
            "Base indispensable pour le délestage intelligent et le reporting Décret Tertiaire (OPERAT).",
        ],
        "cibles": "Gestionnaires de Patrimoine • Centres Commerciaux • Campus • Industrie & Tertiaire",
        "roi": "ROI typique : 6 à 18 mois",
    },
    "bldg_qai": {
        "accroche": "Transformez la Qualité d'Air Intérieur (CO₂, COV, PM2.5) en levier de santé, de productivité et de conformité réglementaire ERP.",
        "benefices": [
            "Suivi continu du CO₂, des particules fines et du confort hygrothermique dans les espaces occupés.",
            "Déclenchement automatique ou guidé du renouvellement d'air uniquement lorsque nécessaire.",
            "Conformité avec les exigences QAI (écoles, crèches, bureaux HQE/WELL/BREEAM).",
        ],
        "cibles": "Collectivités (Écoles/ERP) • Foncières Tertiaires • DRH / QVT • Établissements de Santé",
        "roi": "Conformité QAI & confort prouvé",
    },
    "bldg_heatpump": {
        "accroche": "Maximisez la performance saisonnière de vos Pompes à Chaleur réversibles et accélérez la décarbonation du chauffage tertiaire.",
        "benefices": [
            "Surveillance des régimes chaud/froid, pressions circuit et températures d'échange primaire/secondaire.",
            "Détection précoce des courts-cycles compresseur prolongeant la durée de vie de l'équipement.",
            "Pilotage à distance du mode (Chauffage / Rafraîchissement / Veille) et de la loi d'eau.",
        ],
        "cibles": "Bâtiments Tertiaires • Hôtellerie • Santé • Collectivités Locales",
        "roi": "Gain rendement : +10 à +20 %",
    },
    "bldg_fire_ssi": {
        "accroche": "Renforcez la vigilance sécurité incendie de vos ERP/IGH grâce à la remontée temps réel des états SSI, désenfumage et secours électrique.",
        "benefices": [
            "Supervision centralisée de l'opacité fumées, position des clapets coupe-feu et ventilateurs de désenfumage.",
            "Surveillance continue de la disponibilité des sources de sécurité (batteries / ASI) avant incident.",
            "Traçabilité horodatée facilitant les vérifications périodiques et la levée de doutes PC Sécurité.",
        ],
        "cibles": "Directeurs Sécurité ERP / IGH • Centres Commerciaux • Hôpitaux • Parkings Couverts",
        "roi": "Sécurité réglementaire & traçabilité",
    },
    "bldg_dali_lighting": {
        "accroche": "Divisez jusqu'à deux fois la consommation d'éclairage tertiaire grâce au pilotage DALI asservi à la luminosité naturelle et à la présence.",
        "benefices": [
            "Gradation automatique (daylight harvesting) maintenant un éclairement constant en lux au poste de travail.",
            "Extinction automatique des zones inoccupées et détection rapide des luminaires en défaut.",
            "Contribution directe aux exigences d'automatisation du Décret BACS (Classe A/B).",
        ],
        "cibles": "Bureaux • Établissements Scolaires • Entrepôts Logistiques • Commerces",
        "roi": "Économie éclairage : 40 à 60 %",
    },
    "bldg_thermal_meter": {
        "accroche": "Fiabilisez la facturation énergétique et vos audits thermiques grâce au sous-comptage calorifique certifié (Delta T, débit, MWh).",
        "benefices": [
            "Mesure précise de l'énergie thermique livrée par zone, bâtiment ou locataire (répartition de charges).",
            "Détection immédiate d'un mauvais Delta T signe de déséquilibrage hydraulique ou de vanne fuyarde.",
            "Alimentation automatisée des bilans énergétiques annuels et contrats de performance (CPE).",
        ],
        "cibles": "Bailleurs & Foncières • Exploitants CVC (P1/P2/P3) • Hôpitaux & Campus",
        "roi": "Équilibrage & refacturation exacte",
    },
    "bldg_access_flow": {
        "accroche": "Pilotez la sûreté physique et l'occupation réelle de vos bâtiments pour optimiser l'accueil, le nettoyage et la régulation CVC.",
        "benefices": [
            "Comptage temps réel des flux d'entrée/sortie et de la jauge d'occupation instantanée du site.",
            "Alertes immédiates sur les tentatives d'accès refusées ou l'ouverture anormale d'issues de secours.",
            "Croisement possible avec la GTB pour adapter chauffage et ventilation au taux de présence réel.",
        ],
        "cibles": "Campus d'Entreprises • Stades & ERP • Sites Sensibles • Coworking & Bureaux Flex",
        "roi": "Sûreté + optimisation m² / services",
    },
    "bldg_bacs_class_a": {
        "accroche": "Répondez clé en main aux obligations du Décret BACS et du Décret Tertiaire avec une hypervision GTB Classe A orientée économies d'énergie.",
        "benefices": [
            "Suivi consolidé CVC + Éclairage + IPE surfacique (kWh/m²) et calcul en direct des gains énergétiques.",
            "Détection automatique des dérives de consommation (talon de nuit, week-end, surchauffe).",
            "Livrable prêt pour justifier la conformité BACS et valoriser les certificats d'économies d'énergie (CEE BAT-TH-116).",
        ],
        "cibles": "Propriétaires & Exploitants > 70 kW CVC • Collectivités • Foncières • Retail",
        "roi": "Éligible CEE BAT-TH-116 • -20 à -30 %",
    },
    # =========================================================================
    # 3. INFRASTRUCTURES & ÉNERGIE (9)
    # =========================================================================
    "infra_transfo_hta": {
        "accroche": "Protégez vos postes sources HTA/BT contre les coupures critiques en surveillant en continu le diélectrique, la charge et la protection DGPT2.",
        "benefices": [
            "Anticipation des échauffements d'huile, surpressions cuve et dégradations d'isolement.",
            "Surveillance du taux de distorsion harmonique (THD) protégeant les équipements sensibles aval.",
            "Réduction drastique des risques de black-out site et des coûts d'intervention d'urgence.",
        ],
        "cibles": "Industriels HTA • Data Centers • Hôpitaux • Gestionnaires de Réseaux Privés",
        "roi": "Continuité de service critique 24/7",
    },
    "infra_solar_pv": {
        "accroche": "Maximisez le productible de vos centrales photovoltaïques et ombrières grâce au suivi temps réel du Performance Ratio (PR) et des onduleurs.",
        "benefices": [
            "Détection immédiate des pertes de production par décrochage onduleur, ombrage ou encrassement panneaux.",
            "Corrélation directe entre irradiation solaire mesurée et puissance injectée / autoconsommée.",
            "Valorisation instantanée de l'énergie produite (MWh) et des tonnes de CO₂ évitées.",
        ],
        "cibles": "Producteurs ENR • Industriels & Retail (Ombrières) • Collectivités • Tiers-Investisseurs",
        "roi": "Gain productible : +3 à +7 %/an",
    },
    "infra_irve_charger": {
        "accroche": "Supervisez votre parc de bornes de recharge IRVE, sécurisez la puissance disponible (Smart Charging) et garantissez la disponibilité usagers.",
        "benefices": [
            "Suivi en temps réel des sessions de charge, puissances délivrées et taux de disponibilité bornes.",
            "Pilotage dynamique de la puissance (délestage) pour éviter le renforcement coûteux du raccordement.",
            "Détection rapide des défauts borne permettant une télémaintenance proactive (reset à distance).",
        ],
        "cibles": "Opérateurs CPO • Parkings Tertiaires & Commerciaux • Flottes d'Entreprises • Collectivités",
        "roi": "Disponibilité > 99 % & CapEx évité",
    },
    "infra_water_pump": {
        "accroche": "Fiabilisez vos postes de relevage d'assainissement et prévenez tout risque de débordement ou de pollution environnementale.",
        "benefices": [
            "Surveillance continue du niveau de bâche, des débits refoulés et du temps de marche des pompes.",
            "Gestion de l'alternance des pompes et détection précoce des colmatages par dérive de courant.",
            "Alertes immédiates niveau très haut (H2S / trop-plein) pour intervention rapide des astreintes.",
        ],
        "cibles": "Syndicats des Eaux • Collectivités • Délégataires Eau & Assainissement • Zones Industrielles",
        "roi": "Prévention débordements & -20 % astreintes",
    },
    "infra_wind_turbine": {
        "accroche": "Optimisez la disponibilité de vos parcs éoliens en corrélant vent, orientation nacelle, courbe de puissance et thermique multiplicateur.",
        "benefices": [
            "Suivi temps réel de la vitesse vent, régime rotor, angle yaw et puissance active injectée.",
            "Détection précoce des échauffements paliers/multiplicateur réduisant les interventions lourdes par grue.",
            "Aide au pilotage des bridages acoustiques, environnementaux ou réseau.",
        ],
        "cibles": "Exploitants de Parcs Éoliens • Producteurs d'Énergie Renouvelable • Asset Managers ENR",
        "roi": "Disponibilité parc +1 à +3 %",
    },
    "infra_bess_storage": {
        "accroche": "Monétisez la flexibilité énergétique de vos conteneurs batteries (BESS) tout en préservant l'état de santé (SoH) et la sécurité thermique des cellules.",
        "benefices": [
            "Supervision fine du SoC, SoH, tension pack, équilibrage et températures cellules (anti-emballement).",
            "Pilotage de l'effacement des pointes tarifaires, de l'autoconsommation PV et des services réseau.",
            "Allongement de la durée de vie des batteries grâce à la maîtrise des cycles charge/décharge.",
        ],
        "cibles": "Microgrids Industriels • Centrales ENR Hybrides • Agrégateurs • Sites Isolés / Insulaires",
        "roi": "Optimisation tarifs & durée de vie BESS",
    },
    "infra_rail_switch": {
        "accroche": "Sécurisez la régularité du trafic ferroviaire et tramway grâce à la maintenance prédictive des moteurs d'aiguillages et du réchauffage hivernal.",
        "benefices": [
            "Analyse du courant d'effort d'aiguille pour détecter un point dur mécanique avant la panne bloquante.",
            "Pilotage et surveillance du réchauffage de rail en conditions hivernales (économie d'énergie + sûreté).",
            "Visibilité temps réel des états de voie et détection d'essieux pour les postes de commande.",
        ],
        "cibles": "Opérateurs Ferroviaires • Autorités Organisatrices (Tramway / Métro) • Ports & Sites Embranchés",
        "roi": "Réduction retards & pannes critiques",
    },
    "infra_water_treatment": {
        "accroche": "Maîtrisez la qualité de rejet de vos stations d'épuration (STEP) tout en réduisant jusqu'à 25 % la facture électrique d'aération biologique.",
        "benefices": [
            "Pilotage fin de l'oxygène dissous (O₂), du redox et du pH dans les bassins d'aération.",
            "Asservissement des surpresseurs à la charge polluante réelle (premier poste électrique d'une STEP).",
            "Traçabilité continue des paramètres de rejet conforme aux exigences Police de l'Eau.",
        ],
        "cibles": "Collectivités & Métropoles • Exploitants STEP • Stations Industrielles Agroalimentaires",
        "roi": "Économie électricité aération : 15 à 25 %",
    },
    "infra_district_heating": {
        "accroche": "Optimisez le rendement de vos sous-stations de Réseaux de Chaleur Urbains (RCU) grâce à la maîtrise du Delta T retour et du comptage thermique.",
        "benefices": [
            "Surveillance en continu de l'échangeur primaire/secondaire pour maintenir un retour froid optimal.",
            "Détection immédiate des vannes fuyardes ou dérives de régulation pénalisant tout le réseau urbain.",
            "Calcul en temps réel des MWh livrés et des tonnes de CO₂ évitées pour le reporting délégataire.",
        ],
        "cibles": "Délégataires de Réseaux de Chaleur • Collectivités • Bailleurs Sociaux • Hôpitaux",
        "roi": "Réduction pertes réseau & gain pompage",
    },
    # =========================================================================
    # 4. VILLES DURABLES & TÉLÉCOMS (8)
    # =========================================================================
    "city_lighting": {
        "accroche": "Réduisez jusqu'à 60 % la facture d'éclairage public de vos collectivités grâce à la télégestion d'armoires, la gradation nocturne et la détection de pannes.",
        "benefices": [
            "Pilotage fin des plages d'allumage/extinction et d'abaissement de puissance en cœur de nuit.",
            "Détection automatique des défauts d'isolement et départs coupés sans attendre les signalements citoyens.",
            "Suivi précis des consommations kWh et des économies réalisées pour les élus.",
        ],
        "cibles": "Communes & Métropoles • Syndicats d'Énergie • Zones d'Activités & Ports",
        "roi": "Économie énergie : 40 à 65 %",
    },
    "city_weather": {
        "accroche": "Anticipez les épisodes climatiques extrêmes et cartographiez les îlots de chaleur urbains pour adapter l'exploitation de la ville.",
        "benefices": [
            "Mesure micro-climatique hyper-locale (température, vent, pluie, hygrométrie, UV).",
            "Aide à la décision pour le plan canicule, la viabilité hivernale et la sécurité des chantiers/événements.",
            "Données ouvertes réutilisables pour asservir l'arrosage, la GTB ou l'éclairage public.",
        ],
        "cibles": "Villes & Métropoles • Gestionnaires d'Infrastructures • Ports, Aéroports & Chantiers",
        "roi": "Résilience climatique & sécurité",
    },
    "telecom_shelter": {
        "accroche": "Garantissez une disponibilité de 99,99 % sur vos shelters télécoms, NRO fibre et locaux techniques distants sans déplacements inutiles.",
        "benefices": [
            "Surveillance temps réel de l'autonomie onduleur/batteries, de la climatisation et des intrusions.",
            "Détection précoce des fuites d'eau et surchauffes baies avant coupure du trafic réseau.",
            "Réduction des rondes préventives et diagnostic à distance avant envoi d'une équipe terrain.",
        ],
        "cibles": "Opérateurs Télécoms • RIP Fibre Optique • Infrastructures Critiques • Data Centers Edge",
        "roi": "Réduction déplacements : -30 à -40 %",
    },
    "city_traffic": {
        "accroche": "Objectivez vos politiques de mobilité douce et fluidifiez le trafic urbain grâce au comptage multi-modal (voitures, vélos, vitesses).",
        "benefices": [
            "Mesure continue des flux véhicules, vélos/trottinettes et vitesses moyennes par axe.",
            "Évaluation factuelle de l'impact des aménagements cyclables, ZFE et plans de circulation.",
            "Détection rapide de congestion pour informer les usagers via panneaux à messages variables (PMV).",
        ],
        "cibles": "Collectivités & Métropoles • Gestionnaires de Voirie • Aménageurs Urbains",
        "roi": "Pilotage factuel des mobilités",
    },
    "city_waste_bin": {
        "accroche": "Optimisez jusqu'à 35 % vos tournées de collecte de déchets grâce aux sondes de remplissage et à la détection incendie sur PAV.",
        "benefices": [
            "Collecte dynamique déclenchée uniquement lorsque les conteneurs dépassent le seuil de remplissage.",
            "Prévention des débordements (propreté urbaine) et alerte thermique immédiate en cas de départ de feu.",
            "Réduction des kilomètres parcourus, du carburant et des émissions CO₂ des bennes.",
        ],
        "cibles": "Intercommunalités & Syndicats Déchets • Opérateurs de Propreté • Campus & Parcs",
        "roi": "Réduction tournées : 20 à 35 %",
    },
    "city_smart_irrigation": {
        "accroche": "Économisez jusqu'à 40 % d'eau sur vos espaces verts et terrains sportifs grâce à l'arrosage intelligent piloté par l'humidité réelle du sol.",
        "benefices": [
            "Mesure tensiométrique en profondeur pour n'arroser que selon le besoin hydrique réel des végétaux.",
            "Détection instantanée des fuites de canalisation ou de vannes bloquées ouvertes via débitmètre.",
            "Pilotage à distance des électrovannes et conformité facilitée en période d'arrêtés sécheresse.",
        ],
        "cibles": "Services Espaces Verts (Villes) • Golfs & Complexes Sportifs • Campus & Parcs",
        "roi": "Économie d'eau : 30 à 45 %",
    },
    "city_acoustic_sensor": {
        "accroche": "Maîtrisez les nuisances sonores urbaines et de chantiers grâce à une surveillance acoustique continue et objective (LAeq, LCpeak).",
        "benefices": [
            "Alertes automatiques en cas de dépassement des seuils réglementaires diurnes/nocturnes.",
            "Apaisement des relations riverains sur grands chantiers BTP, zones festives ou axes routiers.",
            "Capteur autonome (solaire/batterie) déployable rapidement sur mât ou façade.",
        ],
        "cibles": "Entreprises de BTP / Grands Chantiers • Collectivités • Sites Industriels ICPE",
        "roi": "Conformité bruit & acceptabilité chantier",
    },
    "city_structure_shm": {
        "accroche": "Sécurisez le patrimoine d'ouvrages d'art (ponts, viaducs, tunnels) par une instrumentation structurelle continue (SHM) à haute précision.",
        "benefices": [
            "Suivi millimétrique des fissures, inclinaisons (mrad), déformations et fréquences vibratoires.",
            "Détection précoce d'évolutions structurelles anormales permettant d'anticiper les travaux lourds.",
            "Priorisation budgétaire objective des opérations de maintenance du patrimoine d'ouvrages.",
        ],
        "cibles": "Gestionnaires d'Autoroutes & Ponts • Collectivités • SNCF / Voies Navigables • Génie Civil",
        "roi": "Sécurité patrimoine & CapEx maîtrisé",
    },
}


def _sample_value_for_var(var: VariableConfig) -> str:
    """Computes a realistic nominal sample value string for a preset variable."""
    if var.data_type == DataType.BOOLEAN:
        return "ON" if (var.math_config.constant_val >= 0.5) else "OFF"
    if var.data_type == DataType.STRING:
        return "NOMINAL"

    mc = var.math_config
    if var.sim_mode == SimMode.CONSTANT:
        val = mc.constant_val
    elif var.sim_mode == SimMode.INTEGRATOR:
        val = max(125.0, var.integrator_config.initial_value + 142.5)
    elif var.sim_mode == SimMode.DERIVED:
        val = (mc.min_val + mc.max_val) / 2.0 if (mc.max_val > mc.min_val) else 42.5
    else:
        val = (mc.min_val + mc.max_val) / 2.0 + mc.offset

    if var.data_type == DataType.INTEGER:
        return f"{int(round(val))}"
    return f"{val:.1f}"


def render_preset_synoptic_svg(preset: EquipmentPreset, svg_catalog: Dict[str, object]) -> str:
    """Renders an authentic ISA-101 horizontal process flow SVG populated with realistic nominal values."""
    nodes = SYNOPTIC_COMPONENT_MAP.get(preset.id, [])
    if not nodes:
        return ""

    var_map = {v.id: v for v in preset.variables}
    count = len(nodes)
    card_w = 140
    gap = 34
    margin_x = 16
    total_w = margin_x * 2 + count * card_w + max(0, count - 1) * gap
    total_h = 128
    y_pos = 9
    pipe_y = y_pos + 55

    pipes_svg = ""
    if count > 1:
        x_start = margin_x + card_w // 2
        x_end = margin_x + (count - 1) * (card_w + gap) + card_w // 2
        pipes_svg = (
            f'<line x1="{x_start}" y1="{pipe_y}" x2="{x_end}" y2="{pipe_y}" '
            f'stroke="#64748B" stroke-width="4.5" stroke-linecap="round"/>'
        )
        for i in range(count - 1):
            mid_x = margin_x + (i + 1) * card_w + i * gap + gap // 2
            pipes_svg += (
                f'<polygon points="{mid_x - 5},{pipe_y - 5} {mid_x + 5},{pipe_y} {mid_x - 5},{pipe_y + 5}" '
                f'fill="#475569"/>'
            )

    comp_blocks: List[str] = []
    for idx, (comp_id, var_key, label) in enumerate(nodes):
        spec = svg_catalog.get(comp_id)
        if not spec:
            continue
        x = margin_x + idx * (card_w + gap)
        v_obj = var_map.get(var_key)
        if v_obj:
            val_str = _sample_value_for_var(v_obj)
            unit = v_obj.unit or spec.default_unit
        else:
            val_str = "42.5"
            unit = spec.default_unit

        val_display = f"{val_str} {unit}".strip()
        body = _resolve_static_body(spec.svg_body, val_display, label, ISA101_NOMINAL_COLOR)
        comp_blocks.append(
            f'<g transform="translate({x}, {y_pos})">'
            f'<rect width="140" height="110" rx="6" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="1.2"/>'
            f'<text x="70" y="11" fill="#334155" font-size="8" font-weight="700" font-family="sans-serif" text-anchor="middle">{html.escape(label[:22])}</text>'
            f"{body}"
            f"</g>"
        )

    return (
        f'<svg viewBox="0 0 {total_w} {total_h}" width="100%" height="104" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{total_w}" height="{total_h}" rx="7" fill="#E5E7EB" stroke="#CBD5E1" stroke-width="1"/>'
        f"{pipes_svg}"
        f'{"".join(comp_blocks)}'
        f"</svg>"
    )


def build_html_document() -> str:
    """Assembles the complete commercial catalog HTML document for WeasyPrint."""
    presets = get_builtin_catalog()
    svg_catalog = {c.id: c for c in get_svg_components_catalog()}
    blueprints = get_site_blueprints()

    grouped: Dict[str, List[EquipmentPreset]] = {s: [] for s in SECTOR_ORDER}
    for p in presets:
        grouped.setdefault(p.category, []).append(p)

    # Blueprints cards HTML
    blueprint_cards_html = ""
    bp_pitches = {
        "site_tertiaire_bacs": "Idéal pour les rendez-vous Direction Immobilière / Facility Management : prouvez en 3 minutes la conformité Décret BACS & Tertiaire avec hypervision multi-équipements.",
        "site_usine_decarbonee": "Parfait pour les Directeurs d'Usine et Responsables Énergie : démontrez le plan de comptage ISO 50001, les utilités critiques et l'autoconsommation photovoltaïque sur un même écran.",
        "site_microgrid_energie": "Conçu pour les projets ENR, Smart Grid et mobilité électrique : mettez en scène la flexibilité PV + Stockage Batterie BESS + Poste HTA + Recharge Rapide IRVE.",
    }
    for bp in blueprints:
        eq_pills = "".join(
            f'<span class="pill-eq">{html.escape(eq.display_name)}</span>'
            for eq in bp.equipments
        )
        blueprint_cards_html += f"""
        <div class="bp-card">
          <div class="bp-header">
            <div>
              <span class="badge-sector">{html.escape(bp.sector)}</span>
              <h3>{html.escape(bp.name)}</h3>
            </div>
            <span class="badge-count">{len(bp.equipments)} équipements liés</span>
          </div>
          <p class="bp-desc">{html.escape(bp.description)}</p>
          <p class="bp-pitch"><strong>Argumentaire démo :</strong> {html.escape(bp_pitches.get(bp.id, ""))}</p>
          <div class="pill-row">{eq_pills}</div>
        </div>
        """

    # Sector sections & 35 Use-Case Cards
    sectors_html = ""
    global_idx = 0
    for sector_idx, sector_key in enumerate(SECTOR_ORDER, start=1):
        meta = SECTOR_META[sector_key]
        sector_presets = grouped.get(sector_key, [])
        cards_html = ""

        for p in sector_presets:
            global_idx += 1
            pitch = COMMERCIAL_PITCHES.get(p.id, {})
            accroche = str(pitch.get("accroche", p.description))
            benefices = list(pitch.get("benefices", [p.description]))
            cibles = str(pitch.get("cibles", "Direction Technique • Exploitation • Maintenance"))
            roi = str(pitch.get("roi", "Démo prête en 1 clic"))

            telemetries = [v for v in p.variables if v.var_type == VariableType.TELEMETRY]
            controls = [v for v in p.variables if v.var_type == VariableType.ATTRIBUTE]

            tel_pills = "".join(
                f'<span class="var-pill">{html.escape(v.name)}'
                + (f' <small>({html.escape(v.unit)})</small>' if v.unit else "")
                + "</span>"
                for v in telemetries[:8]
            )
            if len(telemetries) > 8:
                tel_pills += f'<span class="var-pill var-more">+{len(telemetries) - 8} autres</span>'

            ctrl_pills = "".join(
                f'<span class="ctrl-pill">⚡ {html.escape(v.name)}</span>'
                for v in controls[:4]
            )
            if not ctrl_pills:
                ctrl_pills = '<span class="ctrl-pill ctrl-muted">Supervision temps réel (lecture)</span>'

            ben_li = "".join(f"<li>{html.escape(str(b))}</li>" for b in benefices)
            synoptic_svg = render_preset_synoptic_svg(p, svg_catalog)
            proto = p.default_protocol.value.upper()

            cards_html += f"""
            <div class="uc-card">
              <div class="uc-header">
                <div class="uc-title-group">
                  <span class="uc-num">#{global_idx:02d}</span>
                  <div>
                    <h3 class="uc-title">{html.escape(p.name)}</h3>
                    <div class="uc-meta-sub">ID : <code>{html.escape(p.id)}</code> &nbsp;•&nbsp; {len(telemetries)} mesures &amp; {len(controls)} commande(s)</div>
                  </div>
                </div>
                <div class="uc-badges">
                  <span class="badge-roi">{html.escape(roi)}</span>
                  <span class="badge-proto">{html.escape(proto)}</span>
                </div>
              </div>

              <div class="uc-synoptic">
                {synoptic_svg}
              </div>

              <div class="uc-pitch">
                <span class="pitch-label">PITCH COMMERCIAL</span>
                <p>{html.escape(accroche)}</p>
              </div>

              <div class="uc-grid">
                <div class="uc-col-left">
                  <div class="mini-title">Bénéfices Clients &amp; Valeur Métier</div>
                  <ul class="ben-list">{ben_li}</ul>
                </div>
                <div class="uc-col-right">
                  <div class="mini-title">Cibles &amp; Interlocuteurs</div>
                  <div class="cibles-box">{html.escape(cibles)}</div>

                  <div class="mini-title" style="margin-top:6px;">Grandeurs Supervisées</div>
                  <div class="pill-row">{tel_pills}</div>

                  <div class="mini-title" style="margin-top:6px;">Pilotage Bidirectionnel</div>
                  <div class="pill-row">{ctrl_pills}</div>
                </div>
              </div>
            </div>
            """

        sectors_html += f"""
        <div class="sector-section">
          <div class="sector-banner">
            <div class="sector-banner-top">
              <span class="sector-num">SECTEUR {sector_idx} / 4</span>
              <span class="sector-count">{len(sector_presets)} cas d'usage prêts à démontrer</span>
            </div>
            <h2>{html.escape(meta["title"])}</h2>
            <p>{html.escape(meta["subtitle"])}</p>
          </div>
          {cards_html}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Catalogue Commercial — 35 Cas d'Usage IoT &amp; SCADA (ISA-101)</title>
<style>
  @page {{
    size: A4;
    margin: 14mm 13mm 15mm 13mm;
    @top-left {{
      content: "CATALOGUE COMMERCIAL — 35 CAS D'USAGE IoT & SCADA";
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 7.5pt;
      font-weight: 700;
      color: #64748B;
      letter-spacing: 0.4px;
    }}
    @top-right {{
      content: "Norme ANSI/ISA-101 • ThingsBoard 4.3";
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 7.5pt;
      color: #64748B;
    }}
    @bottom-left {{
      content: "IoT Data Simulator — Offres Numériques & Avant-Vente";
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 7.5pt;
      color: #64748B;
    }}
    @bottom-right {{
      content: "Page " counter(page) " / " counter(pages);
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 7.5pt;
      font-weight: 700;
      color: #334155;
    }}
  }}
  @page :first {{
    @top-left {{ content: none; }}
    @top-right {{ content: none; }}
  }}

  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #0F172A;
    margin: 0;
    padding: 0;
    font-size: 9pt;
    line-height: 1.38;
  }}

  /* COVER PAGE */
  .cover {{
    background: #E5E7EB;
    border: 1.5px solid #CBD5E1;
    border-radius: 12px;
    padding: 26px 28px;
    margin-bottom: 16px;
  }}
  .cover-eyebrow {{
    display: inline-block;
    background: #0F172A;
    color: #F8FAFC;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 4px 10px;
    border-radius: 4px;
    margin-bottom: 12px;
  }}
  .cover h1 {{
    font-size: 23pt;
    line-height: 1.15;
    margin: 0 0 10px 0;
    color: #0F172A;
    letter-spacing: -0.3px;
  }}
  .cover-sub {{
    font-size: 11pt;
    color: #334155;
    margin: 0 0 18px 0;
  }}
  .kpi-strip {{
    display: flex;
    gap: 10px;
    margin-top: 14px;
  }}
  .kpi-box {{
    flex: 1;
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #475569;
    border-radius: 6px;
    padding: 10px 12px;
  }}
  .kpi-val {{
    font-size: 17pt;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.1;
  }}
  .kpi-lbl {{
    font-size: 7.5pt;
    color: #475569;
    font-weight: 600;
    margin-top: 3px;
    text-transform: uppercase;
  }}

  .exec-grid {{
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
  }}
  .exec-box {{
    flex: 1;
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 12px 14px;
  }}
  .exec-box h3 {{
    margin: 0 0 6px 0;
    font-size: 10pt;
    color: #0F172A;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 4px;
  }}
  .exec-box ul {{
    margin: 0;
    padding-left: 16px;
    font-size: 8.5pt;
    color: #334155;
  }}
  .exec-box li {{ margin-bottom: 4px; }}

  .sector-summary-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 6px;
    font-size: 8.5pt;
  }}
  .sector-summary-table th {{
    background: #334155;
    color: #FFFFFF;
    text-align: left;
    padding: 7px 10px;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }}
  .sector-summary-table td {{
    padding: 7px 10px;
    border-bottom: 1px solid #CBD5E1;
    color: #1E293B;
  }}
  .sector-summary-table tr:nth-child(even) td {{ background: #F8FAFC; }}

  .isa-note {{
    margin-top: 14px;
    background: #F1F5F9;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #0F172A;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 8.4pt;
    color: #334155;
  }}

  /* PAGE 2: BLUEPRINTS & PRESALES */
  .page-break {{ page-break-before: always; }}
  .section-title {{
    font-size: 14pt;
    color: #0F172A;
    margin: 0 0 4px 0;
    border-bottom: 2px solid #475569;
    padding-bottom: 5px;
  }}
  .section-intro {{
    font-size: 8.8pt;
    color: #475569;
    margin: 0 0 12px 0;
  }}
  .bp-card {{
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #475569;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 10px;
    page-break-inside: avoid;
  }}
  .bp-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 5px;
  }}
  .bp-header h3 {{
    margin: 3px 0 0 0;
    font-size: 10.5pt;
    color: #0F172A;
  }}
  .badge-sector {{
    display: inline-block;
    background: #E2E8F0;
    color: #334155;
    font-size: 7pt;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    text-transform: uppercase;
  }}
  .badge-count {{
    background: #0F172A;
    color: #F8FAFC;
    font-size: 7.5pt;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    white-space: nowrap;
  }}
  .bp-desc {{ margin: 0 0 5px 0; font-size: 8.5pt; color: #334155; }}
  .bp-pitch {{ margin: 0 0 7px 0; font-size: 8.4pt; color: #0F172A; background: #E5E7EB; padding: 6px 9px; border-radius: 5px; }}
  .pill-eq {{
    display: inline-block;
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    color: #1E293B;
    font-size: 7.4pt;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
    margin: 0 4px 4px 0;
  }}

  .demo-steps {{
    display: flex;
    gap: 8px;
    margin-top: 10px;
  }}
  .demo-step {{
    flex: 1;
    background: #E5E7EB;
    border: 1px solid #CBD5E1;
    border-radius: 7px;
    padding: 9px 10px;
  }}
  .demo-step-num {{
    font-size: 8pt;
    font-weight: 800;
    color: #0F172A;
    text-transform: uppercase;
    margin-bottom: 3px;
  }}
  .demo-step p {{
    margin: 0;
    font-size: 8pt;
    color: #334155;
  }}

  /* SECTOR BANNERS */
  .sector-section {{
    page-break-before: always;
  }}
  .sector-banner {{
    background: #0F172A;
    color: #F8FAFC;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
  }}
  .sector-banner-top {{
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    font-weight: 700;
    color: #CBD5E1;
    letter-spacing: 0.6px;
    margin-bottom: 4px;
  }}
  .sector-banner h2 {{
    margin: 0 0 3px 0;
    font-size: 14pt;
    color: #FFFFFF;
  }}
  .sector-banner p {{
    margin: 0;
    font-size: 8.5pt;
    color: #E2E8F0;
  }}

  /* USE CASE CARDS */
  .uc-card {{
    background: #FFFFFF;
    border: 1.2px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 11px;
    page-break-inside: avoid;
  }}
  .uc-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 6px;
    margin-bottom: 7px;
  }}
  .uc-title-group {{
    display: flex;
    align-items: center;
    gap: 9px;
  }}
  .uc-num {{
    background: #334155;
    color: #FFFFFF;
    font-size: 8.5pt;
    font-weight: 800;
    padding: 4px 7px;
    border-radius: 5px;
    font-family: monospace;
  }}
  .uc-title {{
    margin: 0;
    font-size: 10.8pt;
    color: #0F172A;
    line-height: 1.15;
  }}
  .uc-meta-sub {{
    font-size: 7.4pt;
    color: #64748B;
    margin-top: 1px;
  }}
  .uc-meta-sub code {{
    background: #F1F5F9;
    padding: 1px 4px;
    border-radius: 3px;
    color: #334155;
    font-size: 7.2pt;
  }}
  .uc-badges {{
    display: flex;
    gap: 5px;
    align-items: center;
  }}
  .badge-roi {{
    background: #F1F5F9;
    border: 1px solid #94A3B8;
    color: #0F172A;
    font-size: 7.3pt;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    white-space: nowrap;
  }}
  .badge-proto {{
    background: #334155;
    color: #FFFFFF;
    font-size: 7pt;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
  }}

  .uc-synoptic {{
    margin-bottom: 7px;
    text-align: center;
  }}
  .uc-synoptic svg {{
    display: block;
    margin: 0 auto;
    max-width: 100%;
  }}

  .uc-pitch {{
    background: #E5E7EB;
    border-left: 3.5px solid #0F172A;
    border-radius: 4px;
    padding: 6px 9px;
    margin-bottom: 7px;
  }}
  .pitch-label {{
    display: inline-block;
    font-size: 6.6pt;
    font-weight: 800;
    color: #475569;
    letter-spacing: 0.7px;
    margin-bottom: 1px;
  }}
  .uc-pitch p {{
    margin: 0;
    font-size: 8.6pt;
    font-weight: 600;
    color: #0F172A;
    line-height: 1.3;
  }}

  .uc-grid {{
    display: flex;
    gap: 12px;
  }}
  .uc-col-left {{ flex: 1.15; }}
  .uc-col-right {{ flex: 1; }}

  .mini-title {{
    font-size: 7.2pt;
    font-weight: 800;
    text-transform: uppercase;
    color: #475569;
    letter-spacing: 0.4px;
    margin-bottom: 3px;
  }}
  .ben-list {{
    margin: 0;
    padding-left: 14px;
    font-size: 8pt;
    color: #1E293B;
  }}
  .ben-list li {{ margin-bottom: 3px; }}

  .cibles-box {{
    font-size: 7.8pt;
    color: #0F172A;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 4px;
    padding: 4px 7px;
    font-weight: 600;
  }}
  .pill-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
  }}
  .var-pill {{
    background: #F1F5F9;
    border: 1px solid #CBD5E1;
    color: #1E293B;
    font-size: 6.9pt;
    padding: 1.5px 5px;
    border-radius: 3px;
  }}
  .var-pill small {{ color: #64748B; }}
  .var-more {{ background: #E2E8F0; font-weight: 700; }}
  .ctrl-pill {{
    background: #E2E8F0;
    border: 1px solid #94A3B8;
    color: #0F172A;
    font-size: 7pt;
    font-weight: 700;
    padding: 1.5px 6px;
    border-radius: 3px;
  }}
  .ctrl-muted {{
    background: #F8FAFC;
    border-color: #E2E8F0;
    color: #64748B;
    font-weight: 500;
  }}
</style>
</head>
<body>

  <!-- PAGE 1 : COUVERTURE & SYNTHÈSE EXÉCUTIVE -->
  <div class="cover">
    <span class="cover-eyebrow">BOOK COMMERCIAL &amp; AVANT-VENTE • ÉDITION ANSI/ISA-101</span>
    <h1>Catalogue des 35 Cas d'Usage IoT &amp; Hypervision SCADA</h1>
    <p class="cover-sub">
      Argumentaires métiers, bénéfices clients, leviers ROI et synoptiques vectoriels haute performance prêts à démontrer en direct sur <strong>ThingsBoard 4.3</strong>.
    </p>
    <div class="kpi-strip">
      <div class="kpi-box">
        <div class="kpi-val">35</div>
        <div class="kpi-lbl">Cas d'Usage Métiers</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-val">4</div>
        <div class="kpi-lbl">Secteurs d'Activité</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-val">70</div>
        <div class="kpi-lbl">Composants SVG ISA-101</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-val">&lt; 5 min</div>
        <div class="kpi-lbl">Démo Client Live</div>
      </div>
    </div>
  </div>

  <div class="exec-grid">
    <div class="exec-box">
      <h3>🎯 Pourquoi utiliser ce catalogue en rendez-vous client ?</h3>
      <ul>
        <li><strong>Parler le langage du client</strong> : chaque fiche fournit une accroche métier, 3 bénéfices concrets, les interlocuteurs cibles et les ordres de grandeur ROI.</li>
        <li><strong>Montrer plutôt que promettre</strong> : chaque cas d'usage dispose de son <em>synoptique SCADA vectoriel</em> et de sa simulation physique réaliste déployables en 1 clic.</li>
        <li><strong>Prouver la réactivité en direct</strong> : le <em>Bouton Chaos</em> simule une panne ou une dérive en soutenance pour déclencher les alarmes ISA-101 et le pilotage bidirectionnel.</li>
      </ul>
    </div>
    <div class="exec-box">
      <h3>🧰 Inclus dans la Suite Avant-Vente</h3>
      <ul>
        <li><strong>3 Sites Clients Express</strong> : instanciation multi-équipements complète (Tertiaire BACS, Usine ISO 50001, Microgrid PV+BESS+IRVE).</li>
        <li><strong>Calculateur de Dimensionnement &amp; ROI</strong> : estimation points, débit, stockage et gains réglementaires.</li>
        <li><strong>Livrables d'Offres Automatiques</strong> : export <em>IO List CSV</em> et <em>Dossier d'Architecture Markdown</em> prêts à annexer aux mémoires techniques.</li>
      </ul>
    </div>
  </div>

  <table class="sector-summary-table">
    <thead>
      <tr>
        <th style="width:26%;">Secteur d'Activité</th>
        <th style="width:12%;">Volume</th>
        <th>Exemples de Cas d'Usage &amp; Enjeux Clients</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>1. Industrie &amp; Automatismes</strong></td>
        <td><strong>9 cas</strong></td>
        <td>Air comprimé, Broche CNC, Groupe froid, Convoyeur TRS, Chambre froide HACCP, Chaudière vapeur, Salle blanche ISO, Four thermique, Comptage ISO 50001.</td>
      </tr>
      <tr>
        <td><strong>2. Tertiaire &amp; Smart Building</strong></td>
        <td><strong>9 cas</strong></td>
        <td>CTA, TGBT Multi-Fluides, Qualité d'Air QAI, PAC réversible, Sécurité Incendie SSI, Éclairage DALI, Compteur calories, Contrôle d'accès, GTB Classe A (Décret BACS).</td>
      </tr>
      <tr>
        <td><strong>3. Infrastructures &amp; Énergie</strong></td>
        <td><strong>9 cas</strong></td>
        <td>Poste HTA/BT, Centrale Solaire PV, Bornes IRVE, Relevage assainissement, Éolienne MW, Stockage BESS, Aiguillage ferroviaire, STEP aération, Réseau de chaleur RCU.</td>
      </tr>
      <tr>
        <td><strong>4. Villes Durables &amp; Télécoms</strong></td>
        <td><strong>8 cas</strong></td>
        <td>Éclairage public, Station météo urbaine, Shelter télécoms/fibre, Comptage trafic, Conteneur déchets PAV, Arrosage intelligent, Sonde acoustique, Ouvrage d'art SHM.</td>
      </tr>
    </tbody>
  </table>

  <div class="isa-note">
    <strong>Différenciateur Ergonomique — Conformité stricte ANSI/ISA-101.01 (High-Performance HMI) :</strong>
    Tous les synoptiques présentés dans ce catalogue adoptent les standards industriels de supervision haute performance : fond gris mat anti-fatigue (<code>#E5E7EB</code>), équipements désaturés en état normal, et <strong>codage couleur par exception</strong> redondant forme + couleur (Avertissement <strong>▲ Ambre</strong>, Critique <strong>■ ! Rouge</strong>) garantissant une lecture instantanée par les exploitants et une accessibilité totale (daltonisme).
  </div>

  <!-- PAGE 2 : SITES CLIENTS EXPRESS & SCÉNARIO DE DÉMO -->
  <div class="page-break">
    <h2 class="section-title">Sites Clients Express (Hypervision Multi-Équipements en 1 Clic)</h2>
    <p class="section-intro">
      Au-delà des 35 équipements unitaires, l'outil permet de générer en 1 clic un <strong>site client complet multi-métiers</strong> accompagné de son tableau de bord d'hypervision consolidé ThingsBoard 4.3.
    </p>

    {blueprint_cards_html}

    <h2 class="section-title" style="margin-top:16px;">Déroulé Type d'une Soutenance Client Réussie (10 minutes)</h2>
    <div class="demo-steps">
      <div class="demo-step">
        <div class="demo-step-num">1. Cadrage (2 min)</div>
        <p>Sélectionnez 1 à 4 cas d'usage de ce catalogue (ou un Site Express) correspondant aux équipements réels du prospect.</p>
      </div>
      <div class="demo-step">
        <div class="demo-step-num">2. Démo Live (4 min)</div>
        <p>Ouvrez le dashboard ThingsBoard 4.3 généré : montrez les flux temps réel, le synoptique ISA-101 et les KPI énergétiques.</p>
      </div>
      <div class="demo-step">
        <div class="demo-step-num">3. Effet "Waouh" (2 min)</div>
        <p>Activez le <strong>Bouton Chaos</strong> (dérive thermique / panne) pour déclencher l'alarme visuelle ▲ / ■ !, puis corrigez via le pilotage bidirectionnel.</p>
      </div>
      <div class="demo-step">
        <div class="demo-step-num">4. Projection Offre (2 min)</div>
        <p>Exportez l'<strong>IO List CSV</strong> et le <strong>Dossier d'Architecture</strong> pour repartir avec un livrable concret pour le mémoire technique.</p>
      </div>
    </div>
  </div>

  <!-- PAGES 3+ : LES 35 FICHES PAR SECTEUR -->
  {sectors_html}

</body>
</html>
"""


def main() -> None:
    html_content = build_html_document()
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = weasyprint.HTML(string=html_content).render()
    doc.write_pdf(str(OUTPUT_PDF))
    size_kb = OUTPUT_PDF.stat().st_size / 1024
    print(f"PDF généré avec succès : {OUTPUT_PDF} ({len(doc.pages)} pages, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
