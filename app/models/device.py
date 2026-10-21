from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class PlatformType(str, Enum):
    THINGSBOARD = "thingsboard"
    HOMEASSISTANT = "homeassistant"
    DATACAKE = "datacake"
    GENERIC = "generic"

class DeviceConfig(BaseModel):
    id: str = Field(..., description="Identifiant unique de l'équipement")
    name: str = Field(..., description="Nom d'affichage de l'équipement")
    platform: PlatformType = Field(default=PlatformType.THINGSBOARD, description="Plateforme IoT cible")
    token: Optional[str] = Field(default=None, description="Token d'authentification (ThingsBoard Device Token ou Datacake Token)")
    enabled: bool = Field(default=True, description="Équipement actif")
