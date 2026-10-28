#!/usr/bin/env python3
"""
IoT Equipment Preset Full Package Builder
========================================
Takes a raw equipment preset definition and bundles it into an autonomous,
100% compliant export package including:
- Equipment definition model
- ThingsBoard 4.3 JSON dashboard descriptor (animated SCADA P&ID vector synoptic, gauges, switches)
- ThingsBoard bulk CSV import template
- Instantiation specifications
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List


def generate_svg_synoptic(preset_name: str, variables: List[Dict[str, Any]]) -> str:
    """Generates an animated industrial SVG SCADA synoptic with live `${key:1}` data tags.

    Args:
        preset_name: Human-readable equipment preset name.
        variables: List of telemetry and attribute variable dictionaries.

    Returns:
        Formatted HTML wrapper string containing embedded SVG with CSS animations.
    """
    telemetries = [v for v in variables if v.get("var_type") == "telemetry"]
    
    # Build telemetry measurement tags
    tags_svg = []
    y_pos = 120
    for idx, t in enumerate(telemetries[:6]):
        k = t.get("id", "")
        unit = t.get("unit", "")
        name = t.get("name", k)
        tags_svg.append(f"""
        <g transform="translate(480, {y_pos})">
          <rect width="180" height="36" rx="6" fill="#0B132B" stroke="#38BDF8" stroke-width="1.2"/>
          <circle cx="16" cy="18" r="4" fill="#38BDF8"/>
          <text x="28" y="16" fill="#94A3B8" font-size="9" font-family="sans-serif">{name[:22]}</text>
          <text x="28" y="29" fill="#38BDF8" font-size="12" font-weight="bold" font-family="monospace">${{{k}:1}} {unit}</text>
        </g>
        """)
        y_pos += 44

    tags_joined = "\n".join(tags_svg)

    return f"""
    <div style="background:#0F172A; border-radius:12px; padding:18px; color:#F8FAFC; font-family:sans-serif; position:relative; overflow:hidden; border:1px solid #1E293B;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid #334155; pb:8px;">
        <div style="font-size:14px; font-weight:700; color:#38BDF8; letter-spacing:0.5px;">SYNOPTIQUE INDUSTRIEL SCADA</div>
        <div style="font-size:11px; color:#94A3B8;">Équipement : <strong style="color:#FFF;">{preset_name}</strong></div>
      </div>
      <svg viewBox="0 0 720 380" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <style>
            @keyframes pipeFlow {{
              0% {{ stroke-dashoffset: 40; }}
              100% {{ stroke-dashoffset: 0; }}
            }}
            .scada-flow {{
              stroke-dasharray: 8, 4;
              animation: pipeFlow 1.2s linear infinite;
            }}
          </style>
          <linearGradient id="eqGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#1E293B"/>
            <stop offset="100%" stop-color="#0F172A"/>
          </linearGradient>
        </defs>

        <!-- Process piping with animated fluid flow -->
        <path d="M 60 190 L 220 190 L 220 280 L 450 280 L 450 190 L 470 190" fill="none" stroke="#475569" stroke-width="8" stroke-linecap="round"/>
        <path d="M 60 190 L 220 190 L 220 280 L 450 280 L 450 190 L 470 190" fill="none" stroke="#38BDF8" stroke-width="3" class="scada-flow"/>

        <!-- Process tank and machine core -->
        <rect x="180" y="90" width="220" height="200" rx="14" fill="url(#eqGrad)" stroke="#0284C7" stroke-width="2.5"/>
        <text x="290" y="125" fill="#38BDF8" font-size="13" font-weight="800" text-anchor="middle" letter-spacing="1">UNITÉ DE PROCESS</text>
        <circle cx="290" cy="195" r="45" fill="#182234" stroke="#0284C7" stroke-width="1.5"/>
        <text x="290" y="200" fill="#94A3B8" font-size="10" font-family="monospace" text-anchor="middle">ACTIVE</text>

        <!-- Live ThingsBoard telemetry badges -->
        {tags_joined}
      </svg>
    </div>
    """


def generate_tb43_dashboard(preset: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a complete ThingsBoard 4.3 JSON dashboard compatible with Community and Professional Editions.

    Args:
        preset: Equipment preset dictionary.

    Returns:
        Structured ThingsBoard dashboard dictionary.
    """
    alias_id = str(uuid.uuid4())
    p_name = preset.get("name", "Équipement")
    p_id = preset.get("id", "equip")
    variables = preset.get("variables", [])

    widgets: Dict[str, Any] = {}
    layout_widgets: Dict[str, Any] = {}
    current_row = 0

    # 1. Widget Header HTML Card
    header_id = str(uuid.uuid4())
    widgets[header_id] = {
        "typeFullFqn": "system.cards.html_card",
        "isSystemType": True,
        "bundleAlias": "cards",
        "typeAlias": "html_card",
        "type": "static",
        "title": f"Informations - {p_name}",
        "sizeX": 24,
        "sizeY": 2,
        "config": {
            "datasources": [],
            "settings": {
                "cardHtml": f"<div style='padding:12px 18px; font-size:16px; font-weight:700; color:#0F172A; background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px;'>IoT Data Simulator • {p_name} <span style='font-size:12px; color:#64748B; font-weight:normal; margin-left:12px;'>ID: {p_id} | Authentification: Jeton Sécurisé</span></div>",
                "html": f"<div style='padding:12px 18px; font-size:16px; font-weight:700; color:#0F172A; background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px;'>IoT Data Simulator • {p_name} <span style='font-size:12px; color:#64748B; font-weight:normal; margin-left:12px;'>ID: {p_id} | Authentification: Jeton Sécurisé</span></div>"
            }
        }
    }
    layout_widgets[header_id] = {"sizeX": 24, "sizeY": 2, "row": current_row, "col": 0}
    current_row += 2

    # 2. Synoptique SCADA vectoriel P&ID
    scada_id = str(uuid.uuid4())
    scada_html = generate_svg_synoptic(p_name, variables)
    
    # DataKeys avec label == clean_key (CRITIQUE pour ThingsBoard 4.3)
    data_keys = []
    for v in variables:
        if v.get("var_type") == "telemetry":
            vk = v.get("id", "")
            data_keys.append({
                "name": vk,
                "label": vk,
                "type": "timeseries",
                "color": "#38BDF8",
                "settings": {}
            })

    widgets[scada_id] = {
        "typeFullFqn": "system.cards.html_value_card",
        "isSystemType": True,
        "bundleAlias": "cards",
        "typeAlias": "html_value_card",
        "type": "latest",
        "title": f"Synoptique SCADA - {p_name}",
        "sizeX": 16,
        "sizeY": 8,
        "config": {
            "useDashboardTimewindow": True,
            "datasources": [{
                "type": "entity",
                "entityAliasId": alias_id,
                "dataKeys": data_keys
            }],
            "settings": {
                "cardHtml": scada_html,
                "html": scada_html,
                "cardCss": "",
                "css": ""
            }
        }
    }
    layout_widgets[scada_id] = {"sizeX": 16, "sizeY": 8, "row": current_row, "col": 0}

    # 3. Widgets de Contrôle Interactifs (Single Switch pour booléens)
    ctrl_col = 16
    ctrl_row = current_row
    attributes = [v for v in variables if v.get("var_type") == "attribute"]
    for attr in attributes[:4]:
        ctrl_id = str(uuid.uuid4())
        attr_k = attr.get("id", "")
        widgets[ctrl_id] = {
            "typeFullFqn": "system.single_switch",
            "isSystemType": True,
            "bundleAlias": "control_widgets",
            "typeAlias": "single_switch",
            "type": "rpc",
            "title": f"Pilotage - {attr.get('name', attr_k)}",
            "sizeX": 8,
            "sizeY": 2,
            "config": {
                "showTitle": True,
                "targetDevice": {"type": "entity", "entityAliasId": alias_id},
                "settings": {
                    "initialState": {
                        "action": "GET_ATTRIBUTE",
                        "getAttribute": {"scope": "SHARED_SCOPE", "key": attr_k}
                    },
                    "onUpdateState": {
                        "action": "SET_ATTRIBUTE",
                        "setAttribute": {"scope": "SHARED_SCOPE", "key": attr_k}
                    }
                }
            }
        }
        layout_widgets[ctrl_id] = {"sizeX": 8, "sizeY": 2, "row": ctrl_row, "col": ctrl_col}
        ctrl_row += 2

    current_row += 8

    # 4. Timeseries Chart
    chart_id = str(uuid.uuid4())
    widgets[chart_id] = {
        "typeFullFqn": "system.charts.basic_timeseries",
        "isSystemType": True,
        "bundleAlias": "charts",
        "typeAlias": "basic_timeseries",
        "type": "timeseries",
        "title": f"Télémétries Temps Réel - {p_name}",
        "sizeX": 24,
        "sizeY": 6,
        "config": {
            "datasources": [{
                "type": "entity",
                "entityAliasId": alias_id,
                "dataKeys": data_keys[:8]
            }],
            "settings": {}
        }
    }
    layout_widgets[chart_id] = {"sizeX": 24, "sizeY": 6, "row": current_row, "col": 0}

    return {
        "title": f"Supervision SCADA - {p_name}",
        "configuration": {
            "description": f"Tableau de bord de supervision généré pour le cas d'usage {p_name}",
            "entityAliases": {
                alias_id: {
                    "id": alias_id,
                    "alias": p_name,
                    "filter": {
                        "type": "singleEntity",
                        "resolveMultiple": False,
                        "singleEntity": {
                            "entityType": "DEVICE",
                            "id": "00000000-0000-0000-0000-000000000000"
                        }
                    }
                }
            },
            "widgets": widgets,
            "states": {
                "default": {
                    "name": f"Supervision SCADA - {p_name}",
                    "root": True,
                    "layouts": {
                        "main": {
                            "gridAppearance": {
                                "layoutDimension": {
                                    "type": "percentage",
                                    "percentage": 100
                                }
                            },
                            "widgets": layout_widgets
                        }
                    }
                }
            }
        }
    }

def build_package(preset: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble le package d'export exhaustif normalisé v2.1.0."""
    p_name = preset.get("name", "Équipement")
    p_id = preset.get("id", "equip")
    preset["is_custom"] = True

    dashboard_data = generate_tb43_dashboard(preset)

    csv_template = {
        "headers": "name,type,label,access_token",
        "sample_row": f"{p_name},default,{p_name},${{AUTO_GENERATED_TOKEN}}",
        "notes": "Fichier compatible avec l'outil d'import CSV d'appareils de ThingsBoard"
    }

    instantiation_spec = {
        "suggested_device_id_prefix": p_id,
        "default_name": p_name,
        "default_protocol": preset.get("default_protocol", "mqtt"),
        "default_platform": "thingsboard",
        "variables_count": len(preset.get("variables", [])),
        "recommended_publish_interval": 2.0
    }

    return {
        "schema_version": "2.1.0",
        "export_type": "single_preset",
        "export_date": datetime.now(timezone.utc).isoformat(),
        "generator": "IoT Data Simulator v2.2.0 (IoT Preset Architect)",
        "preset": preset,
        "dashboard_template": dashboard_data,
        "csv_template": csv_template,
        "instantiation_spec": instantiation_spec,
    }

def main():
    parser = argparse.ArgumentParser(description="Assembleur de package complet de cas d'usage pour IoT Data Simulator")
    parser.add_argument("--input", "-i", required=True, help="Chemin du fichier JSON de preset brut")
    parser.add_argument("--output", "-o", required=True, help="Chemin du fichier JSON de package de sortie")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Erreur : Fichier d'entrée introuvable '{args.input}'", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur de lecture JSON : {e}", file=sys.stderr)
        sys.exit(1)

    # Extraire preset si déjà emballé
    preset = data.get("preset", data) if isinstance(data, dict) else data

    package = build_package(preset)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2, ensure_ascii=False)

    print(f"✅ Package complet généré avec succès dans '{args.output}' !")
    print(f"📊 {len(preset.get('variables', []))} grandeurs, Dashboard ThingsBoard 4.3 et Template CSV inclus.")

if __name__ == "__main__":
    main()
