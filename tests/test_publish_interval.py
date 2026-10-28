"""
Unit Tests for Device-Level Cadence Cascading
=============================================
Validates propagation of device `publish_interval` updates to associated variables,
variable-specific overrides, and disk persistence in StorageRepository.
"""

import os
import sys
import shutil
import tempfile
import types

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
        @classmethod
        def model_validate(cls, data):
            if isinstance(data, cls):
                return data
            return cls(**data)
        def model_dump(self):
            res = {}
            for k, v in self.__dict__.items():
                if hasattr(v, 'model_dump'):
                    res[k] = v.model_dump()
                elif isinstance(v, list):
                    res[k] = [x.model_dump() if hasattr(x, 'model_dump') else x for x in v]
                elif hasattr(v, 'value'):
                    res[k] = v.value
                else:
                    res[k] = v
            return res
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
from app.storage.repository import StorageRepository


def test_device_publish_interval_cascade():
    """Validates cascading cadence changes from parent device to associated variables."""
    tmp_dir = tempfile.mkdtemp()
    tmp_file = os.path.join(tmp_dir, "test_simulator_state.json")
    try:
        repo = StorageRepository(file_path=tmp_file)

        # 1. Create a device without global publish_interval
        dev1 = DeviceConfig(id="pump_01", name="Pompe Primaire", platform=PlatformType.GENERIC)
        repo.save_device(dev1)

        v1 = VariableConfig(
            id="p1_flow",
            name="Débit",
            device_id="pump_01",
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            publish_interval=5.0,
            sim_mode=SimMode.SINE,
            math_config=MathConfig(min_val=10.0, max_val=20.0),
        )
        v2 = VariableConfig(
            id="p1_pressure",
            name="Pression",
            device_id="pump_01",
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            publish_interval=10.0,
            sim_mode=SimMode.SINE,
            math_config=MathConfig(min_val=1.0, max_val=5.0),
        )
        repo.save_variable(v1)
        repo.save_variable(v2)

        # Verify initial intervals
        assert repo.get_variable("p1_flow").publish_interval == 5.0
        assert repo.get_variable("p1_pressure").publish_interval == 10.0

        # 2. Update device with global publish_interval of 2.5s
        dev1.publish_interval = 2.5
        repo.save_device(dev1)

        # Both variables should now cascade to 2.5s
        flow_var = repo.get_variable("p1_flow")
        press_var = repo.get_variable("p1_pressure")
        assert flow_var.publish_interval == 2.5
        assert press_var.publish_interval == 2.5

        # 3. Individual variable override
        flow_var.publish_interval = 0.5
        repo.save_variable(flow_var)

        assert repo.get_variable("p1_flow").publish_interval == 0.5
        assert repo.get_variable("p1_pressure").publish_interval == 2.5

        # 4. Subsequent device-level override
        dev1.publish_interval = 1.0
        repo.save_device(dev1)

        assert repo.get_variable("p1_flow").publish_interval == 1.0
        assert repo.get_variable("p1_pressure").publish_interval == 1.0

        # 5. Unrelated device isolation
        dev2 = DeviceConfig(id="meter_01", name="Compteur", platform=PlatformType.GENERIC, publish_interval=15.0)
        repo.save_device(dev2)
        v_meter = VariableConfig(
            id="m1_index",
            name="Index",
            device_id="meter_01",
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            publish_interval=60.0,
            sim_mode=SimMode.SINE,
            math_config=MathConfig(min_val=100.0, max_val=200.0),
        )
        repo.save_variable(v_meter)
        assert repo.get_variable("m1_index").publish_interval == 60.0

        dev2.publish_interval = 12.0
        repo.save_device(dev2)
        assert repo.get_variable("m1_index").publish_interval == 12.0
        # pump_01 remains unaffected
        assert repo.get_variable("p1_flow").publish_interval == 1.0

        # 6. Verify file reload persistence
        repo_reloaded = StorageRepository(file_path=tmp_file)
        assert repo_reloaded.get_device("pump_01").publish_interval == 1.0
        assert repo_reloaded.get_variable("p1_flow").publish_interval == 1.0
        assert repo_reloaded.get_variable("p1_pressure").publish_interval == 1.0

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_device_publish_interval_cascade()
    print("✅ All tests passed successfully!")
