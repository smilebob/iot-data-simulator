"""
Unit Tests for ThingsBoard Dashboard Generation
===============================================
Validates ThingsBoard 4.3 JSON dashboard descriptors, SCADA P&ID vector synoptic
integration, interactive control widgets (switches, inputs), and layout grid positioning.
"""

import json
import os
import sys
import shutil
import tempfile
import types

# Lightweight mock stubs to allow test execution without external pip dependencies
if 'pydantic' not in sys.modules:
    pyd = types.ModuleType('pydantic')
    class BaseModel:
        """Mock BaseModel."""
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def model_copy(self, deep=True):
            import copy
            return copy.deepcopy(self)
        def model_dump(self):
            return self.__dict__
    def Field(default=None, default_factory=None, description=None, **kwargs):
        if default_factory:
            return default_factory()
        return default
    pyd.BaseModel = BaseModel
    pyd.Field = Field
    pyd.field_validator = lambda *a, **k: (lambda f: f)
    sys.modules['pydantic'] = pyd

for mod in ['paho', 'paho.mqtt', 'paho.mqtt.client', 'fastapi', 'fastapi.responses', 'aiocoap', 'httpx']:
    if mod not in sys.modules:
        m = types.ModuleType(mod)
        m.Client = lambda *a, **k: None
        m.Response = lambda *a, **k: None
        sys.modules[mod] = m

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.models.device import DeviceConfig, PlatformType, TransportProtocol
from app.models.variable import VariableConfig, VariableType, DataType, SimMode, MathConfig
from app.core.dashboard_generator import generate_thingsboard_dashboard


def test_thingsboard_dashboard_generation():
    """Validates complete ThingsBoard 4.3 JSON dashboard generation and widget layouts."""
    # 1. Test device with specific token
    dev = DeviceConfig(
        id="test_boiler_01",
        name="Chaudière Test #1",
        platform=PlatformType.THINGSBOARD,
        protocol=TransportProtocol.MQTT,
        token="TB_TOKEN_SECRET_9876",
        publish_interval=2.0,
        enabled=True
    )

    vars_list = [
        VariableConfig(
            id="v_steam_press",
            name="Pression Vapeur",
            device_id="test_boiler_01",
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="bar",
            publish_interval=2.0,
            sim_mode=SimMode.SINE,
            math_config=MathConfig(min_val=8.0, max_val=15.0)
        ),
        VariableConfig(
            id="v_flame_temp",
            name="Température Flamme",
            device_id="test_boiler_01",
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="°C",
            publish_interval=2.0,
            sim_mode=SimMode.SINE,
            math_config=MathConfig(min_val=750.0, max_val=920.0)
        ),
        VariableConfig(
            id="v_burner_status",
            name="État Brûleur",
            device_id="test_boiler_01",
            var_type=VariableType.ATTRIBUTE,
            data_type=DataType.STRING,
            unit="",
            publish_interval=10.0,
            sim_mode=SimMode.CONSTANT,
            math_config=MathConfig(constant_val="ACTIVE_HIGH")
        ),
        VariableConfig(
            id="v_pump_enable",
            name="Pompe d'Alimentation Active",
            device_id="test_boiler_01",
            var_type=VariableType.ATTRIBUTE,
            data_type=DataType.BOOLEAN,
            unit="",
            publish_interval=10.0,
            sim_mode=SimMode.CONSTANT,
            math_config=MathConfig(constant_val=True)
        )
    ]

    # Generate ThingsBoard dashboard
    dashboard = generate_thingsboard_dashboard(dev, vars_list)

    assert dashboard["title"] == "Supervision SCADA - Chaudière Test #1"
    # CIS / OWASP Security: Token must never leak into description or widgets
    assert "TB_TOKEN_SECRET_9876" not in dashboard["configuration"]["description"]

    # Verify singleEntity alias placeholder
    aliases = dashboard["configuration"]["entityAliases"]
    assert len(aliases) == 1
    alias = list(aliases.values())[0]
    assert alias["alias"] == "Chaudière Test #1"
    assert alias["filter"]["type"] == "singleEntity"
    assert alias["filter"]["singleEntity"]["id"] == "00000000-0000-0000-0000-000000000000"

    # Verify widgets collection
    widgets = dashboard["configuration"]["widgets"]
    assert len(widgets) >= 4  # Header + SCADA Synoptic + Gauges + Chart + Attributes Table

    # Verify SCADA Synoptic widget
    synoptic_w = next(w for w in widgets.values() if "Synoptique SCADA" in w.get("title", ""))
    assert synoptic_w.get("typeFullFqn") == "system.cards.html_value_card"
    assert synoptic_w.get("typeAlias") == "html_value_card"
    assert synoptic_w.get("type") == "latest"
    assert len(synoptic_w["config"]["datasources"][0]["dataKeys"]) >= 2
    assert "<svg" in synoptic_w["config"]["settings"]["cardHtml"]
    assert synoptic_w["config"]["settings"]["cardHtml"] == synoptic_w["config"]["settings"]["html"]
    assert synoptic_w["config"]["settings"]["cardCss"] == synoptic_w["config"]["settings"]["css"]
    assert synoptic_w["config"].get("useDashboardTimewindow") is True
    assert "pipe-flow" in synoptic_w["config"]["settings"]["cardHtml"]
    assert "${" in synoptic_w["config"]["settings"]["cardHtml"]
    assert "TB_TOKEN_SECRET_9876" not in synoptic_w["config"]["settings"]["cardHtml"]

    # ThingsBoard 4.3 compatibility: dataKey label must match name
    for dk in synoptic_w["config"]["datasources"][0]["dataKeys"]:
        assert dk["label"] == dk["name"], f"DataKey label '{dk['label']}' must equal name '{dk['name']}' for ThingsBoard 4.3"

    # Verify Header widget
    header_w = next(w for w in widgets.values() if w.get("typeAlias") == "html_card" and "Informations" in w.get("title", ""))
    assert header_w.get("typeFullFqn") == "system.cards.html_card"
    assert "TB_TOKEN_SECRET_9876" not in header_w["config"]["settings"]["cardHtml"]
    assert "Jeton Sécurisé" in header_w["config"]["settings"]["cardHtml"]
    assert header_w["config"]["settings"]["cardHtml"] == header_w["config"]["settings"]["html"]
    assert "Chaudière Test #1" in header_w["config"]["settings"]["cardHtml"]
    assert "MQTT" in header_w["config"]["settings"]["cardHtml"]

    # Verify JustGage gauge widgets
    gauge_w = next(w for w in widgets.values() if w.get("typeAlias") == "simple_gauge_justgage")
    assert gauge_w.get("typeFullFqn") == "system.digital_gauges.simple_gauge_justgage"
    assert gauge_w.get("bundleAlias") == "digital_gauges"

    # Verify timeseries chart widget
    chart_w = next(w for w in widgets.values() if w.get("typeAlias") == "basic_timeseries")
    assert chart_w.get("typeFullFqn") == "system.charts.basic_timeseries"
    assert chart_w.get("bundleAlias") == "charts"
    ds = chart_w["config"]["datasources"][0]
    datakeys = [dk["name"] for dk in ds["dataKeys"]]
    assert "v_steam_press" in datakeys
    assert "v_flame_temp" in datakeys

    # Verify interactive control widgets (Switch & Input Form)
    switch_w = next(w for w in widgets.values() if w.get("typeAlias") in ("single_switch", "round_switch"))
    assert switch_w.get("typeFullFqn") in ("system.single_switch", "system.control_widgets.round_switch")
    assert switch_w.get("bundleAlias") == "control_widgets"
    assert "Pilotage - Pompe d'Alimentation Active" in switch_w.get("title", "")
    assert switch_w["config"]["settings"]["onUpdateState"]["setAttribute"]["key"] == "v_pump_enable"
    assert switch_w["config"]["settings"]["onUpdateState"]["setAttribute"]["scope"] == "SHARED_SCOPE"

    input_form_w = next(w for w in widgets.values() if w.get("typeAlias") == "update_multiple_attributes")
    assert input_form_w.get("typeFullFqn") == "system.input_widgets.update_multiple_attributes"
    assert input_form_w.get("bundleAlias") == "input_widgets"
    assert "Consigne - État Brûleur" in input_form_w.get("title", "")

    # Verify attributes table (entities_table) and grid layout alignment
    attr_w = next(w for w in widgets.values() if w.get("typeAlias") == "entities_table")
    assert attr_w.get("typeFullFqn") == "system.cards.entities_table"
    assert attr_w.get("bundleAlias") == "cards"
    attr_ds = attr_w["config"]["datasources"][0]
    attr_keys = [dk["name"] for dk in attr_ds["dataKeys"]]
    assert "v_burner_status" in attr_keys
    assert "v_pump_enable" in attr_keys

    # Layout anti-overlapping assertion
    layout = dashboard["configuration"]["states"]["default"]["layouts"]["main"]["widgets"]
    switch_layout = layout[switch_w["id"]]
    attr_layout = layout[attr_w["id"]]
    assert attr_layout["row"] == switch_layout["row"] + switch_layout["sizeY"], "Attributes table must be positioned below control widgets without overlap!"
    assert attr_layout["sizeY"] == 4, "Attributes table height must be adjusted to 4 when control widgets exist!"

    # Valid JSON serialization check
    serialized = json.dumps(dashboard)
    assert len(serialized) > 1000


if __name__ == "__main__":
    test_thingsboard_dashboard_generation()
    print("✅ test_thingsboard_dashboard_generation passed successfully!")
