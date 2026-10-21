import json
import os
import shutil
import tempfile
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

    # Vérification de l'alias d'entité
    aliases = dashboard["configuration"]["entityAliases"]
    assert len(aliases) == 1
    alias = list(aliases.values())[0]
    assert alias["alias"] == "Chaudière Test #1"
    assert alias["filter"]["type"] == "entityName"
    assert alias["filter"]["entityNameFilter"] == "Chaudière Test #1"

    # Vérification des widgets
    widgets = dashboard["configuration"]["widgets"]
    assert len(widgets) >= 4  # Header + Synoptique SCADA + Jauges + Graphique + Carte Attributs

    # Vérification du synoptique SCADA
    synoptic_w = next(w for w in widgets.values() if "Synoptique SCADA" in w.get("title", ""))
    assert "<svg" in synoptic_w["config"]["settings"]["html"]
    assert "pipe-flow" in synoptic_w["config"]["settings"]["html"]

    # Vérification du widget d'en-tête (HTML) avec le token
    header_w = next(w for w in widgets.values() if w.get("typeAlias") == "html_card")
    assert "TB_TOKEN_SECRET_9876" in header_w["config"]["settings"]["html"]
    assert "Chaudière Test #1" in header_w["config"]["settings"]["html"]
    assert "MQTT" in header_w["config"]["settings"]["html"]

    # Vérification du graphique timeseries
    chart_w = next(w for w in widgets.values() if w.get("typeAlias") == "timeseries")
    ds = chart_w["config"]["datasources"][0]
    datakeys = [dk["name"] for dk in ds["dataKeys"]]
    assert "v_steam_press" in datakeys
    assert "v_flame_temp" in datakeys

    # Vérification de la carte d'attributs
    attr_w = next(w for w in widgets.values() if w.get("typeAlias") == "latest_values")
    attr_ds = attr_w["config"]["datasources"][0]
    attr_keys = [dk["name"] for dk in attr_ds["dataKeys"]]
    assert "v_burner_status" in attr_keys

    # Vérification de la sérialisation JSON valide
    serialized = json.dumps(dashboard)
    assert len(serialized) > 1000

if __name__ == "__main__":
    test_thingsboard_dashboard_generation()
    print("✅ test_thingsboard_dashboard_generation passed successfully!")
