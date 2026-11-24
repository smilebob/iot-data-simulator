"""
Unit Tests for IoT Architecture Sizing Calculator and Regulatory/ROI Presets.
"""

from app.core.sizing_calculator import (
    SizingRequest,
    calculate_sizing,
    calculate_sizing_from_active_devices,
)
from app.core.equipment_catalog import get_equipment_catalog
from app.models.device import DeviceConfig, TransportProtocol, PlatformType
from app.models.variable import VariableConfig, VariableType, SimMode


def test_sizing_calculator_compact_and_cluster():
    """Validates throughput, bandwidth, storage, and server tier recommendations."""
    small = calculate_sizing(
        SizingRequest(
            device_count=10,
            variables_per_device=8,
            publish_interval_sec=10.0,
            protocol="mqtt",
            use_tls=True,
            retention_years=3,
        )
    )
    assert small.messages_per_second == 1.0
    assert small.messages_per_day == 86400
    assert small.data_points_per_second == 8.0
    assert small.data_points_per_day == 86400 * 8
    assert small.storage_compressed_gb_total < small.storage_raw_gb_total
    assert "Compact" in small.recommended_tb_tier
    assert "Dimensionnement Architecture IoT" in small.markdown_report
    assert "https://thingsboard.io/docs/reference/architecture/" in small.markdown_report
    assert len(small.hypotheses) >= 4
    assert len(small.sources) >= 4

    large = calculate_sizing(
        SizingRequest(
            device_count=5000,
            variables_per_device=12,
            publish_interval_sec=1.0,
            protocol="http",
            use_tls=True,
            retention_years=5,
        )
    )
    assert large.messages_per_second == 5000.0
    assert "Cluster" in large.recommended_tb_tier


def test_sizing_from_active_devices():
    """Validates sizing computation derived from simulator device/variable models."""
    devices = [
        DeviceConfig(id="dev1", name="GTB 1", protocol=TransportProtocol.MQTT, platform=PlatformType.THINGSBOARD, publish_interval=5.0),
        DeviceConfig(id="dev2", name="GTB 2", protocol=TransportProtocol.MQTT, platform=PlatformType.THINGSBOARD, publish_interval=5.0),
    ]
    variables = [
        VariableConfig(id="v1", name="T1", device_id="dev1", var_type=VariableType.TELEMETRY),
        VariableConfig(id="v2", name="P1", device_id="dev1", var_type=VariableType.TELEMETRY),
        VariableConfig(id="v3", name="T2", device_id="dev2", var_type=VariableType.TELEMETRY),
        VariableConfig(id="v4", name="P2", device_id="dev2", var_type=VariableType.TELEMETRY),
    ]
    res = calculate_sizing_from_active_devices(devices, variables, scale_multiplier=5, retention_years=2)
    assert res.device_count == 10
    assert res.total_variables == 20
    assert res.retention_years == 2


def test_regulatory_roi_presets_in_catalog():
    """Validates the 3 new BACS / RCU / ISO 50001 presets and their causal physics references."""
    catalog = {p.id: p for p in get_equipment_catalog()}
    expected_ids = ["bldg_bacs_class_a", "infra_district_heating", "ind_iso50001_multifluid"]

    for pid in expected_ids:
        assert pid in catalog, f"Missing regulatory preset {pid}"
        preset = catalog[pid]
        var_ids = {v.id for v in preset.variables}
        for v in preset.variables:
            if v.sim_mode == SimMode.INTEGRATOR:
                assert v.integrator_config.source_variable_id in var_ids
            if v.sim_mode == SimMode.DERIVED:
                assert len(v.derived_config.formula.strip()) > 0
