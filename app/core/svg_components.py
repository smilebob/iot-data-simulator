"""
ISA-101 High-Performance HMI Modular SCADA SVG Components & ThingsBoard 4.3 Widget Bundle.

Strictly adheres to ANSI/ISA-101.01 High-Performance HMI ergonomics:
- Matte neutral light-gray industrial background (#E5E7EB) to eliminate glare.
- Desaturated slate/steel-gray static equipment & piping (#64748B, #94A3B8, #475569).
- High-contrast dark slate typography (#0F172A) for nominal process values.
- Strict Color by Exception: Amber (#D97706) and Red (#DC2626) reserved exclusively
  for warning/critical thresholds and abnormal states.
"""

import json
from typing import Dict, List, Any
from pydantic import BaseModel

ISA101_BG = "#E5E7EB"
ISA101_BORDER = "#CBD5E1"
ISA101_EQUIP_FILL = "#CBD5E1"
ISA101_EQUIP_STROKE = "#475569"
ISA101_PIPE_STROKE = "#64748B"
ISA101_TEXT_MAIN = "#0F172A"
ISA101_TEXT_TITLE = "#334155"
ISA101_NOMINAL_COLOR = "#475569"
ISA101_WARN_COLOR = "#D97706"
ISA101_CRIT_COLOR = "#DC2626"


class SvgComponentSpec(BaseModel):
    """Metadata and ISA-101 SVG template specification for a single SCADA component."""
    id: str
    name: str
    family: str  # electricity, hvac, process, infrastructure
    family_label: str
    description: str
    default_unit: str
    default_color: str = ISA101_NOMINAL_COLOR
    dynamic_behavior: str  # level, state, value
    svg_body: str  # Inner SVG markup using viewBox="0 0 140 110" and Angular/placeholder bindings


def _wrap_preview_svg(spec: SvgComponentSpec, sample_value: str = "42.5") -> str:
    """Renders a standalone ISA-101 preview SVG (for PDF catalog & documentation)."""
    body = (
        spec.svg_body
        .replace("{{valDisplay}}", f"{sample_value} {spec.default_unit}".strip())
        .replace("{{title}}", spec.name)
        .replace("{{statusColor}}", spec.default_color)
        .replace("[attr.stroke]=\"statusColor\"", f'stroke="{spec.default_color}"')
        .replace("[attr.fill]=\"statusColor\"", f'fill="{spec.default_color}"')
        .replace("[attr.height]=\"fillPct * 0.62\"", 'height="40"')
        .replace("[attr.y]=\"80 - (fillPct * 0.62)\"", 'y="40"')
        .replace("[class.isa-alarm-pulse]=\"isAlarm\"", "")
    )
    return (
        f'<svg viewBox="0 0 140 110" width="140" height="110" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="140" height="110" rx="6" fill="{ISA101_BG}"/>'
        f'{body}</svg>'
    )


def get_svg_components_catalog() -> List[SvgComponentSpec]:
    """Returns all 30 ISA-101 High-Performance HMI modular SCADA SVG components."""
    return [
        # =====================================================================
        # 1. ÉLECTRICITÉ, SLD & ÉNERGIE (IEC 60617) - 8 composants
        # =====================================================================
        SvgComponentSpec(
            id="elec_transformer_hta",
            name="Transformateur HTA/BT",
            family="electricity",
            family_label="Électricité, SLD & Énergie",
            description="Poste de transformation moyenne/basse tension (IEC 60617) en gris acier ISA-101.",
            default_unit="kVA",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="70" y1="8" x2="70" y2="24" stroke="#64748B" stroke-width="3"/>'
                '<circle cx="70" cy="38" r="16" fill="none" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<circle cx="70" cy="58" r="16" fill="none" stroke="#475569" stroke-width="2.5"/>'
                '<line x1="70" y1="74" x2="70" y2="88" stroke="#64748B" stroke-width="3"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_breaker",
            name="Disjoncteur Motorisé",
            family="electricity",
            family_label="Électricité, SLD & Énergie",
            description="Appareil de coupure et protection avec état normal sobre et alarme sur défaut.",
            default_unit="",
            dynamic_behavior="state",
            svg_body=(
                '<line x1="70" y1="10" x2="70" y2="30" stroke="#64748B" stroke-width="3"/>'
                '<rect x="52" y="30" width="36" height="36" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="62" y1="40" x2="78" y2="56" [attr.stroke]="statusColor" stroke-width="3"/>'
                '<line x1="78" y1="40" x2="62" y2="56" [attr.stroke]="statusColor" stroke-width="3"/>'
                '<line x1="70" y1="66" x2="70" y2="86" stroke="#64748B" stroke-width="3"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_busbar",
            name="Jeu de Barres Triphasé",
            family="electricity",
            family_label="Électricité, SLD & Énergie",
            description="Jeu de barres TGBT avec départs et mesure de tension ou puissance.",
            default_unit="V",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="15" y1="40" x2="125" y2="40" [attr.stroke]="statusColor" stroke-width="6" stroke-linecap="round"/>'
                '<line x1="35" y1="40" x2="35" y2="75" stroke="#64748B" stroke-width="2.5"/>'
                '<line x1="70" y1="40" x2="70" y2="75" stroke="#64748B" stroke-width="2.5"/>'
                '<line x1="105" y1="40" x2="105" y2="75" stroke="#64748B" stroke-width="2.5"/>'
                '<circle cx="70" cy="40" r="4.5" fill="#0F172A"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_inverter",
            name="Onduleur DC/AC",
            family="electricity",
            family_label="Électricité, SLD & Énergie",
            description="Convertisseur statique continu/alternatif conforme ISA-101.",
            default_unit="kW",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="35" y="18" width="70" height="58" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="35" y1="76" x2="105" y2="18" stroke="#64748B" stroke-width="1.5"/>'
                '<text x="52" y="38" fill="#334155" font-size="11" font-weight="bold">=</text>'
                '<text x="86" y="64" fill="#0F172A" font-size="14" font-weight="bold">~</text>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_bess_battery",
            name="Batterie Stockage BESS",
            family="electricity",
            family_label="Électricité, SLD & Énergie",
            description="Conteneur de stockage lithium avec niveau de charge proportionnel (SOC %).",
            default_unit="%",
            dynamic_behavior="level",
            svg_body=(
                '<rect x="56" y="10" width="28" height="8" rx="2" fill="#64748B"/>'
                '<rect x="40" y="18" width="60" height="66" rx="6" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="44" y="40" [attr.y]="80 - (fillPct * 0.62)" width="52" height="40" [attr.height]="fillPct * 0.62" rx="3" [attr.fill]="statusColor" opacity="0.45"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_solar_pv",
            name="Panneau Solaire PV",
            family="electricity",
            family_label="Électricité, SLD & Énergie",
            description="Champ photovoltaïque en niveau de gris industriel avec puissance injectée.",
            default_unit="kW",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="25" y="18" width="90" height="56" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="55" y1="18" x2="55" y2="74" stroke="#64748B" stroke-width="1.2"/>'
                '<line x1="85" y1="18" x2="85" y2="74" stroke="#64748B" stroke-width="1.2"/>'
                '<line x1="25" y1="46" x2="115" y2="46" stroke="#64748B" stroke-width="1.2"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_wind_turbine",
            name="Éolienne / Aérogénérateur",
            family="electricity",
            family_label="Électricité, SLD & Énergie",
            description="Turbine éolienne statique ISA-101 sans animation distrayante au nominal.",
            default_unit="MW",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="70" y1="42" x2="70" y2="84" stroke="#64748B" stroke-width="4"/>'
                '<line x1="70" y1="42" x2="70" y2="12" [attr.stroke]="statusColor" stroke-width="3" stroke-linecap="round"/>'
                '<line x1="70" y1="42" x2="96" y2="57" [attr.stroke]="statusColor" stroke-width="3" stroke-linecap="round"/>'
                '<line x1="70" y1="42" x2="44" y2="57" [attr.stroke]="statusColor" stroke-width="3" stroke-linecap="round"/>'
                '<circle cx="70" cy="42" r="4.5" fill="#0F172A"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_irve_charger",
            name="Borne de Recharge IRVE",
            family="electricity",
            family_label="Électricité, SLD & Énergie",
            description="Borne de charge rapide VE avec puissance délivrée.",
            default_unit="kW",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="46" y="14" width="48" height="68" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polygon points="73,26 60,48 70,48 66,66 80,44 70,44" [attr.fill]="statusColor"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),

        # =====================================================================
        # 2. CVC, GTB & THERMIQUE (DIN 1946) - 8 composants
        # =====================================================================
        SvgComponentSpec(
            id="hvac_fan",
            name="Ventilateur / Extracteur",
            family="hvac",
            family_label="CVC, GTB & Thermique",
            description="Ventilateur de soufflage ou extraction CTA conforme DIN 1946 / ISA-101.",
            default_unit="m³/h",
            dynamic_behavior="value",
            svg_body=(
                '<circle cx="70" cy="46" r="28" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<path d="M70,46 C62,24 78,24 70,46 C92,38 92,54 70,46 C78,68 62,68 70,46 C48,54 48,38 70,46 Z" [attr.fill]="statusColor" opacity="0.7"/>'
                '<circle cx="70" cy="46" r="4" fill="#0F172A"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="hvac_damper",
            name="Registre d'Air Motorisé",
            family="hvac",
            family_label="CVC, GTB & Thermique",
            description="Volet de modulation air neuf / reprise en gaine aéraulique.",
            default_unit="%",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="25" y="24" width="90" height="48" fill="#CBD5E1" stroke="#64748B" stroke-width="2"/>'
                '<line x1="45" y1="30" x2="65" y2="66" [attr.stroke]="statusColor" stroke-width="3" stroke-linecap="round"/>'
                '<line x1="75" y1="30" x2="95" y2="66" [attr.stroke]="statusColor" stroke-width="3" stroke-linecap="round"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="hvac_coil_heat",
            name="Batterie Chaude / Froide",
            family="hvac",
            family_label="CVC, GTB & Thermique",
            description="Batterie d'échange thermique en caisson CTA.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="35" y="18" width="70" height="60" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polyline points="45,28 95,38 45,48 95,58 45,68" fill="none" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="hvac_cooling_tower",
            name="Tour Aéroréfrigérante",
            family="hvac",
            family_label="CVC, GTB & Thermique",
            description="Tour de refroidissement industrielle pour rejet thermique condenseur.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<polygon points="44,18 96,18 106,78 34,78" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="48" y1="62" x2="92" y2="62" [attr.stroke]="statusColor" stroke-width="2" stroke-dasharray="4 3"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="hvac_boiler",
            name="Chaudière / Brûleur",
            family="hvac",
            family_label="CVC, GTB & Thermique",
            description="Générateur thermique gaz/vapeur ISA-101 (alerte colorée si dépassement).",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="35" y="16" width="70" height="64" rx="8" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<path d="M70,32 C80,45 80,62 70,66 C60,62 60,45 70,32 Z" [attr.fill]="statusColor" opacity="0.75"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="hvac_heatpump",
            name="Pompe à Chaleur (PAC)",
            family="hvac",
            family_label="CVC, GTB & Thermique",
            description="Module PAC air/eau ou eau/eau avec indication COP ou température départ.",
            default_unit="COP",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="28" y="18" width="84" height="58" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<circle cx="52" cy="47" r="15" fill="none" stroke="#475569" stroke-width="2"/>'
                '<line x1="76" y1="32" x2="100" y2="32" stroke="#64748B" stroke-width="2.5"/>'
                '<line x1="76" y1="47" x2="100" y2="47" stroke="#64748B" stroke-width="2.5"/>'
                '<line x1="76" y1="62" x2="100" y2="62" stroke="#64748B" stroke-width="2.5"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="hvac_qai_sensor",
            name="Sonde QAI / Ambiante",
            family="hvac",
            family_label="CVC, GTB & Thermique",
            description="Boîtier capteur CO2, température ou hygrométrie en zone tertiaire.",
            default_unit="ppm",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="42" y="18" width="56" height="58" rx="8" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<circle cx="70" cy="40" r="10" fill="none" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<circle cx="70" cy="40" r="4" [attr.fill]="statusColor"/>'
                '<line x1="56" y1="62" x2="84" y2="62" stroke="#64748B" stroke-width="2"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="hvac_thermal_meter",
            name="Compteur Calorifique MID",
            family="hvac",
            family_label="CVC, GTB & Thermique",
            description="Calculateur d'énergie thermique aller/retour pour sous-station.",
            default_unit="MWh",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="34" y="20" width="72" height="52" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="44" y="30" width="52" height="18" rx="2" fill="#F1F5F9" stroke="#64748B"/>'
                '<text x="70" y="43" fill="#0F172A" font-size="9" font-family="monospace" text-anchor="middle">MID kWh</text>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),

        # =====================================================================
        # 3. PROCESS INDUSTRIEL, EAU & HYDROGÈNE (ISO 10628) - 8 composants
        # =====================================================================
        SvgComponentSpec(
            id="proc_valve_2way",
            name="Vanne Motorisée 2 Voies",
            family="process",
            family_label="Process Industriel, Eau & H2",
            description="Vanne de sectionnement ou régulation ISO 10628.",
            default_unit="%",
            dynamic_behavior="state",
            svg_body=(
                '<line x1="15" y1="58" x2="125" y2="58" stroke="#64748B" stroke-width="5"/>'
                '<polygon points="48,44 70,58 48,72" [attr.fill]="statusColor"/>'
                '<polygon points="92,44 70,58 92,72" [attr.fill]="statusColor"/>'
                '<line x1="70" y1="58" x2="70" y2="34" stroke="#475569" stroke-width="2"/>'
                '<rect x="58" y="20" width="24" height="14" rx="3" fill="#64748B"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_valve_3way",
            name="Vanne 3 Voies Mélangeuse",
            family="process",
            family_label="Process Industriel, Eau & H2",
            description="Vanne de régulation 3 voies pour boucles hydrauliques et échangeurs.",
            default_unit="%",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="15" y1="50" x2="125" y2="50" stroke="#64748B" stroke-width="4"/>'
                '<line x1="70" y1="50" x2="70" y2="82" stroke="#64748B" stroke-width="4"/>'
                '<polygon points="50,38 70,50 50,62" [attr.fill]="statusColor"/>'
                '<polygon points="90,38 70,50 90,62" [attr.fill]="statusColor"/>'
                '<polygon points="58,70 70,50 82,70" [attr.fill]="statusColor"/>'
                '<rect x="58" y="16" width="24" height="14" rx="3" fill="#64748B"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_pump",
            name="Pompe Centrifuge",
            family="process",
            family_label="Process Industriel, Eau & H2",
            description="Pompe centrifuge ISO 10628 en gris acier ISA-101.",
            default_unit="m³/h",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="15" y1="48" x2="125" y2="48" stroke="#64748B" stroke-width="5"/>'
                '<circle cx="70" cy="48" r="24" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polygon points="58,34 88,48 58,62" [attr.fill]="statusColor"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_tank",
            name="Cuve / Réservoir Niveau",
            family="process",
            family_label="Process Industriel, Eau & H2",
            description="Cuve verticale avec niveau de liquide proportionnel à la télémétrie.",
            default_unit="%",
            dynamic_behavior="level",
            svg_body=(
                '<rect x="38" y="14" width="64" height="70" rx="10" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="42" y="40" [attr.y]="80 - (fillPct * 0.62)" width="56" height="40" [attr.height]="fillPct * 0.62" rx="6" [attr.fill]="statusColor" opacity="0.45"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_flowmeter",
            name="Débitmètre Électromagnétique",
            family="process",
            family_label="Process Industriel, Eau & H2",
            description="Capteur de débit en ligne avec transmetteur déporté.",
            default_unit="m³/h",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="15" y1="58" x2="125" y2="58" stroke="#64748B" stroke-width="5"/>'
                '<circle cx="70" cy="58" r="16" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<text x="70" y="62" fill="#0F172A" font-size="10" font-weight="bold" text-anchor="middle">FT</text>'
                '<line x1="70" y1="42" x2="70" y2="28" stroke="#475569" stroke-width="2"/>'
                '<rect x="52" y="14" width="36" height="16" rx="3" fill="#F1F5F9" stroke="#475569"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_electrolyzer",
            name="Électrolyseur PEM Hydrogène",
            family="process",
            family_label="Process Industriel, Eau & H2",
            description="Stack d'électrolyse multi-cellules avec production H2.",
            default_unit="Nm³/h",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="30" y="18" width="80" height="58" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="50" y1="24" x2="50" y2="70" stroke="#475569" stroke-width="2"/>'
                '<line x1="63" y1="24" x2="63" y2="70" stroke="#64748B" stroke-width="2"/>'
                '<line x1="77" y1="24" x2="77" y2="70" stroke="#475569" stroke-width="2"/>'
                '<line x1="90" y1="24" x2="90" y2="70" stroke="#64748B" stroke-width="2"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_motor_cnc",
            name="Moteur / Broche CNC",
            family="process",
            family_label="Process Industriel, Eau & H2",
            description="Moteur asynchrone ou broche d'usinage instrumentée (RPM / Vibration).",
            default_unit="rpm",
            dynamic_behavior="value",
            svg_body=(
                '<circle cx="70" cy="46" r="24" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<text x="70" y="51" fill="#0F172A" font-size="14" font-weight="bold" text-anchor="middle">M</text>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_conveyor",
            name="Convoyeur / Ligne Process",
            family="process",
            family_label="Process Industriel, Eau & H2",
            description="Convoyeur à bande industriel avec rouleaux d'entraînement.",
            default_unit="pcs/min",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="20" y="38" width="100" height="22" rx="11" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<circle cx="34" cy="49" r="5" fill="#475569"/>'
                '<circle cx="70" cy="49" r="5" fill="#475569"/>'
                '<circle cx="106" cy="49" r="5" fill="#475569"/>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),

        # =====================================================================
        # 4. INFRASTRUCTURES, RAIL, SMART CITY & TÉLÉCOMS - 6 composants
        # =====================================================================
        SvgComponentSpec(
            id="infra_street_light",
            name="Mât Éclairage Public LED",
            family="infrastructure",
            family_label="Infrastructures, Rail & Smart City",
            description="Candélabre urbain connecté avec gradation lumineuse.",
            default_unit="%",
            dynamic_behavior="state",
            svg_body=(
                '<path d="M45,82 L45,24 L95,24" fill="none" stroke="#475569" stroke-width="4" stroke-linecap="round"/>'
                '<rect x="82" y="20" width="22" height="8" rx="3" [attr.fill]="statusColor"/>'
                '<polygon points="84,28 102,28 112,56 74,56" [attr.fill]="statusColor" opacity="0.22"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_rail_switch",
            name="Aiguillage Ferroviaire",
            family="infrastructure",
            family_label="Infrastructures, Rail & Smart City",
            description="Appareil de voie ADV avec contrôle de position et effort moteur.",
            default_unit="A",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="15" y1="58" x2="125" y2="58" stroke="#64748B" stroke-width="4"/>'
                '<line x1="48" y1="58" x2="115" y2="26" [attr.stroke]="statusColor" stroke-width="4"/>'
                '<rect x="44" y="64" width="18" height="12" rx="2" fill="#475569"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_bridge_shm",
            name="Ouvrage d'Art / Pont SHM",
            family="infrastructure",
            family_label="Infrastructures, Rail & Smart City",
            description="Monitoring structurel de pont (déformation, vibration, inclinaison).",
            default_unit="mm",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="15" y1="46" x2="125" y2="46" [attr.stroke]="statusColor" stroke-width="5"/>'
                '<rect x="35" y="46" width="10" height="34" fill="#64748B"/>'
                '<rect x="95" y="46" width="10" height="34" fill="#64748B"/>'
                '<circle cx="70" cy="46" r="5" fill="#0F172A"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_weather_station",
            name="Station Météo Urbaine",
            family="infrastructure",
            family_label="Infrastructures, Rail & Smart City",
            description="Anémomètre, pyranomètre et capteur pluviométrique connecté.",
            default_unit="km/h",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="70" y1="22" x2="70" y2="82" stroke="#64748B" stroke-width="3"/>'
                '<line x1="42" y1="36" x2="98" y2="36" stroke="#475569" stroke-width="2.5"/>'
                '<circle cx="42" cy="36" r="6" [attr.fill]="statusColor"/>'
                '<circle cx="98" cy="36" r="6" [attr.fill]="statusColor"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_telecom_shelter",
            name="Shelter / Baie Télécoms 48V",
            family="infrastructure",
            family_label="Infrastructures, Rail & Smart City",
            description="Armoire télécoms / Data Center Edge avec température interne et alimentation 48V DC.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="36" y="16" width="68" height="66" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="44" y="24" width="52" height="12" rx="2" fill="#F1F5F9" stroke="#64748B"/>'
                '<rect x="44" y="42" width="52" height="12" rx="2" fill="#F1F5F9" stroke="#64748B"/>'
                '<circle cx="52" cy="30" r="2.5" fill="#475569"/>'
                '<circle cx="52" cy="48" r="2.5" fill="#475569"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_ssi_fire",
            name="Centrale Incendie SSI",
            family="infrastructure",
            family_label="Infrastructures, Rail & Smart City",
            description="Tableau de signalisation incendie conforme ISA-101 (gris au repos, rouge en alarme).",
            default_unit="",
            dynamic_behavior="state",
            svg_body=(
                '<rect x="38" y="18" width="64" height="60" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polygon points="70,28 86,58 54,58" fill="none" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<text x="70" y="54" [attr.fill]="statusColor" font-size="13" font-weight="bold" text-anchor="middle">!</text>'
                '<text x="70" y="98" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
    ]


def _build_widget_type_dict(spec: SvgComponentSpec, bundle_alias: str = "scada_industrial_suite") -> Dict[str, Any]:
    """Builds an ISA-101 ThingsBoard 4.3 widgetType definition for a modular SVG component."""
    template_html = (
        '<div class="isa101-widget-card" [class.isa-alarm-pulse]="isAlarm">'
        '  <div class="isa101-widget-title">{{title}}</div>'
        '  <svg viewBox="0 0 140 110" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">'
        f'    {spec.svg_body}'
        '  </svg>'
        '</div>'
    )

    template_css = (
        f".isa101-widget-card {{ width:100%; height:100%; background:{ISA101_BG}; border-radius:8px; "
        f"border:1px solid {ISA101_BORDER}; display:flex; flex-direction:column; align-items:center; "
        "justify-content:space-between; padding:8px; box-sizing:border-box; font-family:sans-serif; }\n"
        f".isa101-widget-title {{ font-size:11px; font-weight:700; color:{ISA101_TEXT_TITLE}; text-align:center; "
        "white-space:nowrap; overflow:hidden; text-overflow:ellipsis; width:100%; }\n"
        f"@keyframes isaAlarmPulse {{ 0%, 100% {{ border-color: {ISA101_BORDER}; }} 50% {{ border-color: {ISA101_CRIT_COLOR}; }} }}\n"
        ".isa-alarm-pulse { animation: isaAlarmPulse 1.2s ease-in-out infinite; border-width: 2px; }\n"
    )

    controller_script = """
self.onInit = function() {
    var s = self.ctx.settings || {};
    self.ctx.$scope.title = s.title || (self.ctx.widget && self.ctx.widget.config && self.ctx.widget.config.title) || "__NAME__";
    self.ctx.$scope.unit = s.unit || "";
    self.ctx.$scope.decimals = s.decimals !== undefined ? Number(s.decimals) : 1;
    self.ctx.$scope.accentColor = s.accentColor || "__COLOR__";
    self.ctx.$scope.valDisplay = "--";
    self.ctx.$scope.isAlarm = false;
    self.ctx.$scope.fillPct = 50;
    self.ctx.$scope.statusColor = self.ctx.$scope.accentColor;
    self.onDataUpdated();
};

self.onDataUpdated = function() {
    var s = self.ctx.settings || {};
    var val = null;
    var unit = s.unit || "";
    if (self.ctx.data && self.ctx.data.length > 0) {
        var ds = self.ctx.data[0];
        if (!unit && ds.dataKey && ds.dataKey.units) {
            unit = ds.dataKey.units;
        }
        if (ds.data && ds.data.length > 0) {
            val = ds.data[ds.data.length - 1][1];
        }
    }
    if (val !== null && val !== undefined) {
        var num = Number(val);
        if (!isNaN(num)) {
            var dec = s.decimals !== undefined ? Number(s.decimals) : 1;
            self.ctx.$scope.valDisplay = num.toFixed(dec) + (unit ? " " + unit : "");
            self.ctx.$scope.fillPct = Math.max(0, Math.min(100, num));
            var c = s.accentColor || "__COLOR__";
            var alarm = false;
            if (s.critThreshold !== undefined && s.critThreshold !== null && s.critThreshold !== "" && num >= Number(s.critThreshold)) {
                c = "#DC2626";
                alarm = true;
            } else if (s.warnThreshold !== undefined && s.warnThreshold !== null && s.warnThreshold !== "" && num >= Number(s.warnThreshold)) {
                c = "#D97706";
            }
            self.ctx.$scope.statusColor = c;
            self.ctx.$scope.isAlarm = alarm;
        } else {
            self.ctx.$scope.valDisplay = String(val);
            var isFault = (val === true || val === "true" || val === "ALARM" || val === "FAULT");
            self.ctx.$scope.statusColor = isFault ? "#DC2626" : "__COLOR__";
            self.ctx.$scope.isAlarm = isFault;
        }
    }
    self.ctx.detectChanges();
};
""".replace("__NAME__", spec.name.replace('"', '\\"')).replace("__COLOR__", spec.default_color)

    settings_schema = {
        "schema": {
            "type": "object",
            "title": "Paramètres ISA-101 SCADA",
            "properties": {
                "title": {"title": "Libellé affiché", "type": "string", "default": spec.name},
                "unit": {"title": "Unité (optionnel, sinon lu depuis DataKey)", "type": "string", "default": spec.default_unit},
                "decimals": {"title": "Décimales", "type": "integer", "default": 1},
                "accentColor": {"title": "Couleur nominale ISA-101 (Gris Acier)", "type": "string", "default": spec.default_color},
                "warnThreshold": {"title": "Seuil Avertissement Ambre (>=)", "type": "number"},
                "critThreshold": {"title": "Seuil Critique Rouge (>=)", "type": "number"},
            },
        },
        "form": ["title", "unit", "decimals", "accentColor", "warnThreshold", "critThreshold"],
    }

    default_config = {
        "datasources": [{"type": "function", "name": "function", "dataKeys": [{"name": "f(x)", "type": "function", "label": spec.name, "color": spec.default_color, "settings": {}, "funcBody": "return 42;"}]}],
        "timewindow": {"realtime": {"timewindowMs": 60000}},
        "showTitle": False,
        "dropShadow": False,
        "backgroundColor": ISA101_BG,
        "color": ISA101_TEXT_MAIN,
        "settings": {
            "title": spec.name,
            "unit": spec.default_unit,
            "decimals": 1,
            "accentColor": spec.default_color,
        },
    }

    return {
        "fqn": f"{bundle_alias}.{spec.id}",
        "name": spec.name,
        "deprecated": False,
        "scada": True,
        "version": 1,
        "image": None,
        "description": spec.description,
        "tags": ["isa-101", "scada", spec.family, "svg"],
        "descriptor": {
            "type": "latest",
            "sizeX": 4,
            "sizeY": 3,
            "resources": [],
            "templateHtml": template_html,
            "templateCss": template_css,
            "controllerScript": controller_script.strip(),
            "settingsSchema": settings_schema,
            "dataKeySettingsSchema": {"schema": {"type": "object", "properties": {}}, "form": ["*"]},
            "defaultConfig": json.dumps(default_config),
        },
    }


def generate_thingsboard_widget_bundle() -> Dict[str, Any]:
    """Generates a complete ISA-101 ThingsBoard 4.3 Widgets Bundle JSON containing all 30 SCADA widgets."""
    bundle_alias = "scada_industrial_suite"
    catalog = get_svg_components_catalog()
    return {
        "widgetsBundle": {
            "alias": bundle_alias,
            "title": "SCADA ISA-101 Industriel & Énergie (30 Composants)",
            "image": None,
            "description": "Bibliothèque conforme ANSI/ISA-101.01 (fond gris mat anti-éblouissement, gris acier au nominal, couleur par exception sur alarme) prête pour ThingsBoard 4.3.",
            "order": 1,
        },
        "widgetTypes": [_build_widget_type_dict(spec, bundle_alias=bundle_alias) for spec in catalog],
    }


def generate_individual_widget_type(component_id: str) -> Dict[str, Any]:
    """Generates a standalone ThingsBoard 4.3 widgetType JSON for a single ISA-101 component."""
    catalog = {c.id: c for c in get_svg_components_catalog()}
    if component_id not in catalog:
        raise ValueError(f"Composant SVG '{component_id}' introuvable.")
    return _build_widget_type_dict(catalog[component_id])
