"""
IoT & ThingsBoard Architecture Sizing Calculator.

Computes message throughput, network bandwidth (MQTT/HTTP/CoAP + TLS overhead),
4G/LTE monthly data consumption, database storage requirements (raw & compressed),
recommended ThingsBoard server sizing, and generates a ready-to-paste Markdown
technical specification for pre-sales and bid management.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.device import DeviceConfig, TransportProtocol
from app.models.variable import VariableConfig, VariableType


PROTOCOL_OVERHEAD_BYTES = {
    "mqtt": 48,
    "http": 380,
    "coap": 24,
}
TLS_OVERHEAD_BYTES = 64


class SizingRequest(BaseModel):
    """Input parameters for projecting an IoT deployment architecture."""
    device_count: int = Field(default=10, ge=1, le=100000, description="Total number of field devices")
    variables_per_device: int = Field(default=8, ge=1, le=500, description="Telemetry variables per device")
    publish_interval_sec: float = Field(default=10.0, ge=0.1, le=86400.0, description="Average publish period in seconds")
    protocol: str = Field(default="mqtt", description="Transport protocol: mqtt, http, or coap")
    use_tls: bool = Field(default=True, description="Whether TLS/SSL encryption is enabled")
    retention_years: int = Field(default=3, ge=1, le=15, description="Time-series database retention in years")
    compression_ratio: float = Field(default=5.0, ge=1.0, le=20.0, description="Database compression ratio (e.g. TimescaleDB)")


class SizingResult(BaseModel):
    """Calculated throughput, bandwidth, storage, and infrastructure recommendation."""
    device_count: int
    total_variables: int
    messages_per_second: float
    messages_per_day: int
    data_points_per_day: int
    avg_packet_bytes: int
    bandwidth_kbps: float
    monthly_traffic_gb: float
    storage_raw_gb_total: float
    storage_compressed_gb_total: float
    retention_years: int
    recommended_tb_tier: str
    recommended_specs: str
    markdown_report: str


def estimate_payload_bytes(var_count: int) -> int:
    """Estimates JSON telemetry payload size in bytes for N variables."""
    # Typical JSON: {"var_name_01":123.45,...} ~ 22 bytes per metric + 4 bytes braces
    return max(16, 4 + var_count * 22)


def calculate_sizing(req: SizingRequest) -> SizingResult:
    """Computes full IoT telemetry sizing metrics and ThingsBoard sizing tier."""
    proto = req.protocol.lower()
    proto_overhead = PROTOCOL_OVERHEAD_BYTES.get(proto, 48)
    tls_overhead = TLS_OVERHEAD_BYTES if req.use_tls else 0

    payload_bytes = estimate_payload_bytes(req.variables_per_device)
    avg_packet_bytes = payload_bytes + proto_overhead + tls_overhead

    msgs_per_sec = req.device_count / req.publish_interval_sec
    msgs_per_day = int(round(msgs_per_sec * 86400))
    data_points_per_day = msgs_per_day * req.variables_per_device

    bytes_per_sec = msgs_per_sec * avg_packet_bytes
    bandwidth_kbps = round((bytes_per_sec * 8) / 1000.0, 2)
    monthly_traffic_gb = round((bytes_per_sec * 86400 * 30) / (1024 ** 3), 3)

    # DB storage: ~48 bytes per stored data point row (timestamp + entity_id + key_id + value + index)
    bytes_per_dp_row = 48
    raw_bytes_per_year = data_points_per_day * 365 * bytes_per_dp_row
    storage_raw_gb_total = round((raw_bytes_per_year * req.retention_years) / (1024 ** 3), 2)
    storage_compressed_gb_total = round(storage_raw_gb_total / req.compression_ratio, 2)

    if msgs_per_sec <= 50 and req.device_count <= 250:
        tier = "Compact (Mono-nœud)"
        specs = "4 vCPU • 8 Go RAM • SSD NVMe 100 Go (PostgreSQL + TimescaleDB)"
    elif msgs_per_sec <= 500 and req.device_count <= 2500:
        tier = "Standard Production"
        specs = "8 vCPU • 16 Go RAM • SSD NVMe 250 Go (TimescaleDB + Redis)"
    elif msgs_per_sec <= 2500:
        tier = "Haute Performance"
        specs = "16 vCPU • 32 Go RAM • SSD NVMe 500 Go (Cluster TB + Cassandra/TimescaleDB)"
    else:
        tier = "Cluster Entreprise Distribué"
        specs = "Multi-nœuds Kubernetes • Kafka Queue • Cassandra Cluster (32+ vCPU / 64+ Go RAM)"

    markdown_report = (
        f"### Dimensionnement Architecture IoT & ThingsBoard\n\n"
        f"| Paramètre | Valeur Estimée |\n"
        f"| :--- | :--- |\n"
        f"| **Parc d'équipements** | {req.device_count} équipements ({req.device_count * req.variables_per_device} points) |\n"
        f"| **Protocole & Sécurité** | {proto.upper()} ({'TLS activé' if req.use_tls else 'Sans TLS'}) • Cadence {req.publish_interval_sec}s |\n"
        f"| **Débit moyen** | {round(msgs_per_sec, 2)} msg/s ({msgs_per_day:,} msg/jour) |\n"
        f"| **Points de données / jour** | {data_points_per_day:,} points/jour |\n"
        f"| **Bande passante réseau** | {bandwidth_kbps} kbps ({monthly_traffic_gb} Go/mois) |\n"
        f"| **Stockage ({req.retention_years} ans)** | {storage_compressed_gb_total} Go compressés ({storage_raw_gb_total} Go bruts) |\n"
        f"| **Gabarit Serveur ThingsBoard** | **{tier}** — {specs} |\n"
    )

    return SizingResult(
        device_count=req.device_count,
        total_variables=req.device_count * req.variables_per_device,
        messages_per_second=round(msgs_per_sec, 3),
        messages_per_day=msgs_per_day,
        data_points_per_day=data_points_per_day,
        avg_packet_bytes=avg_packet_bytes,
        bandwidth_kbps=bandwidth_kbps,
        monthly_traffic_gb=monthly_traffic_gb,
        storage_raw_gb_total=storage_raw_gb_total,
        storage_compressed_gb_total=storage_compressed_gb_total,
        retention_years=req.retention_years,
        recommended_tb_tier=tier,
        recommended_specs=specs,
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
