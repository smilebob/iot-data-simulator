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
    """Retourne l'adaptateur de plateforme correspondant."""
    return _ADAPTERS.get(platform, _ADAPTERS[PlatformType.GENERIC])

__all__ = [
    "BasePlatformAdapter",
    "ThingsBoardAdapter",
    "HomeAssistantAdapter",
    "DatacakeAdapter",
    "GenericMqttAdapter",
    "get_adapter",
]
