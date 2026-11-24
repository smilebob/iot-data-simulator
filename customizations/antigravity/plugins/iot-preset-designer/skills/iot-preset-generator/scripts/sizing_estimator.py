#!/usr/bin/env python3
"""
Calculateur autonome de dimensionnement IoT & ThingsBoard pour les mémoires techniques.
Prend un fichier preset JSON ou des paramètres directs (N équipements, cadence, rétention)
et produit une fiche technique de volumétrie prête à copier.
Zéro dépendance externe (Python 3 standard).
"""

import argparse
import json
import os
import sys

PROTOCOL_OVERHEAD = {"mqtt": 48, "http": 380, "coap": 24}


def estimate_sizing(
    device_count: int,
    vars_per_device: int,
    interval_sec: float,
    protocol: str = "mqtt",
    use_tls: bool = True,
    retention_years: int = 3,
) -> dict:
    proto = protocol.lower()
    overhead = PROTOCOL_OVERHEAD.get(proto, 48) + (64 if use_tls else 0)
    payload_bytes = max(16, 4 + vars_per_device * 22)
    packet_bytes = payload_bytes + overhead

    msgs_per_sec = device_count / max(0.1, interval_sec)
    msgs_per_day = int(round(msgs_per_sec * 86400))
    dps_per_day = msgs_per_day * vars_per_device
    bw_kbps = round(((msgs_per_sec * packet_bytes) * 8) / 1000.0, 2)
    monthly_gb = round(((msgs_per_sec * packet_bytes) * 86400 * 30) / (1024 ** 3), 3)

    raw_gb = round((dps_per_day * 365 * 48 * retention_years) / (1024 ** 3), 2)
    compressed_gb = round(raw_gb / 5.0, 2)

    if msgs_per_sec <= 50 and device_count <= 250:
        tier = "Compact (Mono-nœud) : 4 vCPU, 8 Go RAM, SSD 100 Go"
    elif msgs_per_sec <= 500 and device_count <= 2500:
        tier = "Standard Production : 8 vCPU, 16 Go RAM, SSD 250 Go"
    else:
        tier = "Haute Performance / Cluster : 16+ vCPU, 32+ Go RAM, SSD 500+ Go"

    return {
        "device_count": device_count,
        "vars_per_device": vars_per_device,
        "interval_sec": interval_sec,
        "protocol": proto.upper(),
        "msgs_per_sec": round(msgs_per_sec, 2),
        "msgs_per_day": msgs_per_day,
        "dps_per_day": dps_per_day,
        "bandwidth_kbps": bw_kbps,
        "monthly_traffic_gb": monthly_gb,
        "storage_raw_gb": raw_gb,
        "storage_compressed_gb": compressed_gb,
        "retention_years": retention_years,
        "recommended_tier": tier,
    }


def main():
    parser = argparse.ArgumentParser(description="Estimateur de dimensionnement IoT pour appels d'offres")
    parser.add_argument("--file", "-f", help="Fichier JSON du preset (détecte automatiquement les télémétries et cadences)")
    parser.add_argument("--devices", "-n", type=int, default=10, help="Nombre d'équipements projetés (défaut: 10)")
    parser.add_argument("--vars", type=int, default=8, help="Télémétries par équipement si --file absent")
    parser.add_argument("--interval", type=float, default=10.0, help="Cadence moyenne en secondes si --file absent")
    parser.add_argument("--protocol", default="mqtt", choices=["mqtt", "http", "coap"])
    parser.add_argument("--retention", type=int, default=3, help="Rétention base de données en années (défaut: 3)")
    args = parser.parse_args()

    vars_count = args.vars
    interval = args.interval
    proto = args.protocol
    label = "Projection personnalisée"

    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ Fichier introuvable : {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        preset = data.get("preset", data)
        label = preset.get("name", label)
        proto = preset.get("default_protocol", proto)
        telems = [v for v in preset.get("variables", []) if v.get("var_type") == "telemetry"]
        if telems:
            vars_count = len(telems)
            intervals = [v.get("publish_interval", 5.0) for v in telems if v.get("publish_interval")]
            if intervals:
                interval = round(sum(intervals) / len(intervals), 2)

    res = estimate_sizing(args.devices, vars_count, interval, proto, True, args.retention)
    print(f"\n📐 Annexe Dimensionnement Offre — {label}")
    print("-" * 60)
    print(f"| Parc projeté       | {res['device_count']} équipements ({res['device_count'] * res['vars_per_device']} points) |")
    print(f"| Protocole / Cadence| {res['protocol']} (TLS) • {res['interval_sec']}s |")
    print(f"| Débit moyen        | {res['msgs_per_sec']} msg/s ({res['msgs_per_day']:,} msg/j) |")
    print(f"| Trafic réseau / 4G | {res['bandwidth_kbps']} kbps ({res['monthly_traffic_gb']} Go/mois) |")
    print(f"| Stockage ({res['retention_years']} ans)    | {res['storage_compressed_gb']} Go compressés ({res['storage_raw_gb']} Go bruts) |")
    print(f"| Gabarit ThingsBoard| {res['recommended_tier']} |")
    print("-" * 60)


if __name__ == "__main__":
    main()
