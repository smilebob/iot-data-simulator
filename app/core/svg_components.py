"""
ISA-101 High-Performance HMI Modular SCADA SVG Components (70 Components)
& ThingsBoard 4.3 Widget Bundle Generator.

Strictly adheres to ANSI/ISA-101.01 High-Performance HMI ergonomics:
- Matte neutral light-gray industrial background (#E5E7EB) to eliminate glare.
- Desaturated slate/steel-gray static equipment & piping (#64748B, #94A3B8, #475569).
- High-contrast dark slate typography (#0F172A) for nominal process values.
- Strict Color by Exception with Redundant Shape + Color coding (daltonism-proof):
  * Warning: Amber (#D97706) + triangle indicator (▲)
  * Critical: Red (#DC2626) + square indicator (■ !) + border pulse
"""

import json
from typing import Dict, List, Optional, Any
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

FAMILY_LABELS: Dict[str, str] = {
    "isa101_primitives": "Primitives ISA-101 High-Performance HMI",
    "electricity": "Électricité, Data Centers, HTB/HTA & Mobilité",
    "hvac": "CVC, GTB & Thermique",
    "process": "Process Industriel, Froid, Pharma & Hydrogène",
    "water_rcu": "Eau, Assainissement STEP & Réseaux de Chaleur",
    "infrastructure": "Infrastructures, Tunnels, Sécurité & Smart City",
}


class SvgComponentSpec(BaseModel):
    """Metadata and ISA-101 SVG template specification for a single SCADA component."""
    id: str
    name: str
    family: str
    family_label: str
    description: str
    default_unit: str
    default_color: str = ISA101_NOMINAL_COLOR
    dynamic_behavior: str  # level, state, value, analog_bar
    svg_body: str  # Inner SVG markup using viewBox="0 0 140 110"


def _resolve_static_body(svg_body: str, value_str: str, title_str: str, color: str = ISA101_NOMINAL_COLOR) -> str:
    """Replaces Angular widget bindings with static/ThingsBoard html_value_card expressions."""
    return (
        svg_body
        .replace("{{valDisplay}}", value_str)
        .replace("{{title}}", title_str)
        .replace("{{statusColor}}", color)
        .replace('[attr.stroke]="statusColor"', f'stroke="{color}"')
        .replace('[attr.fill]="statusColor"', f'fill="{color}"')
        .replace('[attr.height]="fillPct * 0.62"', 'height="40"')
        .replace('[attr.y]="80 - (fillPct * 0.62)"', 'y="40"')
        .replace('[attr.y]="78 - (fillPct * 0.56)"', 'y="46"')
        .replace('[attr.x]="24 + (fillPct * 0.92)"', 'x="68"')
        .replace('[class.isa-alarm-pulse]="isAlarm"', "")
    )


def _wrap_preview_svg(spec: SvgComponentSpec, sample_value: str = "42.5") -> str:
    """Renders a standalone ISA-101 preview SVG (for PDF catalog & documentation)."""
    val_text = f"{sample_value} {spec.default_unit}".strip()
    body = _resolve_static_body(spec.svg_body, val_text, spec.name, spec.default_color)
    return (
        f'<svg viewBox="0 0 140 110" width="140" height="110" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="140" height="110" rx="6" fill="{ISA101_BG}"/>'
        f'{body}</svg>'
    )


def render_synoptic_component(
    component_id: str,
    x: int,
    y: int,
    var_key: str,
    unit: str = "",
    label: Optional[str] = None,
    decimals: int = 1,
    scale: float = 1.0,
) -> str:
    """Renders a component as a `<g>` group with ThingsBoard 4.3 `${var_key}` placeholder for P&ID synoptics."""
    catalog = {c.id: c for c in get_svg_components_catalog()}
    if component_id not in catalog:
        raise ValueError(f"Composant SVG '{component_id}' introuvable.")
    spec = catalog[component_id]
    u = unit if unit != "" else spec.default_unit
    val_expr = f"${{{var_key}:{decimals}}} {u}".strip() if decimals >= 0 else f"${{{var_key}}} {u}".strip()
    lbl = label or spec.name
    body = _resolve_static_body(spec.svg_body, val_expr, lbl, spec.default_color)
    transform = f"translate({x}, {y})" if scale == 1.0 else f"translate({x}, {y}) scale({scale})"
    return (
        f'<g transform="{transform}">'
        f'<rect width="140" height="110" rx="6" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="1.2"/>'
        f'<text x="70" y="11" fill="#334155" font-size="8" font-weight="700" font-family="sans-serif" text-anchor="middle">{lbl[:22]}</text>'
        f'{body}'
        f'</g>'
    )


def get_svg_components_catalog() -> List[SvgComponentSpec]:
    """Returns all 70 ISA-101 High-Performance HMI modular SCADA SVG components across 6 families."""
    return [
        # =====================================================================
        # 1. PRIMITIVES ISA-101 HIGH-PERFORMANCE HMI (8 composants)
        # =====================================================================
        SvgComponentSpec(
            id="isa_analog_bar",
            name="Barre Analogique HH/H/L/LL",
            family="isa101_primitives",
            family_label=FAMILY_LABELS["isa101_primitives"],
            description="Indicateur de profil analogique ISA-101 avec bande normale centrale, zones H/L et pointeur mobile.",
            default_unit="%",
            dynamic_behavior="analog_bar",
            svg_body=(
                '<rect x="52" y="18" width="16" height="64" fill="#F1F5F9" stroke="#64748B" stroke-width="1.5"/>'
                '<rect x="52" y="18" width="16" height="10" fill="#CBD5E1"/>'
                '<rect x="52" y="72" width="16" height="10" fill="#CBD5E1"/>'
                '<rect x="54" y="34" width="12" height="32" fill="#94A3B8" opacity="0.5"/>'
                '<line x1="48" y1="28" x2="72" y2="28" stroke="#475569" stroke-width="1"/>'
                '<line x1="48" y1="72" x2="72" y2="72" stroke="#475569" stroke-width="1"/>'
                '<polygon points="71,46 81,41 81,51" [attr.fill]="statusColor"/>'
                '<rect x="48" y="46" [attr.y]="78 - (fillPct * 0.56)" width="24" height="4" [attr.fill]="statusColor"/>'
                '<text x="94" y="25" fill="#475569" font-size="8" font-family="monospace">HH</text>'
                '<text x="94" y="79" fill="#475569" font-size="8" font-family="monospace">LL</text>'
                '<text x="70" y="102" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="isa_pid_controller",
            name="Bloc Régulateur PID (PV/SP)",
            family="isa101_primitives",
            family_label=FAMILY_LABELS["isa101_primitives"],
            description="Faceplate régulateur ISA-101 affichant Mesure (PV), mode AUTO et état de régulation.",
            default_unit="%",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="18" y="16" width="104" height="68" rx="6" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<rect x="18" y="16" width="104" height="18" rx="4" fill="#CBD5E1"/>'
                '<text x="30" y="28" fill="#0F172A" font-size="9" font-weight="bold">PID</text>'
                '<text x="112" y="28" fill="#334155" font-size="8.5" font-weight="bold" text-anchor="end">AUTO</text>'
                '<text x="28" y="54" fill="#475569" font-size="9" font-weight="bold">PV</text>'
                '<text x="112" y="55" fill="#0F172A" font-size="12" font-weight="bold" font-family="monospace" text-anchor="end">{{valDisplay}}</text>'
                '<line x1="26" y1="64" x2="114" y2="64" stroke="#CBD5E1" stroke-width="1"/>'
                '<text x="70" y="77" fill="#475569" font-size="8" font-family="monospace" text-anchor="middle">MODE BOUCLE FERMÉE</text>'
                '<text x="70" y="102" fill="#334155" font-size="9" font-weight="bold" text-anchor="middle">{{title}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="isa_deviation_gauge",
            name="Jauge de Déviation (SP)",
            family="isa101_primitives",
            family_label=FAMILY_LABELS["isa101_primitives"],
            description="Indicateur horizontal d'écart par rapport à la consigne centrale (0 = cible idéale).",
            default_unit="%",
            dynamic_behavior="analog_bar",
            svg_body=(
                '<rect x="18" y="38" width="104" height="22" rx="3" fill="#F1F5F9" stroke="#64748B" stroke-width="1.5"/>'
                '<rect x="52" y="40" width="36" height="18" fill="#CBD5E1"/>'
                '<line x1="70" y1="32" x2="70" y2="66" stroke="#0F172A" stroke-width="2"/>'
                '<rect x="68" [attr.x]="24 + (fillPct * 0.92)" y="35" width="6" height="28" rx="1" [attr.fill]="statusColor"/>'
                '<text x="22" y="76" fill="#475569" font-size="8" font-family="monospace">-DEV</text>'
                '<text x="70" y="76" fill="#0F172A" font-size="8" font-weight="bold" text-anchor="middle">SP</text>'
                '<text x="118" y="76" fill="#475569" font-size="8" font-family="monospace" text-anchor="end">+DEV</text>'
                '<text x="70" y="102" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="isa_alarm_badge",
            name="Badge Alarme Prioritaire ISA",
            family="isa101_primitives",
            family_label=FAMILY_LABELS["isa101_primitives"],
            description="Annonciateur d'alarme à codage redondant Forme + Couleur conforme ISA-18.2 / ISA-101.",
            default_unit="",
            dynamic_behavior="state",
            svg_body=(
                '<rect x="20" y="20" width="100" height="56" rx="6" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polygon points="44,34 56,58 32,58" fill="none" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<text x="44" y="54" [attr.fill]="statusColor" font-size="12" font-weight="bold" text-anchor="middle">!</text>'
                '<text x="86" y="45" fill="#334155" font-size="8.5" font-weight="bold" text-anchor="middle">STATUT</text>'
                '<text x="86" y="60" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
                '<text x="70" y="100" fill="#475569" font-size="8.5" font-weight="bold" text-anchor="middle">ISA-18.2 PRIORITÉ</text>'
            ),
        ),
        SvgComponentSpec(
            id="isa_transmitter_pt",
            name="Transmetteur Pression (PT)",
            family="isa101_primitives",
            family_label=FAMILY_LABELS["isa101_primitives"],
            description="Symbole instrumenté ISA-5.1 de capteur/transmetteur de pression en ligne.",
            default_unit="bar",
            dynamic_behavior="value",
            svg_body=(
                '<circle cx="70" cy="46" r="24" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="46" y1="46" x2="94" y2="46" stroke="#64748B" stroke-width="1.5"/>'
                '<text x="70" y="41" fill="#0F172A" font-size="11" font-weight="bold" text-anchor="middle">PT</text>'
                '<text x="70" y="61" fill="#475569" font-size="8.5" font-family="monospace" text-anchor="middle">101</text>'
                '<line x1="70" y1="70" x2="70" y2="82" stroke="#64748B" stroke-width="2"/>'
                '<text x="70" y="101" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="isa_transmitter_tt",
            name="Transmetteur Température (TT)",
            family="isa101_primitives",
            family_label=FAMILY_LABELS["isa101_primitives"],
            description="Symbole instrumenté ISA-5.1 de sonde/transmetteur thermique.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<circle cx="70" cy="46" r="24" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="46" y1="46" x2="94" y2="46" stroke="#64748B" stroke-width="1.5"/>'
                '<text x="70" y="41" fill="#0F172A" font-size="11" font-weight="bold" text-anchor="middle">TT</text>'
                '<text x="70" y="61" fill="#475569" font-size="8.5" font-family="monospace" text-anchor="middle">201</text>'
                '<line x1="70" y1="70" x2="70" y2="82" stroke="#64748B" stroke-width="2"/>'
                '<text x="70" y="101" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="isa_transmitter_lt",
            name="Transmetteur Niveau (LT)",
            family="isa101_primitives",
            family_label=FAMILY_LABELS["isa101_primitives"],
            description="Symbole instrumenté ISA-5.1 de mesure de niveau radar/ultrason.",
            default_unit="%",
            dynamic_behavior="value",
            svg_body=(
                '<circle cx="70" cy="46" r="24" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="46" y1="46" x2="94" y2="46" stroke="#64748B" stroke-width="1.5"/>'
                '<text x="70" y="41" fill="#0F172A" font-size="11" font-weight="bold" text-anchor="middle">LT</text>'
                '<text x="70" y="61" fill="#475569" font-size="8.5" font-family="monospace" text-anchor="middle">301</text>'
                '<line x1="70" y1="70" x2="70" y2="82" stroke="#64748B" stroke-width="2"/>'
                '<text x="70" y="101" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="isa_transmitter_vt",
            name="Capteur Vibration (VT)",
            family="isa101_primitives",
            family_label=FAMILY_LABELS["isa101_primitives"],
            description="Symbole ISA-5.1 d'accéléromètre de maintenance prédictive (mm/s RMS).",
            default_unit="mm/s",
            dynamic_behavior="value",
            svg_body=(
                '<circle cx="70" cy="46" r="24" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="46" y1="46" x2="94" y2="46" stroke="#64748B" stroke-width="1.5"/>'
                '<text x="70" y="41" fill="#0F172A" font-size="11" font-weight="bold" text-anchor="middle">VT</text>'
                '<polyline points="56,57 62,52 67,62 73,50 78,60 84,56" fill="none" [attr.stroke]="statusColor" stroke-width="1.8"/>'
                '<line x1="70" y1="70" x2="70" y2="82" stroke="#64748B" stroke-width="2"/>'
                '<text x="70" y="101" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),

        # =====================================================================
        # 2. ÉLECTRICITÉ, DATA CENTERS, HTB/HTA & MOBILITÉ (16 composants)
        # =====================================================================
        SvgComponentSpec(
            id="elec_transformer_hta",
            name="Transformateur HTA/BT",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
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
            family_label=FAMILY_LABELS["electricity"],
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
            family_label=FAMILY_LABELS["electricity"],
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
            family_label=FAMILY_LABELS["electricity"],
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
            family_label=FAMILY_LABELS["electricity"],
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
            family_label=FAMILY_LABELS["electricity"],
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
            family_label=FAMILY_LABELS["electricity"],
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
            family_label=FAMILY_LABELS["electricity"],
            description="Borne de charge rapide VE avec puissance délivrée.",
            default_unit="kW",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="46" y="14" width="48" height="68" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polygon points="73,26 60,48 70,48 66,66 80,44 70,44" [attr.fill]="statusColor"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_generator",
            name="Groupe Électrogène",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
            description="Groupe électrogène secours / cogénération (IEC 60617) pour hôpitaux & Data Centers.",
            default_unit="kVA",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="24" y="20" width="92" height="54" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<circle cx="52" cy="47" r="16" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<text x="52" y="52" fill="#0F172A" font-size="12" font-weight="bold" text-anchor="middle">G</text>'
                '<text x="92" y="45" fill="#334155" font-size="9" font-weight="bold" text-anchor="middle">3~</text>'
                '<text x="92" y="58" fill="#475569" font-size="8" font-family="monospace" text-anchor="middle">50Hz</text>'
                '<text x="70" y="99" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_ups_asi",
            name="Onduleur ASI / UPS",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
            description="Alimentation Sans Interruption Data Center / site critique avec taux de charge.",
            default_unit="%",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="30" y="16" width="80" height="62" rx="5" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="38" y="24" width="64" height="20" rx="2" fill="#F1F5F9" stroke="#64748B"/>'
                '<text x="70" y="38" fill="#0F172A" font-size="10" font-weight="bold" text-anchor="middle">UPS / ASI</text>'
                '<line x1="42" y1="60" x2="98" y2="60" stroke="#64748B" stroke-width="3"/>'
                '<circle cx="48" cy="60" r="3" [attr.fill]="statusColor"/>'
                '<circle cx="92" cy="60" r="3" [attr.fill]="statusColor"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_server_rack",
            name="Baie Serveur IT (Data Center)",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
            description="Baie IT 42U avec suivi thermique couloir froid/chaud ou PUE.",
            default_unit="kW",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="40" y="14" width="60" height="70" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="46" y="21" width="48" height="10" rx="1" fill="#F1F5F9" stroke="#64748B"/>'
                '<rect x="46" y="35" width="48" height="10" rx="1" fill="#F1F5F9" stroke="#64748B"/>'
                '<rect x="46" y="49" width="48" height="10" rx="1" fill="#F1F5F9" stroke="#64748B"/>'
                '<rect x="46" y="63" width="48" height="14" rx="1" fill="#94A3B8" opacity="0.5"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_pdu_smart",
            name="PDU Intelligent Triphasé",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
            description="Unité de distribution électrique de salle blanche / Data Center.",
            default_unit="A",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="48" y="14" width="44" height="68" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<circle cx="70" cy="28" r="4" fill="#F1F5F9" stroke="#475569" stroke-width="1.5"/>'
                '<circle cx="70" cy="44" r="4" fill="#F1F5F9" stroke="#475569" stroke-width="1.5"/>'
                '<circle cx="70" cy="60" r="4" fill="#F1F5F9" stroke="#475569" stroke-width="1.5"/>'
                '<text x="70" y="76" fill="#334155" font-size="7.5" font-weight="bold" text-anchor="middle">PDU 3P</text>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_earthing_switch",
            name="Sectionneur de Terre HTA",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
            description="Sectionneur d'isolement et mise à la terre (MALT) pour postes HTB/HTA.",
            default_unit="",
            dynamic_behavior="state",
            svg_body=(
                '<line x1="70" y1="12" x2="70" y2="30" stroke="#64748B" stroke-width="3"/>'
                '<line x1="70" y1="30" x2="88" y2="52" [attr.stroke]="statusColor" stroke-width="3" stroke-linecap="round"/>'
                '<circle cx="70" cy="30" r="3.5" fill="#0F172A"/>'
                '<circle cx="70" cy="56" r="3.5" fill="#0F172A"/>'
                '<line x1="70" y1="56" x2="70" y2="72" stroke="#64748B" stroke-width="3"/>'
                '<line x1="56" y1="72" x2="84" y2="72" stroke="#475569" stroke-width="2.5"/>'
                '<line x1="61" y1="77" x2="79" y2="77" stroke="#475569" stroke-width="2"/>'
                '<line x1="66" y1="82" x2="74" y2="82" stroke="#475569" stroke-width="2"/>'
                '<text x="70" y="102" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_power_analyzer",
            name="Analyseur Réseau (cos φ/THD)",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
            description="Centrale de mesure qualité électrique (harmoniques THD, cos φ, déséquilibre).",
            default_unit="%",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="30" y="18" width="80" height="58" rx="5" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="38" y="25" width="64" height="30" rx="2" fill="#F1F5F9" stroke="#64748B"/>'
                '<path d="M42,40 Q50,28 58,40 T74,40 T90,40 T98,40" fill="none" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<text x="70" y="69" fill="#334155" font-size="8" font-weight="bold" text-anchor="middle">THD / COS φ</text>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_rail_substation",
            name="Sous-Station Traction Rail",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
            description="Alimentation caténaire 1500V DC / 25kV AC pour infrastructures ferroviaires et tramways.",
            default_unit="kV",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="26" y="26" width="88" height="48" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="15" y1="18" x2="125" y2="18" stroke="#475569" stroke-width="2.5"/>'
                '<line x1="70" y1="18" x2="70" y2="26" stroke="#475569" stroke-width="2.5"/>'
                '<text x="70" y="54" fill="#0F172A" font-size="10" font-weight="bold" text-anchor="middle">TRACTION</text>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="elec_mcs_truck_charger",
            name="Borne Poids Lourds (MCS)",
            family="electricity",
            family_label=FAMILY_LABELS["electricity"],
            description="Station Megawatt Charging System haute puissance pour flottes poids lourds & bus électriques.",
            default_unit="kW",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="28" y="16" width="54" height="64" rx="5" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<text x="55" y="42" fill="#0F172A" font-size="11" font-weight="bold" text-anchor="middle">MCS</text>'
                '<polygon points="57,48 48,60 55,60 52,72 62,58 55,58" [attr.fill]="statusColor"/>'
                '<path d="M82,34 L106,34 L106,68 L96,68" fill="none" stroke="#475569" stroke-width="3" stroke-linecap="round"/>'
                '<text x="70" y="102" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),

        # =====================================================================
        # 3. CVC, GTB & THERMIQUE (DIN 1946) - 10 composants
        # =====================================================================
        SvgComponentSpec(
            id="hvac_fan",
            name="Ventilateur / Extracteur",
            family="hvac",
            family_label=FAMILY_LABELS["hvac"],
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
            family_label=FAMILY_LABELS["hvac"],
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
            family_label=FAMILY_LABELS["hvac"],
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
            family_label=FAMILY_LABELS["hvac"],
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
            family_label=FAMILY_LABELS["hvac"],
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
            family_label=FAMILY_LABELS["hvac"],
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
            family_label=FAMILY_LABELS["hvac"],
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
            family_label=FAMILY_LABELS["hvac"],
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
        SvgComponentSpec(
            id="hvac_ahu_complete",
            name="CTA Double Flux Complète",
            family="hvac",
            family_label=FAMILY_LABELS["hvac"],
            description="Caisson Centrale de Traitement d'Air double flux avec récupérateur rotatif intégré.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="16" y="20" width="108" height="56" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="16" y1="48" x2="124" y2="48" stroke="#64748B" stroke-width="1.5"/>'
                '<ellipse cx="70" cy="48" rx="10" ry="22" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<circle cx="38" cy="34" r="7" fill="none" stroke="#475569" stroke-width="1.5"/>'
                '<circle cx="102" cy="62" r="7" fill="none" stroke="#475569" stroke-width="1.5"/>'
                '<text x="70" y="99" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="hvac_plate_exchanger",
            name="Échangeur à Plaques",
            family="hvac",
            family_label=FAMILY_LABELS["hvac"],
            description="Échangeur thermique à plaques brasées avec suivi Delta T primaire/secondaire.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="34" y="18" width="72" height="58" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="48" y1="24" x2="48" y2="70" stroke="#475569" stroke-width="2"/>'
                '<line x1="60" y1="24" x2="60" y2="70" stroke="#475569" stroke-width="2"/>'
                '<line x1="72" y1="24" x2="72" y2="70" stroke="#475569" stroke-width="2"/>'
                '<line x1="84" y1="24" x2="84" y2="70" stroke="#475569" stroke-width="2"/>'
                '<line x1="96" y1="24" x2="96" y2="70" stroke="#475569" stroke-width="2"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),

        # =====================================================================
        # 4. PROCESS INDUSTRIEL, FROID, PHARMA & HYDROGÈNE (18 composants)
        # =====================================================================
        SvgComponentSpec(
            id="proc_valve_2way",
            name="Vanne Motorisée 2 Voies",
            family="process",
            family_label=FAMILY_LABELS["process"],
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
            family_label=FAMILY_LABELS["process"],
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
            family_label=FAMILY_LABELS["process"],
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
            family_label=FAMILY_LABELS["process"],
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
            family_label=FAMILY_LABELS["process"],
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
            family_label=FAMILY_LABELS["process"],
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
            family_label=FAMILY_LABELS["process"],
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
            family_label=FAMILY_LABELS["process"],
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
        SvgComponentSpec(
            id="proc_screw_compressor",
            name="Compresseur à Vis Air",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Symbole ISO 10628 de compresseur industriel avec pression de refoulement.",
            default_unit="bar",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="14" y1="48" x2="126" y2="48" stroke="#64748B" stroke-width="4"/>'
                '<circle cx="70" cy="48" r="24" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="54" y1="32" x2="89" y2="40" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<line x1="54" y1="64" x2="89" y2="56" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<text x="70" y="99" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_chiller",
            name="Groupe Froid / Chiller",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Production d'eau glacée industrielle / Data Center avec température départ.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="20" y="20" width="100" height="56" rx="5" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="48" y1="30" x2="48" y2="66" stroke="#475569" stroke-width="2"/>'
                '<line x1="34" y1="48" x2="62" y2="48" stroke="#475569" stroke-width="2"/>'
                '<line x1="38" y1="38" x2="58" y2="58" stroke="#475569" stroke-width="1.5"/>'
                '<line x1="58" y1="38" x2="38" y2="58" stroke="#475569" stroke-width="1.5"/>'
                '<text x="92" y="52" fill="#0F172A" font-size="10" font-weight="bold" text-anchor="middle">CHILLER</text>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_cold_room_evap",
            name="Évaporateur Chambre Froide",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Aérofrigorifère de chambre froide positive/négative agroalimentaire.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="22" y="24" width="96" height="44" rx="5" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<circle cx="48" cy="46" r="12" fill="#F1F5F9" stroke="#475569" stroke-width="2"/>'
                '<circle cx="92" cy="46" r="12" fill="#F1F5F9" stroke="#475569" stroke-width="2"/>'
                '<text x="70" y="99" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_autoclave",
            name="Autoclave / Pasteurisateur",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Enceinte de stérilisation batch pharma / agroalimentaire sous pression.",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="24" y="24" width="92" height="50" rx="18" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="42" y1="24" x2="42" y2="74" stroke="#64748B" stroke-width="2"/>'
                '<line x1="98" y1="24" x2="98" y2="74" stroke="#64748B" stroke-width="2"/>'
                '<text x="70" y="53" fill="#0F172A" font-size="9.5" font-weight="bold" text-anchor="middle">BATCH</text>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_robot_6axis",
            name="Robot Industriel 6 Axes",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Bras robotisé d'atelier d'assemblage ou palettisation (cadence / couple).",
            default_unit="cyc/h",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="44" y="70" width="52" height="10" rx="2" fill="#64748B"/>'
                '<polyline points="70,70 50,46 84,26 102,38" fill="none" [attr.stroke]="statusColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
                '<circle cx="70" cy="70" r="5" fill="#0F172A"/>'
                '<circle cx="50" cy="46" r="5" fill="#0F172A"/>'
                '<circle cx="84" cy="26" r="5" fill="#0F172A"/>'
                '<text x="70" y="102" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_silo_hopper",
            name="Silo / Trémie Stockage",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Silo de stockage vrac / pulvérulents avec niveau proportionnel.",
            default_unit="%",
            dynamic_behavior="level",
            svg_body=(
                '<polygon points="40,16 100,16 100,56 78,82 62,82 40,56" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="43" y="40" [attr.y]="80 - (fillPct * 0.62)" width="54" height="40" [attr.height]="fillPct * 0.62" [attr.fill]="statusColor" opacity="0.35"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_check_valve",
            name="Clapet Anti-Retour",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Clapet anti-retour ISO 10628 protégeant les pompes contre le retour de flux.",
            default_unit="bar",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="15" y1="48" x2="125" y2="48" stroke="#64748B" stroke-width="5"/>'
                '<polygon points="50,34 86,48 50,62" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="86" y1="32" x2="86" y2="64" [attr.stroke]="statusColor" stroke-width="3.5"/>'
                '<text x="70" y="99" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_air_dryer_filter",
            name="Sécheur / Filtre Air",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Traitement d'air comprimé (point de rosée ou perte de charge filtre ΔP).",
            default_unit="°C",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="44" y="16" width="52" height="64" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="44" y1="48" x2="96" y2="48" stroke="#475569" stroke-width="2" stroke-dasharray="4 3"/>'
                '<text x="70" y="38" fill="#0F172A" font-size="9" font-weight="bold" text-anchor="middle">FILTRE</text>'
                '<text x="70" y="101" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_h2_storage_hp",
            name="Stockage Hydrogène HP",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Rack de bouteilles H2 haute pression (350 / 700 bar) pour mobilité verte.",
            default_unit="bar",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="28" y="20" width="22" height="58" rx="10" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<rect x="59" y="20" width="22" height="58" rx="10" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<rect x="90" y="20" width="22" height="58" rx="10" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<text x="70" y="54" fill="#0F172A" font-size="11" font-weight="bold" text-anchor="middle">H2</text>'
                '<text x="70" y="101" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="proc_h2_dispenser",
            name="Station Avitaillement H2",
            family="process",
            family_label=FAMILY_LABELS["process"],
            description="Distributeur hydrogène (Hydrogen Refueling Station) avec masse délivrée.",
            default_unit="kg",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="42" y="14" width="56" height="68" rx="6" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="50" y="24" width="40" height="20" rx="2" fill="#F1F5F9" stroke="#64748B"/>'
                '<text x="70" y="38" fill="#0F172A" font-size="10" font-weight="bold" text-anchor="middle">H2 HRS</text>'
                '<text x="70" y="66" fill="#334155" font-size="9" font-weight="bold" text-anchor="middle">700 bar</text>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),

        # =====================================================================
        # 5. EAU, ASSAINISSEMENT STEP & RÉSEAUX DE CHALEUR (6 composants)
        # =====================================================================
        SvgComponentSpec(
            id="water_bar_screen",
            name="Dégrilleur Automatique STEP",
            family="water_rcu",
            family_label=FAMILY_LABELS["water_rcu"],
            description="Prétraitement eaux usées avec surveillance perte de charge amont/aval.",
            default_unit="cm",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="20" y="42" width="100" height="36" fill="#CBD5E1" stroke="#64748B" stroke-width="2"/>'
                '<line x1="56" y1="20" x2="76" y2="78" [attr.stroke]="statusColor" stroke-width="3"/>'
                '<line x1="66" y1="20" x2="86" y2="78" [attr.stroke]="statusColor" stroke-width="3"/>'
                '<line x1="76" y1="20" x2="96" y2="78" [attr.stroke]="statusColor" stroke-width="3"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="water_aeration_basin",
            name="Bassin d'Aération STEP",
            family="water_rcu",
            family_label=FAMILY_LABELS["water_rcu"],
            description="Traitement biologique boues activées avec suivi oxygène dissous (mg/L).",
            default_unit="mg/L",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="18" y="34" width="104" height="44" rx="4" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="20" y="48" width="100" height="28" fill="#CBD5E1"/>'
                '<circle cx="44" cy="60" r="3" fill="#475569"/>'
                '<circle cx="58" cy="54" r="2.5" fill="#475569"/>'
                '<circle cx="74" cy="62" r="3.5" fill="#475569"/>'
                '<circle cx="94" cy="56" r="3" fill="#475569"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="water_clarifier",
            name="Clarificateur / Décanteur",
            family="water_rcu",
            family_label=FAMILY_LABELS["water_rcu"],
            description="Ouvrage circulaire de décantation secondaire avec pont racleur (turbidité NTU).",
            default_unit="NTU",
            dynamic_behavior="value",
            svg_body=(
                '<circle cx="70" cy="48" r="30" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<circle cx="70" cy="48" r="22" fill="#CBD5E1" opacity="0.6"/>'
                '<line x1="70" y1="48" x2="98" y2="48" stroke="#0F172A" stroke-width="3"/>'
                '<circle cx="70" cy="48" r="5" fill="#475569"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="water_dosing_pump",
            name="Pompe Doseuse Réactif",
            family="water_rcu",
            family_label=FAMILY_LABELS["water_rcu"],
            description="Injection de chlorure ferrique / polymère / chlore en station de traitement.",
            default_unit="L/h",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="36" y="28" width="44" height="44" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polygon points="80,38 106,50 80,62" [attr.fill]="statusColor"/>'
                '<text x="58" y="54" fill="#0F172A" font-size="9" font-weight="bold" text-anchor="middle">DOS</text>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="water_penstock_gate",
            name="Vanne Murale / Batardeau",
            family="water_rcu",
            family_label=FAMILY_LABELS["water_rcu"],
            description="Vanne de régulation de canal ou bassin d'orage (% d'ouverture).",
            default_unit="%",
            dynamic_behavior="level",
            svg_body=(
                '<rect x="44" y="24" width="52" height="56" fill="#F1F5F9" stroke="#64748B" stroke-width="2.5"/>'
                '<rect x="48" y="40" [attr.y]="80 - (fillPct * 0.62)" width="44" height="40" [attr.height]="fillPct * 0.62" [attr.fill]="statusColor" opacity="0.55"/>'
                '<line x1="70" y1="10" x2="70" y2="40" stroke="#0F172A" stroke-width="3"/>'
                '<rect x="56" y="10" width="28" height="8" rx="2" fill="#475569"/>'
                '<text x="70" y="102" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="water_rcu_substation",
            name="Sous-Station Chaleur (RCU)",
            family="water_rcu",
            family_label=FAMILY_LABELS["water_rcu"],
            description="Sous-station d'échange Réseau de Chaleur Urbain (puissance thermique livrée).",
            default_unit="kW",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="24" y="20" width="92" height="56" rx="5" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polyline points="36,34 52,34 52,62 68,62" fill="none" stroke="#475569" stroke-width="2.5"/>'
                '<polyline points="104,34 88,34 88,62 72,62" fill="none" stroke="#0F172A" stroke-width="2.5"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),

        # =====================================================================
        # 6. INFRASTRUCTURES, TUNNELS, SÉCURITÉ & SMART CITY (12 composants)
        # =====================================================================
        SvgComponentSpec(
            id="infra_street_light",
            name="Mât Éclairage Public LED",
            family="infrastructure",
            family_label=FAMILY_LABELS["infrastructure"],
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
            family_label=FAMILY_LABELS["infrastructure"],
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
            family_label=FAMILY_LABELS["infrastructure"],
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
            family_label=FAMILY_LABELS["infrastructure"],
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
            family_label=FAMILY_LABELS["infrastructure"],
            description="Armoire télécoms / Data Center Edge avec température interne et 48V DC.",
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
            family_label=FAMILY_LABELS["infrastructure"],
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
        SvgComponentSpec(
            id="infra_access_gate",
            name="Portique Contrôle d'Accès",
            family="infrastructure",
            family_label=FAMILY_LABELS["infrastructure"],
            description="Tourniquet / portique RFID de sûreté tertiaire et comptage d'occupation.",
            default_unit="pers",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="28" y="34" width="16" height="44" rx="2" fill="#CBD5E1" stroke="#475569" stroke-width="2"/>'
                '<rect x="96" y="34" width="16" height="44" rx="2" fill="#CBD5E1" stroke="#475569" stroke-width="2"/>'
                '<line x1="44" y1="50" x2="96" y2="50" [attr.stroke]="statusColor" stroke-width="4" stroke-dasharray="6 4"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_traffic_camera",
            name="Caméra / Comptage Trafic",
            family="infrastructure",
            family_label=FAMILY_LABELS["infrastructure"],
            description="Capteur optique / vidéoprotection de flux routiers et mobilités douces.",
            default_unit="véh/h",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="28" y="28" width="60" height="34" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<polygon points="88,36 112,26 112,64 88,54" fill="#94A3B8" stroke="#475569" stroke-width="2"/>'
                '<circle cx="52" cy="45" r="7" fill="#F1F5F9" stroke="#475569" stroke-width="2"/>'
                '<text x="70" y="99" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_vms_sign",
            name="Panneau PMV Tunnel/Route",
            family="infrastructure",
            family_label=FAMILY_LABELS["infrastructure"],
            description="Panneau à Messages Variables autoroutier ou tunnel routier (GTC Trafic).",
            default_unit="km/h",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="16" y="18" width="108" height="46" rx="4" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="24" y="26" width="92" height="30" rx="2" fill="#F1F5F9" stroke="#64748B"/>'
                '<text x="70" y="45" fill="#0F172A" font-size="10" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
                '<line x1="42" y1="64" x2="42" y2="82" stroke="#475569" stroke-width="3.5"/>'
                '<line x1="98" y1="64" x2="98" y2="82" stroke="#475569" stroke-width="3.5"/>'
                '<text x="70" y="102" fill="#334155" font-size="9" font-weight="bold" text-anchor="middle">PMV GTC</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_tunnel_jetfan",
            name="Ventilateur Jet-Fan Tunnel",
            family="infrastructure",
            family_label=FAMILY_LABELS["infrastructure"],
            description="Accélérateur de désenfumage et ventilation longitudinale de tunnel routier.",
            default_unit="m/s",
            dynamic_behavior="value",
            svg_body=(
                '<rect x="26" y="28" width="88" height="38" rx="14" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<line x1="46" y1="28" x2="46" y2="66" stroke="#64748B" stroke-width="2"/>'
                '<line x1="94" y1="28" x2="94" y2="66" stroke="#64748B" stroke-width="2"/>'
                '<polygon points="62,38 82,47 62,56" [attr.fill]="statusColor"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_smart_waste_bin",
            name="Conteneur PAV Déchets",
            family="infrastructure",
            family_label=FAMILY_LABELS["infrastructure"],
            description="Point d'Apport Volontaire enterré avec capteur ultrason de remplissage.",
            default_unit="%",
            dynamic_behavior="level",
            svg_body=(
                '<rect x="38" y="22" width="64" height="60" rx="4" fill="#F1F5F9" [attr.stroke]="statusColor" stroke-width="2.5"/>'
                '<rect x="42" y="40" [attr.y]="80 - (fillPct * 0.62)" width="56" height="40" [attr.height]="fillPct * 0.62" [attr.fill]="statusColor" opacity="0.45"/>'
                '<rect x="32" y="14" width="76" height="8" rx="2" fill="#475569"/>'
                '<text x="70" y="103" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
        SvgComponentSpec(
            id="infra_smart_irrigation",
            name="Borne Arrosage Intelligent",
            family="infrastructure",
            family_label=FAMILY_LABELS["infrastructure"],
            description="Électrovanne d'arrosage espaces verts pilotée par tensiomètre sol.",
            default_unit="%",
            dynamic_behavior="value",
            svg_body=(
                '<line x1="20" y1="68" x2="120" y2="68" stroke="#64748B" stroke-width="3"/>'
                '<rect x="62" y="44" width="16" height="24" rx="2" fill="#CBD5E1" [attr.stroke]="statusColor" stroke-width="2"/>'
                '<path d="M70,44 Q50,24 38,38" fill="none" [attr.stroke]="statusColor" stroke-width="2" stroke-dasharray="3 2"/>'
                '<path d="M70,44 Q90,24 102,38" fill="none" [attr.stroke]="statusColor" stroke-width="2" stroke-dasharray="3 2"/>'
                '<text x="70" y="100" fill="#0F172A" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">{{valDisplay}}</text>'
            ),
        ),
    ]


def _build_widget_type_dict(spec: SvgComponentSpec, bundle_alias: str = "scada_industrial_suite") -> Dict[str, Any]:
    """Builds an ISA-101 ThingsBoard 4.3 widgetType with redundant Shape+Color alarm indicator."""
    template_html = (
        '<div class="isa101-widget-card" [class.isa-alarm-pulse]="alarmLevel === \'CRIT\'">'
        '  <div class="isa101-header-row">'
        '    <span class="isa101-widget-title">{{title}}</span>'
        '    <span class="isa101-alarm-shape isa-warn" *ngIf="alarmLevel === \'WARN\'" title="Avertissement">▲</span>'
        '    <span class="isa101-alarm-shape isa-crit" *ngIf="alarmLevel === \'CRIT\'" title="Alarme Critique">■ !</span>'
        '  </div>'
        '  <svg viewBox="0 0 140 110" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">'
        f'    {spec.svg_body}'
        '  </svg>'
        '</div>'
    )

    template_css = (
        f".isa101-widget-card {{ width:100%; height:100%; background:{ISA101_BG}; border-radius:8px; "
        f"border:1px solid {ISA101_BORDER}; display:flex; flex-direction:column; align-items:center; "
        "justify-content:space-between; padding:6px 8px; box-sizing:border-box; font-family:sans-serif; }\n"
        ".isa101-header-row { display:flex; align-items:center; justify-content:space-between; width:100%; gap:4px; }\n"
        f".isa101-widget-title {{ font-size:11px; font-weight:700; color:{ISA101_TEXT_TITLE}; text-align:left; "
        "white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; }\n"
        ".isa101-alarm-shape { font-size:10px; font-weight:800; padding:1px 5px; border-radius:3px; color:#FFFFFF; }\n"
        f".isa-warn {{ background:{ISA101_WARN_COLOR}; }}\n"
        f".isa-crit {{ background:{ISA101_CRIT_COLOR}; }}\n"
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
    self.ctx.$scope.alarmLevel = "NORMAL";
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
            var lvl = "NORMAL";
            if (s.critThreshold !== undefined && s.critThreshold !== null && s.critThreshold !== "" && num >= Number(s.critThreshold)) {
                c = "#DC2626";
                lvl = "CRIT";
            } else if (s.warnThreshold !== undefined && s.warnThreshold !== null && s.warnThreshold !== "" && num >= Number(s.warnThreshold)) {
                c = "#D97706";
                lvl = "WARN";
            }
            self.ctx.$scope.statusColor = c;
            self.ctx.$scope.alarmLevel = lvl;
            self.ctx.$scope.isAlarm = (lvl === "CRIT");
        } else {
            self.ctx.$scope.valDisplay = String(val);
            var isFault = (val === true || val === "true" || val === "ALARM" || val === "FAULT");
            self.ctx.$scope.statusColor = isFault ? "#DC2626" : "__COLOR__";
            self.ctx.$scope.alarmLevel = isFault ? "CRIT" : "NORMAL";
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
                "warnThreshold": {"title": "Seuil Avertissement ▲ Ambre (>=)", "type": "number"},
                "critThreshold": {"title": "Seuil Critique ■ ! Rouge (>=)", "type": "number"},
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


def generate_thingsboard_widget_bundle(family: Optional[str] = None) -> Dict[str, Any]:
    """Generates an ISA-101 ThingsBoard 4.3 Widgets Bundle JSON (all 70 widgets or filtered by family)."""
    catalog = get_svg_components_catalog()
    if family:
        if family not in FAMILY_LABELS:
            raise ValueError(f"Famille '{family}' inconnue. Valeurs autorisées : {sorted(FAMILY_LABELS.keys())}")
        catalog = [c for c in catalog if c.family == family]
        bundle_alias = f"scada_isa101_{family}"
        title = f"SCADA ISA-101 • {FAMILY_LABELS[family]} ({len(catalog)} Composants)"
    else:
        bundle_alias = "scada_industrial_suite"
        title = f"SCADA ISA-101 Industriel & Énergie ({len(catalog)} Composants)"

    return {
        "widgetsBundle": {
            "alias": bundle_alias,
            "title": title,
            "image": None,
            "description": "Bibliothèque conforme ANSI/ISA-101.01 (fond gris mat #E5E7EB, gris acier au nominal, codage redondant Forme+Couleur sur alarme).",
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
