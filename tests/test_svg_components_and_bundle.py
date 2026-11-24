"""
Unit Tests for the 70 Modular ISA-101 SCADA SVG Components & ThingsBoard 4.3 Widget Bundles.
"""

import json
import pytest
from app.core.svg_components import (
    FAMILY_LABELS,
    get_svg_components_catalog,
    generate_thingsboard_widget_bundle,
    generate_individual_widget_type,
    render_synoptic_component,
    _wrap_preview_svg,
)


def test_svg_components_catalog_completeness():
    """Validates all 70 modular SVG components across the 6 industrial & ISA-101 families."""
    catalog = get_svg_components_catalog()
    assert len(catalog) == 70
    families = {c.family for c in catalog}
    assert families == set(FAMILY_LABELS.keys())
    for spec in catalog:
        preview = _wrap_preview_svg(spec)
        assert preview.startswith("<svg ")
        assert preview.endswith("</svg>")


def test_thingsboard_master_and_thematic_bundles():
    """Validates Master Bundle (70 widgets), 6 Thematic Bundles, and redundant Shape+Color alarm coding."""
    master = generate_thingsboard_widget_bundle()
    assert master["widgetsBundle"]["alias"] == "scada_industrial_suite"
    widget_types = master["widgetTypes"]
    assert len(widget_types) == 70

    for wt in widget_types:
        assert wt["scada"] is True
        desc = wt["descriptor"]
        assert desc["type"] == "latest"
        assert "{{valDisplay}}" in desc["templateHtml"]
        # Redundant Shape + Color ISA-101 indicators (daltonism-proof)
        assert "▲" in desc["templateHtml"]
        assert "■ !" in desc["templateHtml"]
        assert "alarmLevel" in desc["controllerScript"]
        parsed_cfg = json.loads(desc["defaultConfig"])
        assert "datasources" in parsed_cfg

    total_from_families = 0
    for fam in FAMILY_LABELS:
        b = generate_thingsboard_widget_bundle(family=fam)
        assert b["widgetsBundle"]["alias"] == f"scada_isa101_{fam}"
        assert len(b["widgetTypes"]) > 0
        total_from_families += len(b["widgetTypes"])
    assert total_from_families == 70

    with pytest.raises(ValueError):
        generate_thingsboard_widget_bundle(family="nonexistent_family")


def test_synoptic_component_renderer_and_individual_export():
    """Validates render_synoptic_component for ThingsBoard html_value_card and individual widgetType export."""
    g_svg = render_synoptic_component("elec_ups_asi", x=20, y=40, var_key="charge_ups", unit="%")
    assert 'transform="translate(20, 40)"' in g_svg
    assert "${charge_ups:1} %" in g_svg

    wt = generate_individual_widget_type("isa_analog_bar")
    assert wt["fqn"] == "scada_industrial_suite.isa_analog_bar"
    with pytest.raises(ValueError):
        generate_individual_widget_type("unknown_component_xyz")
