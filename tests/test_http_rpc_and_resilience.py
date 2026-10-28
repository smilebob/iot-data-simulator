"""
Unit Tests for HTTP RPC Long-Polling and Storage Resilience
===========================================================
Validates automatic recovery from corrupted storage via `.bak` backups
and bidirectional ThingsBoard HTTP RPC execution (setters and toggles).
"""

import json
import os
import sys
import types
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Lightweight mock stubs for standalone testing outside container environment
if 'pydantic' not in sys.modules:
    pyd = types.ModuleType('pydantic')
    class BaseModel:
        """Mock BaseModel."""
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
from app.models.variable import VariableConfig, VariableType, DataType, SimMode, MathConfig
from app.core.engine import SimulationEngine
from app.storage.repository import StorageRepository


def test_storage_resilience():
    """Validates that storage automatically recovers from .bak backup when state file is corrupted."""
    print("Testing StorageRepository resilience & backup mechanism...")
    test_file = "/tmp/test_simulator_state.json"
    if os.path.exists(test_file): os.remove(test_file)
    if os.path.exists(f"{test_file}.bak"): os.remove(f"{test_file}.bak")

    # 1. Save state with a custom device and attribute
    repo = StorageRepository(file_path=test_file)
    dev = DeviceConfig(
        id="pac_test_01",
        name="PAC Réversible Démo",
        platform=PlatformType.THINGSBOARD,
        token="token_test_123",
        protocol=TransportProtocol.HTTP,
        enabled=True,
    )
    repo.save_device(dev)
    var = VariableConfig(
        id="pac_test_01_mode_chaud",
        name="Mode Chaud",
        device_id="pac_test_01",
        var_type=VariableType.ATTRIBUTE,
        data_type=DataType.BOOLEAN,
        current_value=True,
    )
    repo.save_variable(var)

    assert os.path.exists(test_file)
    assert os.path.exists(f"{test_file}.bak")

    # 2. Normal reload
    repo2 = StorageRepository(file_path=test_file)
    assert "pac_test_01" in repo2.devices
    assert "pac_test_01_mode_chaud" in repo2.variables

    # 3. Simulate file corruption (e.g. sudden power failure during write)
    with open(test_file, "w") as f:
        f.write("{ INVALID JSON CONTENT !!!")

    # Reload must automatically restore from .bak backup without losing state
    repo3 = StorageRepository(file_path=test_file)
    assert "pac_test_01" in repo3.devices
    assert "pac_test_01_mode_chaud" in repo3.variables
    print("✓ Storage resilience validated: Corrupted file automatically recovered from .bak without losing user devices!")

    # Cleanup
    for p in [test_file, f"{test_file}.bak"]:
        if os.path.exists(p): os.remove(p)


def test_http_rpc_and_control():
    """Validates HTTP RPC handler for ThingsBoard interactive widgets (setters and toggles)."""
    print("Testing HTTP RPC Long-Polling and bidirectional switch response...")
    dev = DeviceConfig(
        id="bldg_heatpump_3e2c",
        name="PAC Réversible",
        platform=PlatformType.THINGSBOARD,
        token="c548cizzuynuke4c9ycm",
        protocol=TransportProtocol.HTTP,
        enabled=True,
    )
    var = VariableConfig(
        id="bldg_heatpump_3e2c_mode_chaud",
        name="Mode Chaud",
        device_id="bldg_heatpump_3e2c",
        var_type=VariableType.ATTRIBUTE,
        data_type=DataType.BOOLEAN,
        current_value=False,
    )

    class MockRepo:
        def __init__(self):
            self.devices = {dev.id: dev}
            self.variables = {var.id: var}
            self.broker_config = types.SimpleNamespace(host="easythings.app.test", port=1883)
        def get_devices(self): return list(self.devices.values())
        def get_variables(self): return list(self.variables.values())
        def get_broker(self): return self.broker_config
        def save_variables(self, vars): pass

    class MockMqtt:
        def __init__(self): self.published = []
        def publish_device_message(self, dev_id, topic, payload, qos=1):
            self.published.append((dev_id, topic, payload))
        def get_or_create_device_client(self, dev_id, token): return None

    class MockTransportManager:
        def __init__(self):
            self.http = types.SimpleNamespace(
                poll_rpc=AsyncMock(return_value={"id": 42, "method": "set_mode_chaud", "params": True}),
                respond_rpc=AsyncMock(return_value=True),
                post_payload=AsyncMock(return_value=(True, "OK")),
            )

    repo = MockRepo()
    mqtt = MockMqtt()
    transports = MockTransportManager()

    engine = SimulationEngine(repo, mqtt, transports)

    # Test direct RPC method dispatch
    ret = engine._handle_rpc("bldg_heatpump_3e2c", "v1/devices/me/rpc/request/42", '{"method": "set_mode_chaud", "params": true}')
    assert ret is True
    assert var.current_value is True
    assert var.manual_override is True

    # Test toggle dispatch
    ret_toggle = engine._handle_rpc("bldg_heatpump_3e2c", "v1/devices/me/rpc/request/43", '{"method": "toggle_mode_chaud"}')
    assert ret_toggle is False
    assert var.current_value is False

    print("✓ HTTP RPC & bidirectional switch control test passed successfully!")


if __name__ == "__main__":
    test_storage_resilience()
    test_http_rpc_and_control()

if __name__ == "__main__":
    test_storage_resilience()
    test_http_rpc_and_control()
