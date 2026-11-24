"""
Blocking ANSI/ISA-101.01 (High-Performance HMI) Compliance Tests.

Ensures that all modular SVG components, SCADA synoptics, single-device dashboards,
and multi-equipment site dashboards strictly adhere to ISA-101 ergonomics:
- Matte light-gray anti-glare background (#E5E7EB)
- Desaturated slate/steel equipment colors at nominal state (#475569 / #334155)
- Zero neon/rainbow colors at nominal state
- Color by Exception (#D97706 Amber / #DC2626 Red) reserved for warnings/alarms
"""

from pathlib import Path
from app.core.svg_components import (
    ISA101_BG,
    ISA101_NOMINAL_COLOR,
    get_svg_components_catalog,
    generate_thingsboard_widget_bundle,
)
from app.core.dashboard_generator import PALETTE_COLORS, generate_thingsboard_dashboard
from app.core.site_blueprints import generate_site_hypervision_dashboard
from app.core.scada_synoptics import SCADA_CSS
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType, SimMode, MathConfig


FORBIDDEN_NEON_COLORS = {"#E2001A", "#10B981", "#EC4899", "#84CC16", "#F97316", "#FACC15"}


def test_svg_components_strict_isa101():
    """Verifies all 30 modular SVG components use ISA-101 matte gray and steel nominal color."""
    assert ISA101_BG == "#E5E7EB"
    assert ISA101_NOMINAL_COLOR == "#475569"
    for spec in get_svg_components_catalog():
        assert spec.default_color == "#475569", f"{spec.id} must use ISA-101 nominal #475569"
        for neon in FORBIDDEN_NEON_COLORS:
            assert neon not in spec.svg_body, f"{spec.id} contains forbidden neon color {neon}"

    bundle = generate_thingsboard_widget_bundle()
    for wt in bundle["widgetTypes"]:
        assert "isa-101" in wt["tags"]
        assert ISA101_BG in wt["descriptor"]["templateCss"]


def test_dashboard_generator_strict_isa101():
    """Verifies dashboard_generator PALETTE_COLORS and gauges obey ISA-101 Color by Exception."""
    for c in PALETTE_COLORS:
        assert c.upper() not in FORBIDDEN_NEON_COLORS, f"Forbidden neon color {c} in PALETTE_COLORS"

    dev = DeviceConfig(id="d1", name="Test ISA-101")
    vars_list = [
        VariableConfig(
            id="pression",
            name="Pression",
            device_id="d1",
            var_type=VariableType.TELEMETRY,
            sim_mode=SimMode.SINE,
            math_config=MathConfig(min_val=0, max_val=10),
        )
    ]
    dash = generate_thingsboard_dashboard(dev, vars_list)
    for w in dash["configuration"]["widgets"].values():
        if w.get("typeAlias") == "simple_gauge_justgage":
            assert w["config"]["settings"]["levelColors"] == ["#475569", "#D97706", "#DC2626"]


def test_scada_synoptics_and_site_hypervision_isa101():
    """Verifies SCADA_CSS, all 35 built-in synoptics, and Hypervision Site dashboards obey ISA-101."""
    from app.core.equipment_catalog import get_builtin_catalog
    from app.core.scada_synoptics import SYNOPTIC_COMPONENT_MAP, get_scada_synoptic_html

    assert "background: #E5E7EB;" in SCADA_CSS
    assert "blink-live" not in SCADA_CSS

    valid_comp_ids = {c.id for c in get_svg_components_catalog()}
    for preset in get_builtin_catalog():
        assert preset.id in SYNOPTIC_COMPONENT_MAP, f"Preset {preset.id} missing from SYNOPTIC_COMPONENT_MAP"
        for comp_id, var_key, _ in SYNOPTIC_COMPONENT_MAP[preset.id]:
            assert comp_id in valid_comp_ids, f"Unknown SVG component {comp_id} in {preset.id}"
        dev = DeviceConfig(id=preset.id, name=preset.name)
        html = get_scada_synoptic_html(dev, preset.variables, preset_id=preset.id)
        assert "background: #E5E7EB;" in html
        for neon in FORBIDDEN_NEON_COLORS:
            assert neon not in html, f"Forbidden neon color {neon} in synoptic for {preset.id}"

    site_dash = generate_site_hypervision_dashboard("site_tertiaire_bacs")
    widgets = list(site_dash["configuration"]["widgets"].values())
    header = next(w for w in widgets if w.get("typeAlias") == "html_card")
    assert "background:#E5E7EB" in header["config"]["settings"]["cardHtml"]
