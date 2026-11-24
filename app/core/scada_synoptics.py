"""
ISA-101 Modular SCADA Synoptic Assembler for all 35 Industrial Use Cases.

Assembles ANSI/ISA-101.01 High-Performance HMI vector SVG synoptics for every built-in
equipment preset by composing standardized components from `app/core/svg_components.py`
(`render_synoptic_component`) linked by desaturated process lines on a matte light-gray
canvas (#E5E7EB).

All real-time tags follow ThingsBoard 4.3 `html_value_card` conventions (`${clean_key:1}`).
"""

from typing import Dict, List, Optional, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, DataType
from app.core.svg_components import render_synoptic_component

SCADA_CSS = """
<style>
  .scada-container {
    background: #E5E7EB;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 14px 16px;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #0F172A;
  }
  .scada-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #CBD5E1;
    padding-bottom: 8px;
    margin-bottom: 10px;
  }
  .scada-title {
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .scada-live-indicator {
    display: inline-block;
    width: 9px;
    height: 9px;
    background: #475569;
    border-radius: 50%;
  }
  .scada-badge {
    background: #F1F5F9;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 11px;
    color: #334155;
  }
  .scada-badge strong { color: #0F172A; }
</style>
"""


def get_clean_var_key(variable: VariableConfig) -> str:
    """Strips internal simulator device prefixes from variable identifiers."""
    if variable.device_id and variable.id.startswith(f"{variable.device_id}_"):
        return variable.id[len(variable.device_id) + 1:]
    return variable.id


def scada_wrapper(title: str, token: str, proto: str, svg_content: str) -> str:
    """Wraps raw SVG content inside a standardized ISA-101 matte light-gray SCADA container."""
    return f"""{SCADA_CSS}
<div class="scada-container">
  <div class="scada-header">
    <div class="scada-title">
      <span class="scada-live-indicator"></span>
      {title}
    </div>
    <div style="display:flex; gap:10px; align-items:center;">
      <div class="scada-badge">Protocole: <strong>{proto}</strong></div>
      <div class="scada-badge">Norme: <strong>ANSI/ISA-101</strong></div>
    </div>
  </div>
  {svg_content}
</div>
"""


def make_callout(x: int, y: int, label: str, value_expr: str, accent: str = "#475569", width: int = 155, height: int = 40) -> str:
    """Generates a high-contrast ISA-101 SCADA metric callout box in vector SVG."""
    return f"""
    <g transform="translate({x}, {y})">
      <rect width="{width}" height="{height}" rx="6" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="1.5"/>
      <rect width="4" height="{height}" rx="2" fill="{accent}"/>
      <text x="12" y="15" fill="#475569" font-size="9" font-weight="600">{label}</text>
      <text x="12" y="32" fill="#0F172A" font-size="13" font-weight="bold" font-family="monospace">{value_expr}</text>
    </g>"""


# Declarative ISA-101 Synoptic Mapping for all 35 Built-In Equipment Presets
# Each entry maps preset_id -> list of (svg_component_id, var_key, short_label)
SYNOPTIC_COMPONENT_MAP: Dict[str, List[Tuple[str, str, str]]] = {
    # 1. INDUSTRIE & AUTOMATISMES (9)
    "ind_compressor": [
        ("proc_screw_compressor", "pression_reseau", "Compresseur Vis"),
        ("proc_air_dryer_filter", "temp_vis_huile", "Huile / Sécheur"),
        ("proc_flowmeter", "debit_air", "Débit Air"),
        ("elec_power_analyzer", "puissance_active", "Puissance Active"),
    ],
    "ind_spindle": [
        ("proc_motor_cnc", "vitesse_rotation", "Broche CNC"),
        ("isa_transmitter_vt", "vibration_rms", "Vibration RMS"),
        ("isa_transmitter_tt", "temp_palier", "Temp. Palier"),
        ("elec_power_analyzer", "courant_moteur", "Courant Moteur"),
    ],
    "ind_chiller": [
        ("proc_chiller", "temp_eau_depart", "Eau Glacée Dép."),
        ("hvac_plate_exchanger", "temp_eau_retour", "Retour Échangeur"),
        ("isa_transmitter_pt", "pression_hp", "Pression HP"),
        ("isa_analog_bar", "cop_instantane", "COP Instantané"),
    ],
    "ind_conveyor": [
        ("proc_conveyor", "cadence_pieces", "Convoyeur Ligne"),
        ("proc_robot_6axis", "vitesse_bande", "Robot / Bande"),
        ("isa_analog_bar", "taux_rendement_trs", "Rendement TRS"),
    ],
    "ind_cold_room": [
        ("proc_cold_room_evap", "temp_chambre_froide", "Chambre Froide"),
        ("isa_transmitter_tt", "temp_evaporateur", "Évaporateur"),
        ("proc_chiller", "puissance_groupe_kw", "Groupe Froid"),
        ("isa_alarm_badge", "porte_ouverte", "Contact Porte"),
    ],
    "ind_steam_boiler": [
        ("hvac_boiler", "pression_vapeur_bar", "Chaudière Vapeur"),
        ("proc_flowmeter", "debit_vapeur_th", "Débit Vapeur"),
        ("isa_transmitter_tt", "temp_fumees", "Temp. Fumées"),
        ("isa_analog_bar", "rendement_combustion_pct", "Rendement"),
    ],
    "ind_cleanroom_cta": [
        ("hvac_ahu_complete", "surpression_salle_pa", "Surpression ISO"),
        ("hvac_fan", "renouvellement_air_volh", "Renouv. Air"),
        ("hvac_qai_sensor", "comptage_particules_05", "Particules 0.5µm"),
        ("isa_alarm_badge", "alarme_depressurisation", "Dépressurisation"),
    ],
    "ind_thermal_furnace": [
        ("hvac_boiler", "temp_zone_1", "Four Zone 1"),
        ("isa_transmitter_tt", "temp_zone_2", "Temp. Zone 2"),
        ("isa_transmitter_tt", "temp_zone_3", "Temp. Zone 3"),
        ("isa_pid_controller", "puissance_bruleurs_pct", "PID Brûleurs"),
    ],
    "ind_iso50001_multifluid": [
        ("elec_power_analyzer", "puissance_elec_kw", "Électricité Usine"),
        ("proc_flowmeter", "debit_gaz_nm3h", "Gaz Naturel"),
        ("proc_pump", "debit_eau_m3h", "Eau Process"),
        ("isa_analog_bar", "ipe_industriel_kwh_t", "IPE (kWh/t)"),
    ],

    # 2. TERTIAIRE & SMART BUILDING (9)
    "bldg_cta": [
        ("hvac_ahu_complete", "temp_soufflage", "CTA Soufflage"),
        ("hvac_damper", "registre_air_neuf", "Registre Air"),
        ("hvac_fan", "debit_soufflage", "Ventilateur"),
        ("isa_transmitter_pt", "pression_filtre", "ΔP Filtres"),
    ],
    "bldg_tgbt": [
        ("elec_busbar", "tension_l1_l2", "Jeu de Barres"),
        ("elec_power_analyzer", "puissance_totale_kw", "Puissance TGBT"),
        ("isa_analog_bar", "facteur_puissance", "Cos φ"),
        ("proc_flowmeter", "debit_eau_general", "Débit Eau"),
    ],
    "bldg_qai": [
        ("hvac_qai_sensor", "taux_co2", "Sonde CO2"),
        ("isa_transmitter_tt", "temp_ambiante", "Température"),
        ("isa_analog_bar", "humidite_ambiante", "Hygrométrie"),
        ("isa_deviation_gauge", "particules_pm25", "Particules PM2.5"),
    ],
    "bldg_heatpump": [
        ("hvac_heatpump", "temp_depart_eau", "PAC Réversible"),
        ("hvac_plate_exchanger", "puissance_thermique_kw", "Échangeur"),
        ("isa_transmitter_pt", "pression_circuit", "Pression Circuit"),
        ("isa_alarm_badge", "mode_chaud", "Mode Chaud"),
    ],
    "bldg_fire_ssi": [
        ("infra_ssi_fire", "opacite_fumee_obsm", "Centrale SSI"),
        ("hvac_fan", "debit_desenfumage_m3h", "Désenfumage"),
        ("elec_ups_asi", "tension_alim_secours", "Alim. Secours"),
        ("isa_alarm_badge", "declencheur_manuel", "Déclencheur"),
    ],
    "bldg_dali_lighting": [
        ("infra_street_light", "gradation_dali_pct", "Éclairage DALI"),
        ("isa_analog_bar", "eclairement_lux", "Éclairement"),
        ("elec_power_analyzer", "puissance_eclairage_w", "Puissance W"),
        ("isa_deviation_gauge", "taux_presence_zone_pct", "Présence Zone"),
    ],
    "bldg_thermal_meter": [
        ("hvac_thermal_meter", "energie_cumulee_mwh", "Compteur MID"),
        ("hvac_plate_exchanger", "delta_t_deg", "Delta T"),
        ("proc_flowmeter", "debit_volumique_m3h", "Débit Eau"),
        ("isa_transmitter_tt", "temp_depart_eau", "Temp. Départ"),
    ],
    "bldg_access_flow": [
        ("infra_access_gate", "flux_entrees_min", "Portique Entrées"),
        ("isa_analog_bar", "jauge_occupation_pct", "Occupation"),
        ("infra_traffic_camera", "flux_sorties_min", "Flux Sorties"),
        ("isa_alarm_badge", "issues_secours_verrouillees", "Issues Secours"),
    ],
    "bldg_bacs_class_a": [
        ("hvac_ahu_complete", "puissance_cvc_kw", "CVC Bâtiment"),
        ("infra_street_light", "puissance_eclairage_kw", "Éclairage DALI"),
        ("isa_analog_bar", "ipe_surfacique_kwh_m2", "IPE Surfacique"),
        ("isa_deviation_gauge", "economie_bacs_pct", "Gain BACS %"),
    ],

    # 3. INFRASTRUCTURES & ÉNERGIE (9)
    "infra_transfo_hta": [
        ("elec_transformer_hta", "charge_transfo_pct", "Transfo HTA/BT"),
        ("isa_transmitter_tt", "temp_huile_transfo", "Temp. Huile"),
        ("elec_power_analyzer", "taux_thd", "Harmoniques THD"),
        ("isa_alarm_badge", "alarme_dgpt2", "Relais DGPT2"),
    ],
    "infra_solar_pv": [
        ("elec_solar_pv", "puissance_injection_kw", "Champs PV"),
        ("elec_inverter", "rendement_onduleur", "Onduleur DC/AC"),
        ("elec_busbar", "tension_dc_string", "Tension String"),
        ("infra_weather_station", "ensoleillement", "Irradiation"),
    ],
    "infra_irve_charger": [
        ("elec_irve_charger", "puissance_charge_kw", "Borne IRVE"),
        ("elec_power_analyzer", "courant_charge_a", "Courant Charge"),
        ("isa_analog_bar", "energie_session_kwh", "Énergie Session"),
        ("isa_alarm_badge", "statut_connecteur", "Connecteur"),
    ],
    "infra_water_pump": [
        ("proc_tank", "niveau_bache_m", "Bâche Relevage"),
        ("proc_pump", "debit_refoulement", "Pompe Relevage"),
        ("elec_power_analyzer", "conso_pompe_kw", "Puissance Pompe"),
        ("isa_alarm_badge", "alarme_debordement", "Débordement"),
    ],
    "infra_wind_turbine": [
        ("elec_wind_turbine", "puissance_active_mw", "Éolienne MW"),
        ("infra_weather_station", "vitesse_vent_ms", "Vitesse Vent"),
        ("proc_motor_cnc", "vitesse_rotor_rpm", "Vitesse Rotor"),
        ("isa_transmitter_tt", "temp_generatrice", "Génératrice"),
    ],
    "infra_bess_storage": [
        ("elec_bess_battery", "soc_pct", "Batterie BESS"),
        ("elec_inverter", "tension_pack_v", "Convertisseur PCS"),
        ("elec_power_analyzer", "courant_charge_decharge_a", "Courant Pack"),
        ("isa_transmitter_tt", "temp_max_cellule", "Temp. Cellule"),
    ],
    "infra_rail_switch": [
        ("infra_rail_switch", "courant_moteur_aiguille_a", "Aiguillage ADV"),
        ("elec_rail_substation", "temps_manoeuvre_ms", "Manœuvre"),
        ("isa_transmitter_tt", "temp_rail_rechauffage", "Réchauffage Rail"),
        ("isa_alarm_badge", "position_aiguille", "Position Voie"),
    ],
    "infra_water_treatment": [
        ("water_bar_screen", "debit_insufflation_nm3h", "Insufflation STEP"),
        ("water_aeration_basin", "oxygene_dissous_mgl", "Bassin Aération"),
        ("water_clarifier", "turbidite_ntu", "Clarificateur"),
        ("isa_analog_bar", "ph_eau", "pH Eau"),
    ],
    "infra_district_heating": [
        ("water_rcu_substation", "puissance_thermique_kw", "Sous-Station RCU"),
        ("hvac_plate_exchanger", "delta_t_primaire", "Delta T Primaire"),
        ("proc_flowmeter", "debit_primaire_m3h", "Débit Primaire"),
        ("hvac_thermal_meter", "energie_thermique_mwh", "Énergie MWh"),
    ],

    # 4. VILLES DURABLES & TÉLÉCOMS (8)
    "city_lighting": [
        ("infra_street_light", "niveau_gradation_pct", "Éclairage LED"),
        ("elec_power_analyzer", "puissance_eclairage_kw", "Puissance Armoire"),
        ("elec_breaker", "courant_fuite_ma", "Différentiel"),
        ("isa_alarm_badge", "alerte_porte_ouverte", "Porte Armoire"),
    ],
    "city_weather": [
        ("infra_weather_station", "vitesse_vent_kmh", "Anémomètre"),
        ("isa_transmitter_tt", "temp_ext", "Temp. Extérieure"),
        ("isa_analog_bar", "humidite_ext", "Hygrométrie"),
        ("isa_deviation_gauge", "indice_uv", "Indice UV"),
    ],
    "telecom_shelter": [
        ("infra_telecom_shelter", "temp_baie_serveur", "Shelter Télécoms"),
        ("elec_ups_asi", "charge_onduleur_pct", "Onduleur 48V"),
        ("elec_bess_battery", "autonomie_batterie_min", "Autonomie Batt."),
        ("isa_alarm_badge", "detection_inondation", "Inondation"),
    ],
    "city_traffic": [
        ("infra_traffic_camera", "debit_vehicules", "Trafic Routier"),
        ("infra_vms_sign", "vitesse_moyenne_kmh", "PMV Vitesse"),
        ("isa_analog_bar", "debit_cyclistes", "Flux Cyclistes"),
        ("isa_alarm_badge", "alerte_congestion", "Congestion"),
    ],
    "city_waste_bin": [
        ("infra_smart_waste_bin", "taux_remplissage_pct", "Conteneur PAV"),
        ("isa_transmitter_tt", "temp_interne_cuve", "Temp. Cuve"),
        ("elec_bess_battery", "batterie_autonomie_pct", "Batterie Capteur"),
        ("isa_alarm_badge", "alerte_incendie", "Alarme Incendie"),
    ],
    "city_smart_irrigation": [
        ("infra_smart_irrigation", "tension_matricielle_sol_cbar", "Tensiomètre Sol"),
        ("proc_valve_2way", "vanne_secteur_ouverte", "Vanne Secteur"),
        ("proc_flowmeter", "debit_arrosage_lmin", "Débit Arrosage"),
        ("isa_transmitter_tt", "temp_sol_10cm", "Temp. Sol"),
    ],
    "city_acoustic_sensor": [
        ("isa_transmitter_vt", "niveau_laeq_dba", "Sonde LAeq"),
        ("isa_analog_bar", "niveau_lcpeak_dbc", "Crête LCpeak"),
        ("elec_solar_pv", "batterie_solaire_v", "Alim. Solaire"),
        ("isa_alarm_badge", "depassement_seuil_nocturne", "Seuil Nocturne"),
    ],
    "city_structure_shm": [
        ("infra_bridge_shm", "ecartement_fissure_mm", "Ouvrage d'Art"),
        ("isa_transmitter_vt", "frequence_propre_hz", "Fréq. Propre"),
        ("isa_deviation_gauge", "inclinometrie_mrad", "Inclinométrie"),
        ("isa_transmitter_tt", "temp_acier_beton", "Temp. Structure"),
    ],
}


def _compose_isa101_process_svg(
    title: str,
    token: str,
    proto: str,
    nodes: List[Tuple[str, str, str]],
    var_map: Dict[str, VariableConfig],
) -> str:
    """Assembles a horizontal ISA-101 process flow SVG from modular SVG components."""
    count = len(nodes)
    card_w = 140
    gap = 38
    margin_x = 24
    total_w = max(720, margin_x * 2 + count * card_w + max(0, count - 1) * gap)
    total_h = 170
    y_pos = 30
    pipe_y = y_pos + 55

    # Desaturated ISA-101 process connecting bus / piping behind cards
    pipes_svg = ""
    if count > 1:
        x_start = margin_x + card_w // 2
        x_end = margin_x + (count - 1) * (card_w + gap) + card_w // 2
        pipes_svg = (
            f'<line x1="{x_start}" y1="{pipe_y}" x2="{x_end}" y2="{pipe_y}" '
            f'stroke="#64748B" stroke-width="5" stroke-linecap="round"/>'
        )
        # Directional flow chevron arrows between cards
        for i in range(count - 1):
            mid_x = margin_x + (i + 1) * card_w + i * gap + gap // 2
            pipes_svg += (
                f'<polygon points="{mid_x - 6},{pipe_y - 6} {mid_x + 6},{pipe_y} {mid_x - 6},{pipe_y + 6}" '
                f'fill="#475569"/>'
            )

    comp_blocks = []
    for idx, (comp_id, var_key, label) in enumerate(nodes):
        x = margin_x + idx * (card_w + gap)
        v_obj = var_map.get(var_key)
        unit = v_obj.unit if v_obj and v_obj.unit else ""
        decimals = 1 if (not v_obj or v_obj.data_type == DataType.FLOAT) else (0 if v_obj.data_type == DataType.INTEGER else -1)
        comp_blocks.append(
            render_synoptic_component(
                component_id=comp_id,
                x=x,
                y=y_pos,
                var_key=var_key,
                unit=unit,
                label=label,
                decimals=decimals,
            )
        )

    svg = (
        f'<svg viewBox="0 0 {total_w} {total_h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">'
        f'{pipes_svg}'
        f'{"".join(comp_blocks)}'
        f'</svg>'
    )
    return scada_wrapper(title, token, proto, svg)


def build_generic_scada_synoptic(name: str, token: str, proto: str, vars_list: list, var_map: dict) -> str:
    """Fallback ISA-101 modular synoptic for custom or dynamically created equipment."""
    fallback_components = ["isa_analog_bar", "isa_transmitter_pt", "isa_transmitter_tt", "isa_pid_controller"]
    nodes: List[Tuple[str, str, str]] = []
    for idx, v in enumerate(vars_list[:4]):
        ck = get_clean_var_key(v)
        comp_id = fallback_components[idx % len(fallback_components)]
        nodes.append((comp_id, ck, v.name[:20]))
    if not nodes:
        nodes = [("isa_analog_bar", "valeur", "Signal Process")]
    return _compose_isa101_process_svg(f"SYNOPTIQUE ISA-101 • {name}", token, proto, nodes, var_map)


def render_custom_synoptic_preview(
    title: str,
    nodes_spec: List[Dict[str, str]],
    variables: List[VariableConfig],
    proto: str = "HTTP",
) -> str:
    """Renders a live ISA-101 modular SVG synoptic from Studio node specs."""
    var_map = {get_clean_var_key(v): v for v in variables}
    tuples: List[Tuple[str, str, str]] = [
        (
            str(n.get("component_id", "isa_analog_bar")),
            str(n.get("var_key", "valeur")),
            str(n.get("label") or n.get("var_key") or "Signal"),
        )
        for n in nodes_spec[:6]
    ]
    if not tuples:
        tuples = [("isa_analog_bar", "valeur", "Signal Process")]
    return _compose_isa101_process_svg(title, "STUDIO", proto, tuples, var_map)


def get_scada_synoptic_html(device: DeviceConfig, variables: List[VariableConfig], preset_id: Optional[str] = None) -> str:
    """Generates an ISA-101 modular SVG SCADA synoptic for any built-in or custom equipment."""
    dev_id = (preset_id or device.id or "").lower()
    dev_name = device.name or device.id
    token_str = device.token or "NON_RENSEIGNE"
    proto_str = device.protocol.value.upper() if hasattr(device.protocol, "value") else str(device.protocol).upper()
    var_map = {get_clean_var_key(v): v for v in variables}

    # 0. Explicit Studio custom synoptic layout takes top priority
    if getattr(device, "custom_synoptic_nodes", None):
        custom_tuples: List[Tuple[str, str, str]] = [
            (
                str(n.get("component_id", "isa_analog_bar")),
                str(n.get("var_key", "valeur")),
                str(n.get("label") or n.get("var_key") or "Signal"),
            )
            for n in device.custom_synoptic_nodes[:6]
        ]
        if custom_tuples:
            return _compose_isa101_process_svg(
                f"SYNOPTIQUE STUDIO ISA-101 • {dev_name}",
                token_str,
                proto_str,
                custom_tuples,
                var_map,
            )

    # 1. Exact preset match
    if dev_id in SYNOPTIC_COMPONENT_MAP:
        return _compose_isa101_process_svg(
            f"SYNOPTIQUE PROCESS • {dev_name}",
            token_str,
            proto_str,
            SYNOPTIC_COMPONENT_MAP[dev_id],
            var_map,
        )

    # 2. Longest substring keyword match
    for key in sorted(SYNOPTIC_COMPONENT_MAP.keys(), key=len, reverse=True):
        if key in dev_id:
            return _compose_isa101_process_svg(
                f"SYNOPTIQUE PROCESS • {dev_name}",
                token_str,
                proto_str,
                SYNOPTIC_COMPONENT_MAP[key],
                var_map,
            )

    # 3. Generic ISA-101 modular fallback
    return build_generic_scada_synoptic(dev_name, token_str, proto_str, variables, var_map)
