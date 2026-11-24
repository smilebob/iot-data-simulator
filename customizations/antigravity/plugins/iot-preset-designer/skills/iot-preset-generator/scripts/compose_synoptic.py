#!/usr/bin/env python3
"""
Composeur de Synoptiques SCADA ISA-101 pour l'Agent IA (iot-preset-designer).
Assemble des composants de la bibliothèque officielle des 70 SVG ISA-101
(references/svg_catalog_index.json) avec liaisons/tuyauteries et balises ${cle}
prêtes pour ThingsBoard 4.3 (html_value_card).
Zéro dépendance externe (Python 3 standard).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def load_catalog() -> Dict[str, Dict[str, Any]]:
    idx_path = Path(__file__).resolve().parent.parent / "references" / "svg_catalog_index.json"
    if not idx_path.exists():
        raise FileNotFoundError(f"Index SVG introuvable : {idx_path}")
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data}


def resolve_svg_body(svg_body: str, val_expr: str, title: str, color: str = "#475569") -> str:
    return (
        svg_body
        .replace("{{valDisplay}}", val_expr)
        .replace("{{title}}", title)
        .replace("{{statusColor}}", color)
        .replace('[attr.stroke]="statusColor"', f'stroke="{color}"')
        .replace('[attr.fill]="statusColor"', f'fill="{color}"')
        .replace('[attr.height]="fillPct * 0.62"', 'height="40"')
        .replace('[attr.y]="80 - (fillPct * 0.62)"', 'y="40"')
        .replace('[attr.y]="78 - (fillPct * 0.56)"', 'y="46"')
        .replace('[attr.x]="24 + (fillPct * 0.92)"', 'x="68"')
        .replace('[class.isa-alarm-pulse]="isAlarm"', "")
    )


def compose_synoptic_html(spec: Dict[str, Any]) -> str:
    """Construit le code HTML/SVG ISA-101 complet depuis un descripteur JSON."""
    catalog = load_catalog()
    title = spec.get("title", "SYNOPTIQUE SCADA ISA-101")
    width = int(spec.get("width", 760))
    height = int(spec.get("height", 360))
    pipes: List[Dict[str, Any]] = spec.get("pipes", [])
    nodes: List[Dict[str, Any]] = spec.get("components", [])

    pipe_svg = []
    for p in pipes:
        d = p.get("d", "")
        if d:
            pipe_svg.append(
                f'<path d="{d}" fill="none" stroke="#64748B" stroke-width="{p.get("width", 5)}" stroke-linecap="round" stroke-linejoin="round"/>'
            )

    comp_svg = []
    for n in nodes:
        cid = n["component_id"]
        if cid not in catalog:
            raise ValueError(f"Composant SVG inconnu : '{cid}'")
        item = catalog[cid]
        x = int(n.get("x", 0))
        y = int(n.get("y", 0))
        var_key = n["var_key"]
        unit = n.get("unit", item.get("default_unit", ""))
        decimals = int(n.get("decimals", 1))
        lbl = n.get("label", item["name"])
        val_expr = f"${{{var_key}:{decimals}}} {unit}".strip() if decimals >= 0 else f"${{{var_key}}} {unit}".strip()
        body = resolve_svg_body(item["svg_body"], val_expr, lbl, "#475569")
        comp_svg.append(
            f'<g transform="translate({x}, {y})">'
            f'<rect width="140" height="110" rx="6" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="1.2"/>'
            f'<text x="70" y="11" fill="#334155" font-size="8" font-weight="700" font-family="sans-serif" text-anchor="middle">{lbl[:22]}</text>'
            f'{body}'
            f'</g>'
        )

    return (
        '<div style="background:#E5E7EB; border-radius:10px; padding:14px; color:#0F172A; font-family:sans-serif; border:1px solid #CBD5E1;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #CBD5E1;">'
        f'<div style="font-size:13px; font-weight:700; color:#0F172A; text-transform:uppercase;">{title}</div>'
        f'<div style="font-size:11px; color:#475569; background:#F1F5F9; padding:3px 8px; border-radius:4px; border:1px solid #CBD5E1;">Norme ANSI/ISA-101.01</div>'
        '</div>'
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">'
        f'{"".join(pipe_svg)}'
        f'{"".join(comp_svg)}'
        '</svg>'
        '</div>'
    )


def main():
    parser = argparse.ArgumentParser(description="Assembleur de synoptique SCADA ISA-101")
    parser.add_argument("--list", action="store_true", help="Affiche les 70 composants SVG disponibles")
    parser.add_argument("--spec", "-s", help="Fichier JSON décrivant les composants et tuyauteries")
    parser.add_argument("--output", "-o", help="Fichier HTML de sortie (stdout si omis)")
    args = parser.parse_args()

    if args.list:
        cat = load_catalog()
        for cid, item in cat.items():
            print(f"{cid:26s} | {item['family']:18s} | {item['name']}")
        return

    if not args.spec:
        parser.print_help()
        sys.exit(1)

    spec_data = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    html = compose_synoptic_html(spec_data)
    if args.output:
        Path(args.output).write_text(html, encoding="utf-8")
        print(f"✅ Synoptique ISA-101 généré dans {args.output}")
    else:
        print(html)


if __name__ == "__main__":
    main()
