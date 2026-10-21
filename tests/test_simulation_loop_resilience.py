import sys
import os
import types
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Standalone mocks for test execution outside container
if 'pydantic' not in sys.modules:
    pyd = types.ModuleType('pydantic')
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items(): setattr(self, k, v)
        def model_copy(self, deep=True):
            import copy; return copy.deepcopy(self)
        def model_dump(self):
            res = {}
            for k, v in self.__dict__.items():
                if hasattr(v, "model_dump"):
                    res[k] = v.model_dump()
                elif isinstance(v, list):
                    res[k] = [i.model_dump() if hasattr(i, "model_dump") else (i.value if hasattr(i, "value") else i) for i in v]
                elif hasattr(v, "value"):
                    res[k] = v.value
                else:
                    res[k] = v
            return res
        @classmethod
        def model_validate(cls, data):
            if isinstance(data, dict): return cls(**data)
            return data
        @classmethod
        def model_construct(cls, **kwargs):
            return cls(**kwargs)
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
from app.models.variable import VariableConfig, VariableType, DataType, SimMode, MathConfig, AnomalyType
from app.core.engine import SimulationEngine
from app.storage.repository import StorageRepository


def test_sync_device_listeners_resilience():
    print("Testing _sync_device_listeners for MQTT and HTTP without crashes...")
    async def _async_test():
        repo = MagicMock()
        mqtt = MagicMock()
        transports = MagicMock()

        engine = SimulationEngine(repo, mqtt, transports)

        dev_mqtt = DeviceConfig(
            id="dev_pac_mqtt",
            name="PAC Heatpump MQTT",
            platform=PlatformType.THINGSBOARD,
            token="tb_token_pac",
            protocol=TransportProtocol.MQTT,
            enabled=True,
        )
        dev_http = DeviceConfig(
            id="dev_pac_http",
            name="PAC Heatpump HTTP",
            platform=PlatformType.THINGSBOARD,
            token="tb_token_http",
            protocol=TransportProtocol.HTTP,
            enabled=True,
        )

        devices_map = {
            dev_mqtt.id: dev_mqtt,
            dev_http.id: dev_http,
        }

        # Ne doit pas lever de NameError ni d'AttributeError (ex: TransportProtocol.MQTTS inexistant)
        engine._sync_device_listeners(devices_map)
        assert mqtt.get_or_create_device_client.called
        print("✓ _sync_device_listeners succeeded without errors!")
        # Nettoyer les tâches HTTP RPC créées
        for t in engine._http_rpc_tasks.values():
            t.cancel()

    asyncio.run(_async_test())


def test_storage_save_variables():
    print("Testing StorageRepository.save_variables...")
    test_file = "/tmp/test_save_variables.json"
    if os.path.exists(test_file): os.remove(test_file)
    if os.path.exists(f"{test_file}.bak"): os.remove(f"{test_file}.bak")

    repo = StorageRepository(file_path=test_file)
    v1 = VariableConfig(id="v1", name="Var 1", device_id="d1", current_value=10.5)
    v2 = VariableConfig(id="v2", name="Var 2", device_id="d1", current_value=20.0)

    repo.save_variables([v1, v2])
    assert repo.get_variable("v1").current_value == 10.5
    assert repo.get_variable("v2").current_value == 20.0
    print("✓ save_variables succeeded!")


def test_simulation_tick_and_ws_broadcast():
    print("Testing SimulationEngine single tick calculation and WS broadcast format...")
    test_file = "/tmp/test_sim_tick.json"
    if os.path.exists(test_file): os.remove(test_file)
    if os.path.exists(f"{test_file}.bak"): os.remove(f"{test_file}.bak")

    repo = StorageRepository(file_path=test_file)
    dev = DeviceConfig(
        id="pac_01",
        name="PAC",
        platform=PlatformType.THINGSBOARD,
        token="token123",
        protocol=TransportProtocol.MQTT,
        enabled=True,
    )
    repo.save_device(dev)

    var = VariableConfig(
        id="pac_01_temp",
        name="Temperature",
        device_id="pac_01",
        var_type=VariableType.TELEMETRY,
        data_type=DataType.FLOAT,
        sim_mode=SimMode.CONSTANT,
        math_config=MathConfig(constant_val=22.5),
        publish_interval=1.0,
        anomaly=AnomalyType.NONE,
    )
    repo.save_variable(var)

    mqtt = MagicMock()
    transports = MagicMock()
    transports.publish = AsyncMock(return_value=(True, "MQTT", "v1/devices/me/telemetry"))

    engine = SimulationEngine(repo, mqtt, transports)
    broadcasted_messages = []
    engine.register_ws_broadcast(lambda msg: broadcasted_messages.append(msg))

    async def run_single_tick():
        engine.is_running = True
        task = asyncio.create_task(engine._run_loop())
        await asyncio.sleep(0.6)
        engine.is_running = False
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_single_tick())

    assert len(broadcasted_messages) > 0, "No WebSocket message was broadcast!"
    pac_msgs = [m for m in broadcasted_messages if m.get("data", {}).get("variable_id") == "pac_01_temp"]
    assert len(pac_msgs) > 0, f"pac_01_temp not found in broadcast messages: {broadcasted_messages}"
    msg = pac_msgs[0]
    assert msg.get("type") == "telemetry", f"Message type should be 'telemetry', got {msg.get('type')}"
    data = msg.get("data", {})
    assert data.get("variable_id") == "pac_01_temp"
    assert data.get("value") == 22.5
    assert data.get("published") is True
    print("✓ Simulation loop tick, calculation, and WS broadcast format verified successfully!")


if __name__ == "__main__":
    test_sync_device_listeners_resilience()
    test_storage_save_variables()
    test_simulation_tick_and_ws_broadcast()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
