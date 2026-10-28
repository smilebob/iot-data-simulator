"""
IoT platform adapters registry and factory dispatch.

Provides unified lookup for platform-specific formatters:
- `THINGSBOARD`: ThingsBoard Community and Professional Edition (MQTT/HTTP/CoAP).
- `HOMEASSISTANT`: Home Assistant with MQTT Discovery auto-detection.
- `DATACAKE`: Datacake Cloud IoT platform.
- `GENERIC`: Standard hierarchical MQTT format.
"""

from app.models.device import PlatformType
from app.platforms.base import BasePlatformAdapter
from app.platforms.thingsboard import ThingsBoardAdapter
from app.platforms.homeassistant import HomeAssistantAdapter
from app.platforms.datacake import DatacakeAdapter
from app.platforms.generic import GenericMqttAdapter

_ADAPTERS: dict[PlatformType, BasePlatformAdapter] = {
    PlatformType.THINGSBOARD: ThingsBoardAdapter(),
    PlatformType.HOMEASSISTANT: HomeAssistantAdapter(),
    PlatformType.DATACAKE: DatacakeAdapter(),
    PlatformType.GENERIC: GenericMqttAdapter(),
}

def get_adapter(platform: PlatformType) -> BasePlatformAdapter:
    """
    Returns the singleton adapter registered for the specified IoT platform.

    Falls back to `GenericMqttAdapter` if the platform type is unrecognized.

    Args:
        platform: PlatformType enum value.

    Returns:
        BasePlatformAdapter: Platform adapter instance.
    """
    return _ADAPTERS.get(platform, _ADAPTERS[PlatformType.GENERIC])

__all__ = [
    "BasePlatformAdapter",
    "ThingsBoardAdapter",
    "HomeAssistantAdapter",
    "DatacakeAdapter",
    "GenericMqttAdapter",
    "get_adapter",
]

