"""
Bid Deliverables & Technical Memory Exporter.

Generates ready-to-use RFP / technical proposal documents directly from the
currently configured simulator devices and variables:
1. IO List CSV (UTF-8 with BOM, semicolon-delimited for French Microsoft Excel).
2. Technical Architecture Dossier in Markdown (Mermaid flux diagram, device inventory,
   ROI/regulatory KPIs, and IoT sizing annex).
"""

import csv
import io
from datetime import datetime, timezone
from typing import List
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType, DataType, SimMode
from app.core.sizing_calculator import SizingResult
from app.transports.modbus_server import build_modbus_register_map


def _suggest_alarm_threshold(var: VariableConfig) -> str:
    """Suggests an indicative ThingsBoard alarm rule based on variable bounds."""
    if var.var_type != VariableType.TELEMETRY:
        return "Contrôle état (SHARED_SCOPE)"
    if var.data_type not in (DataType.FLOAT, DataType.INTEGER):
        return "Changement d'état / Défaut"
    if var.sim_mode == SimMode.INTEGRATOR:
        return "Index monotone (alerte si gel/baisse)"
    if var.math_config and var.math_config.min_val is not None and var.math_config.max_val is not None:
        unit = f" {var.unit}" if var.unit else ""
        return f"Hors plage [{var.math_config.min_val}; {var.math_config.max_val}]{unit}"
    return "Dérive / Spike / Timeout"


def generate_io_list_csv(devices: List[DeviceConfig], variables: List[VariableConfig]) -> str:
    """Generates a French Excel-friendly CSV (UTF-8 BOM, ';' delimiter) listing all IO points + Modbus map."""
    dev_map = {d.id: d for d in devices}
    modbus_lookup = build_modbus_register_map(devices, variables)["by_variable_id"]
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

    writer.writerow([
        "Équipement",
        "ID Équipement",
        "Protocole",
        "Variable ID",
        "Libellé",
        "Nature",
        "Type Donnée",
        "Unité",
        "Mode Simulation",
        "Plage Min",
        "Plage Max",
        "Cadence (s)",
        "Seuil / Règle Alarme Recommandée",
        "Registre Modbus TCP",
    ])

    for v in variables:
        dev = dev_map.get(v.device_id)
        dev_name = dev.name if dev else (v.device_id or "Global")
        proto = (dev.protocol.value.upper() if dev and hasattr(dev.protocol, "value") else "MQTT")
        nature = "Télémétrie" if v.var_type == VariableType.TELEMETRY else "Attribut Pilotable"
        min_val = v.math_config.min_val if v.math_config else ""
        max_val = v.math_config.max_val if v.math_config else ""
        if v.sim_mode in (SimMode.DERIVED, SimMode.INTEGRATOR, SimMode.CONSTANT):
            min_val = ""
            max_val = ""
        mb_entry = modbus_lookup.get(v.id)
        mb_ref = f"Unit {mb_entry['unit_id']} • {mb_entry['modbus_ref']}" if mb_entry else "-"

        writer.writerow([
            dev_name,
            v.device_id,
            proto,
            v.id,
            v.name,
            nature,
            v.data_type.value if hasattr(v.data_type, "value") else str(v.data_type),
            v.unit or "-",
            v.sim_mode.value if hasattr(v.sim_mode, "value") else str(v.sim_mode),
            min_val,
            max_val,
            v.publish_interval,
            _suggest_alarm_threshold(v),
            mb_ref,
        ])

    return output.getvalue()


def generate_architecture_dossier_md(
    devices: List[DeviceConfig],
    variables: List[VariableConfig],
    sizing: SizingResult,
) -> str:
    """Generates a structured Markdown technical dossier ready for RFP responses."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    vars_by_dev = {}
    for v in variables:
        vars_by_dev.setdefault(v.device_id, []).append(v)

    lines = [
        f"# Dossier Technique d'Architecture IoT & Hypervision",
        f"",
        f"*Généré le {now_str} — Support Avant-Vente & Mémoire Technique*",
        f"",
        f"## 1. Architecture de Collecte & Flux de Données",
        f"",
        f"```mermaid",
        f"flowchart LR",
        f'    TERRAIN["Équipements Terrain ({len(devices)} unités)"] -->|"MQTT / HTTP TLS"| BROKER["Broker / Collecteur IoT"]',
        f'    BROKER -->|"Ingestion Temps Réel"| TB["Plateforme ThingsBoard 4.3"]',
        f'    TB -->|"Rule Chains & Alarmes"| HYPER["Hypervision SCADA & KPIs"]',
        f'    HYPER -.->|"Pilotage SHARED_SCOPE"| TERRAIN',
        f"```",
        f"",
        f"## 2. Inventaire des Équipements & Points de Mesure",
        f"",
        f"| Équipement | Identifiant | Protocole | Cadence | Télémétries | Attributs |",
        f"| :--- | :--- | :---: | :---: | :---: | :---: |",
    ]

    for d in devices:
        d_vars = vars_by_dev.get(d.id, [])
        t_count = sum(1 for v in d_vars if v.var_type == VariableType.TELEMETRY)
        a_count = sum(1 for v in d_vars if v.var_type == VariableType.ATTRIBUTE)
        proto = d.protocol.value.upper() if hasattr(d.protocol, "value") else str(d.protocol).upper()
        cadence = f"{d.publish_interval}s" if d.publish_interval else "Par variable"
        lines.append(f"| **{d.name}** | `{d.id}` | {proto} | {cadence} | {t_count} | {a_count} |")

    roi_vars = [
        v for v in variables
        if any(k in v.id.lower() for k in ("ipe", "co2", "cout", "economie", "energie", "kwh", "mwh"))
    ]
    if roi_vars:
        lines.extend([
            f"",
            f"## 3. Indicateurs de Performance Énergétique (IPE / ROI / Décret BACS)",
            f"",
            f"| Indicateur | Variable | Unité | Mode de Calcul |",
            f"| :--- | :--- | :---: | :--- |",
        ])
        for rv in roi_vars[:15]:
            mode_desc = rv.derived_config.formula if rv.sim_mode == SimMode.DERIVED and rv.derived_config else rv.sim_mode.value
            lines.append(f"| {rv.name} | `{rv.id}` | {rv.unit or '-'} | `{mode_desc}` |")

    lines.extend([
        f"",
        f"## 4. Dimensionnement Infrastructure & Réseau",
        f"",
        sizing.markdown_report,
    ])

    return "\n".join(lines)
