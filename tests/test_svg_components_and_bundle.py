"""
Unit Tests for the 30 Modular SCADA SVG Components & ThingsBoard 4.3 Widget Bundle.
"""

import json
import pytest
from app.core.svg_components import (
    get_svg_components_catalog,
    generate_thingsboard_widget_bundle,
    generate_individual_widget_type,
    _wrap_preview_svg,
)


def test_svg_components_catalog_completeness():
    """Validates all 30 modular SVG components across the 4 industrial verticals."""
    catalog = get_svg_components_catalog()
    assert len(catalog) == 30
    families = {c.family for c in catalog}
    assert families == {"electricity", "hvac", "process", "infrastructure"}
    for spec in catalog:
        preview = _wrap_preview_svg(spec)
        assert preview.startswith("<svg ")
        assert preview.endswith("</svg>")


def test_thingsboard_widget_bundle_structure():
    """Validates ThingsBoard 4.3 widgetsBundle & 30 widgetTypes schema."""
    bundle = generate_thingsboard_widget_bundle()
    assert bundle["widgetsBundle"]["alias"] == "scada_industrial_suite"
    widget_types = bundle["widgetTypes"]
    assert len(widget_types) == 30

    for wt in widget_types:
        assert wt["scada"] is True
        desc = wt["descriptor"]
        assert desc["type"] == "latest"
        assert "{{valDisplay}}" in desc["templateHtml"]
        assert "self.onDataUpdated" in desc["controllerScript"]
        assert "settingsSchema" in desc
        parsed_cfg = json.loads(desc["defaultConfig"])
        assert "datasources" in parsed_cfg


def test_individual_widget_export_and_error():
    """Validates single widgetType export and ValueError on unknown component."""
    wt = generate_individual_widget_type("proc_pump")
    assert wt["fqn"] == "scada_industrial_suite.proc_pump"
    with pytest.raises(ValueError):
        generate_individual_widget_type("unknown_component_xyz")
