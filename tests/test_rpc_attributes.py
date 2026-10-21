import json
import os
import sys
import types

# Mocks minimaux pour exécuter hors conteneur sans dépendances externes
if 'pydantic' not in sys.modules:
    pyd = types.ModuleType('pydantic')
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items(): setattr(self, k, v)
        def model_copy(self, deep=True):
            import copy; return copy.deepcopy(self)
        def model_dump(self): return self.__dict__
    def Field(default=None, default_factory=None, **kwargs):
        if default_factory: return default_factory()
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
from app.core.engine import SimulationEngine

class MockStorageRepository:
    def __init__(self, devices, variables):
        self.devices = {d.id: d for d in devices}
        self.variables = {v.id: v for v in variables}
        self.saved_variables = False

    def get_devices(self):
        return list(self.devices.values())

    def get_variables(self):
        return list(self.variables.values())

    def get_variable(self, var_id):
        return self.variables.get(var_id)

    def save_variables(self, vars_list):
        self.saved_variables = True
        for v in vars_list:
            self.variables[v.id] = v

class MockMqttManager:
    def __init__(self):
        self.published_messages = []
        self.on_rpc_callback = None

    def publish_device_message(self, device_id: str, topic: str, payload: str, qos: int = 1):
        self.published_messages.append((device_id, topic, payload))
        return True

def test_rpc_and_shared_attributes():
    # 1. Équipement PAC (Pompe à Chaleur) avec mode_chaud
    dev = DeviceConfig(
        id="bldg_heatpump_test",
        name="PAC Test",
        platform=PlatformType.THINGSBOARD,
        protocol=TransportProtocol.MQTT,
        token="TOKEN_PAC_TEST",
        enabled=True
    )

    var_mode = VariableConfig(
        id="bldg_heatpump_test_mode_chaud",
        name="Mode Fonctionnement Chaud",
        device_id="bldg_heatpump_test",
        var_type=VariableType.ATTRIBUTE,
        data_type=DataType.BOOLEAN,
        unit="",
        sim_mode=SimMode.CONSTANT,
        math_config=MathConfig(constant_val=True),
        enabled=True
    )

    repo = MockStorageRepository([dev], [var_mode])
    mqtt = MockMqttManager()
    engine = SimulationEngine(repository=repo, mqtt_manager=mqtt)

    assert var_mode.current_value is None or var_mode.current_value is True

    # Test 1 : Commande RPC 'set_mode_chaud' avec params = False
    rpc_topic = "v1/devices/me/rpc/request/101"
    rpc_payload = json.dumps({"method": "set_mode_chaud", "params": False})
    engine._handle_rpc("bldg_heatpump_test", rpc_topic, rpc_payload)

    # Vérifications
    assert var_mode.current_value is False
    assert var_mode.manual_override is True
    assert var_mode.manual_value is False

    # Vérification de l'acquittement RPC émis
    resp_msg = next((msg for msg in mqtt.published_messages if msg[1] == "v1/devices/me/rpc/response/101"), None)
    assert resp_msg is not None
    resp_data = json.loads(resp_msg[2])
    assert resp_data["status"] == "SUCCESS"
    assert resp_data["value"] is False

    # Vérification de la confirmation d'attribut
    attr_msg = next((msg for msg in mqtt.published_messages if msg[1] == "v1/devices/me/attributes"), None)
    assert attr_msg is not None
    assert "mode_chaud" in attr_msg[2]

    # Test 2 : Commande RPC standard 'setValue' avec params = True
    mqtt.published_messages.clear()
    rpc_topic2 = "v1/devices/me/rpc/request/102"
    rpc_payload2 = json.dumps({"method": "setValue", "params": True})
    engine._handle_rpc("bldg_heatpump_test", rpc_topic2, rpc_payload2)

    assert var_mode.current_value is True
    resp_msg2 = next((msg for msg in mqtt.published_messages if msg[1] == "v1/devices/me/rpc/response/102"), None)
    assert resp_msg2 is not None
    assert json.loads(resp_msg2[2])["value"] is True

    # Test 3 : Mise à jour par Attribut Partagé ThingsBoard (Shared Attributes)
    mqtt.published_messages.clear()
    attr_update_topic = "v1/devices/me/attributes"
    attr_update_payload = json.dumps({"mode_chaud": False})
    engine._handle_rpc("bldg_heatpump_test", attr_update_topic, attr_update_payload)

    assert var_mode.current_value is False
    assert var_mode.manual_override is True

    # Test 4 : Commande RPC de lecture 'getValue'
    mqtt.published_messages.clear()
    rpc_topic4 = "v1/devices/me/rpc/request/103"
    rpc_payload4 = json.dumps({"method": "getValue"})
    engine._handle_rpc("bldg_heatpump_test", rpc_topic4, rpc_payload4)

    resp_msg4 = next((msg for msg in mqtt.published_messages if msg[1] == "v1/devices/me/rpc/response/103"), None)
    assert resp_msg4 is not None
    assert json.loads(resp_msg4[2])["value"] is False

    print("✅ test_rpc_and_shared_attributes passed successfully!")

if __name__ == "__main__":
    test_rpc_and_shared_attributes()
