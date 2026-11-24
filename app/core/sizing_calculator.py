"""
IoT & ThingsBoard Architecture Sizing Calculator.

Computes message & data-point throughput (msg/s, dp/s), network bandwidth
(MQTT/HTTP/CoAP + TLS overhead), 4G/LTE monthly data consumption, database
storage requirements (PostgreSQL raw vs Cassandra/TimescaleDB ~5x),
recommended ThingsBoard server sizing aligned with official ThingsBoard
reference benchmarks, and generates a verifiable Markdown technical
specification citing all hypotheses and official ThingsBoard sources.
"""

from typing import List, Dict
from pydantic import BaseModel, Field
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType


PROTOCOL_OVERHEAD_BYTES = {
    "mqtt": 48,   # TCP/IP + MQTT PUBLISH header + topic v1/devices/me/telemetry
    "http": 380,  # TCP/IP + HTTP/1.1 POST headers + /api/v1/{token}/telemetry
    "coap": 24,   # UDP/IP + CoAP RFC 7252 header + Uri-Path options
}
TLS_OVERHEAD_BYTES = 64

# Official ThingsBoard PostgreSQL SQL-mode storage footprint per data point
# (ts_kv row + primary key + indexes + ts_kv_latest overhead ≈ 140–150 B/dp,
# i.e. ~1 GB per 7 million data points).
POSTGRES_BYTES_PER_DATA_POINT = 145

# Official verified ThingsBoard reference documentation sources
THINGSBOARD_OFFICIAL_SOURCES: List[Dict[str, str]] = [
    {
        "title": "ThingsBoard Reference Architecture (SQL vs Hybrid NoSQL / Cassandra ~5×)",
        "url": "https://thingsboard.io/docs/reference/architecture/",
        "scope": "Architecture 2 niveaux (PostgreSQL entités + SQL ou Cassandra séries temporelles), seuil 5 000–10 000 dp/s, efficacité disque ~5× Cassandra vs PostgreSQL.",
    },
    {
        "title": "ThingsBoard Performance & Benchmarks",
        "url": "https://thingsboard.io/docs/reference/performance-tests/",
        "scope": "Dimensionnement exprimé en data points/seconde (dp/s), empreinte RAM des connexions MQTT (~6,5 Go / 100k connexions), capacité PostgreSQL vs Cassandra.",
    },
    {
        "title": "ThingsBoard Monolithic Architecture",
        "url": "https://thingsboard.io/docs/reference/monolithic/",
        "scope": "Déploiement mono-JVM + PostgreSQL + In-Memory Queue pour PoC et petites/moyennes productions (< 2 500–5 000 dp/s).",
    },
    {
        "title": "ThingsBoard Microservices Architecture (MSA)",
        "url": "https://thingsboard.io/docs/reference/msa/",
        "scope": "Cluster haute disponibilité Kubernetes, Apache Kafka, Redis/Valkey et Cassandra (RF=3) au-delà de 5 000–10 000 dp/s.",
    },
    {
        "title": "ThingsBoard Installation Options & Hardware Requirements",
        "url": "https://thingsboard.io/docs/user-guide/install/installation-options/",
        "scope": "Prérequis CPU/RAM/SSD par profil (PoC 2–4 vCPU / 4–8 Go RAM, Production 4+ vCPU / 16 Go RAM, Cluster HA 3+ nœuds).",
    },
]


class SizingRequest(BaseModel):
    """Input parameters for projecting an IoT deployment architecture."""
    device_count: int = Field(default=10, ge=1, le=100000, description="Total number of field devices")
    variables_per_device: int = Field(default=8, ge=1, le=500, description="Telemetry variables per device")
    publish_interval_sec: float = Field(default=10.0, ge=0.1, le=86400.0, description="Average publish period in seconds")
    protocol: str = Field(default="mqtt", description="Transport protocol: mqtt, http, or coap")
    use_tls: bool = Field(default=True, description="Whether TLS/SSL encryption is enabled")
    retention_years: int = Field(default=3, ge=1, le=15, description="Time-series database retention in years")
    compression_ratio: float = Field(default=5.0, ge=1.0, le=20.0, description="Storage efficiency ratio vs raw PostgreSQL (~5x for Cassandra/TimescaleDB)")


class SizingResult(BaseModel):
    """Calculated throughput, bandwidth, storage, infrastructure recommendation, and verifiable sources."""
    device_count: int
    total_variables: int
    messages_per_second: float
    messages_per_day: int
    data_points_per_second: float
    data_points_per_day: int
    avg_packet_bytes: int
    bandwidth_kbps: float
    monthly_traffic_gb: float
    storage_raw_gb_total: float
    storage_compressed_gb_total: float
    retention_years: int
    recommended_tb_tier: str
    recommended_specs: str
    hypotheses: List[str]
    sources: List[Dict[str, str]]
    markdown_report: str


def estimate_payload_bytes(var_count: int) -> int:
    """Estimates JSON telemetry payload size in bytes for N variables."""
    # Typical JSON: {"var_name_01":123.45,...} ~ 22 bytes per metric + 4 bytes braces
    return max(16, 4 + var_count * 22)


def calculate_sizing(req: SizingRequest) -> SizingResult:
    """Computes full IoT telemetry sizing metrics and ThingsBoard sizing tier backed by official benchmarks."""
    proto = req.protocol.lower()
    proto_overhead = PROTOCOL_OVERHEAD_BYTES.get(proto, 48)
    tls_overhead = TLS_OVERHEAD_BYTES if req.use_tls else 0

    payload_bytes = estimate_payload_bytes(req.variables_per_device)
    avg_packet_bytes = payload_bytes + proto_overhead + tls_overhead

    msgs_per_sec = req.device_count / req.publish_interval_sec
    msgs_per_day = int(round(msgs_per_sec * 86400))
    data_points_per_sec = msgs_per_sec * req.variables_per_device
    data_points_per_day = msgs_per_day * req.variables_per_device

    bytes_per_sec = msgs_per_sec * avg_packet_bytes
    bandwidth_kbps = round((bytes_per_sec * 8) / 1000.0, 2)
    monthly_traffic_gb = round((bytes_per_sec * 86400 * 30) / (1024 ** 3), 3)

    # Raw PostgreSQL SQL-mode footprint (~145 B/dp including ts_kv + PK + indexes + ts_kv_latest)
    raw_bytes_per_year = data_points_per_day * 365 * POSTGRES_BYTES_PER_DATA_POINT
    storage_raw_gb_total = round((raw_bytes_per_year * req.retention_years) / (1024 ** 3), 2)
    # Hybrid Cassandra / TimescaleDB compressed footprint (~5x more storage-efficient than raw PostgreSQL)
    storage_compressed_gb_total = round(storage_raw_gb_total / req.compression_ratio, 2)

    # ThingsBoard official tiering based on data points per second (dp/s) & device count
    if data_points_per_sec <= 2500 and req.device_count <= 1000:
        tier = "Compact / PoC (Monolithique)"
        specs = "App : 2–4 vCPU • 8 Go RAM | BDD : PostgreSQL SQL mode (2 vCPU • 4 Go RAM • SSD 100 Go) | Queue In-Memory"
    elif data_points_per_sec <= 5000 and req.device_count <= 50000:
        tier = "Production Standard (Monolithique)"
        specs = "App : 4–8 vCPU • 16 Go RAM | BDD : PostgreSQL SQL mode (4 vCPU • 8 Go RAM • SSD NVMe 250 Go) | Queue In-Memory ou Kafka"
    elif data_points_per_sec <= 10000:
        tier = "Haute Charge (Transition Hybride)"
        specs = "App : 8–16 vCPU • 16–32 Go RAM | Queue Apache Kafka | BDD : PostgreSQL (entités) + TimescaleDB / Cassandra (séries) • SSD NVMe 500 Go"
    else:
        tier = "Cluster Microservices HA (Hybride Cassandra)"
        specs = "Kubernetes : 3+ nœuds App (4 vCPU / 16 Go RAM chacun) • Apache Kafka (3 nœuds) • Cassandra RF=3 (3+ nœuds SSD) + PostgreSQL + Redis"

    hypotheses = [
        f"Métrique de dimensionnement ThingsBoard : débit en points de données/seconde (dp/s = {round(msgs_per_sec, 2)} msg/s × {req.variables_per_device} var = {round(data_points_per_sec, 2)} dp/s).",
        f"Taille moyenne d'un paquet réseau : {payload_bytes} o (JSON ~22 o/variable) + {proto_overhead} o (en-tête {proto.upper()}) + {tls_overhead} o (TLS) = {avg_packet_bytes} octets/msg.",
        f"Stockage brut PostgreSQL (mode SQL ts_kv + index + ts_kv_latest) : {POSTGRES_BYTES_PER_DATA_POINT} octets/point (≈ 1 Go pour 7 millions de points, avant réplication/backups).",
        f"Stockage optimisé (Hybride Cassandra / TimescaleDB compressé) : facteur {req.compression_ratio:g}× par rapport à PostgreSQL brut (≈ {round(POSTGRES_BYTES_PER_DATA_POINT / req.compression_ratio, 1)} octets/point avant RF).",
        "Seuils d'architecture ThingsBoard : Monolithique PostgreSQL ≤ 5 000 dp/s ; transition Kafka/Hybride entre 5 000 et 10 000 dp/s ; Cluster Microservices HA + Cassandra > 10 000 dp/s.",
    ]

    hypotheses_md = "\n".join(f"- {h}" for h in hypotheses)
    sources_md = "\n".join(
        f"- [{s['title']}]({s['url']}) — *{s['scope']}*"
        for s in THINGSBOARD_OFFICIAL_SOURCES
    )

    markdown_report = (
        f"### Dimensionnement Architecture IoT & ThingsBoard\n\n"
        f"| Paramètre | Valeur Estimée |\n"
        f"| :--- | :--- |\n"
        f"| **Parc d'équipements** | {req.device_count} équipements ({req.device_count * req.variables_per_device} points) |\n"
        f"| **Protocole & Sécurité** | {proto.upper()} ({'TLS activé' if req.use_tls else 'Sans TLS'}) • Cadence {req.publish_interval_sec}s |\n"
        f"| **Débit messages** | {round(msgs_per_sec, 2)} msg/s ({msgs_per_day:,} msg/jour) |\n"
        f"| **Débit points de données (métrique TB)** | **{round(data_points_per_sec, 2)} dp/s** ({data_points_per_day:,} points/jour) |\n"
        f"| **Bande passante réseau** | {bandwidth_kbps} kbps ({monthly_traffic_gb} Go/mois) |\n"
        f"| **Stockage ({req.retention_years} ans)** | **{storage_compressed_gb_total} Go** (Cassandra/TimescaleDB {req.compression_ratio:g}×) / {storage_raw_gb_total} Go bruts (PostgreSQL SQL) |\n"
        f"| **Gabarit Serveur ThingsBoard** | **{tier}** — {specs} |\n\n"
        f"#### Hypothèses de Calcul (Vérifiables)\n"
        f"{hypotheses_md}\n\n"
        f"#### Sources Officielles ThingsBoard\n"
        f"{sources_md}\n"
    )

    return SizingResult(
        device_count=req.device_count,
        total_variables=req.device_count * req.variables_per_device,
        messages_per_second=round(msgs_per_sec, 3),
        messages_per_day=msgs_per_day,
        data_points_per_second=round(data_points_per_sec, 3),
        data_points_per_day=data_points_per_day,
        avg_packet_bytes=avg_packet_bytes,
        bandwidth_kbps=bandwidth_kbps,
        monthly_traffic_gb=monthly_traffic_gb,
        storage_raw_gb_total=storage_raw_gb_total,
        storage_compressed_gb_total=storage_compressed_gb_total,
        retention_years=req.retention_years,
        recommended_tb_tier=tier,
        recommended_specs=specs,
        hypotheses=hypotheses,
        sources=THINGSBOARD_OFFICIAL_SOURCES,
        markdown_report=markdown_report,
    )


def calculate_sizing_from_active_devices(
    devices: List[DeviceConfig],
    variables: List[VariableConfig],
    scale_multiplier: int = 1,
    retention_years: int = 3,
) -> SizingResult:
    """Computes sizing from currently configured simulator devices and variables."""
    active_devices = [d for d in devices if d.enabled] or devices
    if not active_devices:
        return calculate_sizing(SizingRequest(device_count=scale_multiplier, retention_years=retention_years))

    total_devs = len(active_devices) * max(1, scale_multiplier)
    telemetry_vars = [v for v in variables if v.var_type == VariableType.TELEMETRY and v.enabled]
    avg_vars = max(1, round(len(telemetry_vars) / len(active_devices))) if telemetry_vars else 5

    intervals = [d.publish_interval for d in active_devices if d.publish_interval and d.publish_interval > 0]
    avg_interval = round(sum(intervals) / len(intervals), 2) if intervals else 5.0

    first_proto = active_devices[0].protocol.value if hasattr(active_devices[0].protocol, "value") else str(active_devices[0].protocol)

    return calculate_sizing(
        SizingRequest(
            device_count=total_devs,
            variables_per_device=avg_vars,
            publish_interval_sec=avg_interval,
            protocol=first_proto,
            use_tls=True,
            retention_years=retention_years,
        )
    )
