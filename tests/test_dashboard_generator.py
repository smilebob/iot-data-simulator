import json
import os
import sys
import shutil
import tempfile
import types

# Mocks minimaux pour exécuter hors conteneur sans dépendances externes
if 'pydantic' not in sys.modules:
    pyd = types.ModuleType('pydantic')
    class BaseModel:
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
    # 1. Équipement de test avec Token spécifique
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
        )
    ]

    # Génération du dashboard ThingsBoard
    dashboard = generate_thingsboard_dashboard(dev, vars_list)

    assert dashboard["title"] == "Supervision SCADA - Chaudière Test #1"
    assert "TB_TOKEN_SECRET_9876" in dashboard["configuration"]["description"]

    # Vérification de l'alias d'entité (singleEntity avec ID placeholder pour assistant ThingsBoard)
    aliases = dashboard["configuration"]["entityAliases"]
    assert len(aliases) == 1
    alias = list(aliases.values())[0]
    assert alias["alias"] == "Chaudière Test #1"
    assert alias["filter"]["type"] == "singleEntity"
    assert alias["filter"]["singleEntity"]["id"] == "00000000-0000-0000-0000-000000000000"

    # Vérification des widgets
    widgets = dashboard["configuration"]["widgets"]
    assert len(widgets) >= 4  # Header + Synoptique SCADA + Jauges + Graphique + Carte Attributs

    # Vérification du synoptique SCADA (html_value_card dynamique temps réel)
    synoptic_w = next(w for w in widgets.values() if "Synoptique SCADA" in w.get("title", ""))
    assert synoptic_w.get("typeFullFqn") == "system.cards.html_value_card"
    assert synoptic_w.get("typeAlias") == "html_value_card"
    assert synoptic_w.get("type") == "latest"
    assert len(synoptic_w["config"]["datasources"][0]["dataKeys"]) >= 2
    assert "<svg" in synoptic_w["config"]["settings"]["cardHtml"]
    assert synoptic_w["config"]["settings"]["cardHtml"] == synoptic_w["config"]["settings"]["html"]
    assert "pipe-flow" in synoptic_w["config"]["settings"]["cardHtml"]
    assert "${" in synoptic_w["config"]["settings"]["cardHtml"]

    # Vérification du widget d'en-tête (HTML) avec le token
    header_w = next(w for w in widgets.values() if w.get("typeAlias") == "html_card" and "Informations" in w.get("title", ""))
    assert header_w.get("typeFullFqn") == "system.cards.html_card"
    assert "TB_TOKEN_SECRET_9876" in header_w["config"]["settings"]["cardHtml"]
    assert header_w["config"]["settings"]["cardHtml"] == header_w["config"]["settings"]["html"]
    assert "Chaudière Test #1" in header_w["config"]["settings"]["cardHtml"]
    assert "MQTT" in header_w["config"]["settings"]["cardHtml"]

    # Vérification des jauges JustGage FQN
    gauge_w = next(w for w in widgets.values() if w.get("typeAlias") == "simple_gauge_justgage")
    assert gauge_w.get("typeFullFqn") == "system.digital_gauges.simple_gauge_justgage"
    assert gauge_w.get("bundleAlias") == "digital_gauges"

    # Vérification du graphique timeseries
    chart_w = next(w for w in widgets.values() if w.get("typeAlias") == "basic_timeseries")
    assert chart_w.get("typeFullFqn") == "system.charts.basic_timeseries"
    assert chart_w.get("bundleAlias") == "charts"
    ds = chart_w["config"]["datasources"][0]
    datakeys = [dk["name"] for dk in ds["dataKeys"]]
    assert "v_steam_press" in datakeys
    assert "v_flame_temp" in datakeys

    # Vérification de la carte d'attributs (entities_table)
    attr_w = next(w for w in widgets.values() if w.get("typeAlias") == "entities_table")
    assert attr_w.get("typeFullFqn") == "system.cards.entities_table"
    assert attr_w.get("bundleAlias") == "cards"
    attr_ds = attr_w["config"]["datasources"][0]
    attr_keys = [dk["name"] for dk in attr_ds["dataKeys"]]
    assert "v_burner_status" in attr_keys

    # Vérification de la sérialisation JSON valide
    serialized = json.dumps(dashboard)
    assert len(serialized) > 1000

if __name__ == "__main__":
    test_thingsboard_dashboard_generation()
    print("✅ test_thingsboard_dashboard_generation passed successfully!")
