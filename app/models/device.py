from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class PlatformType(str, Enum):
    THINGSBOARD = "thingsboard"
    HOMEASSISTANT = "homeassistant"
    DATACAKE = "datacake"
    GENERIC = "generic"

class TransportProtocol(str, Enum):
    MQTT = "mqtt"
    HTTP = "http"
    COAP = "coap"

class DeviceConfig(BaseModel):
    id: str = Field(..., description="Identifiant unique de l'équipement")
    name: str = Field(..., description="Nom d'affichage de l'équipement")
    platform: PlatformType = Field(default=PlatformType.THINGSBOARD, description="Plateforme IoT cible")
    token: Optional[str] = Field(default=None, description="Token d'authentification (ThingsBoard Device Token ou Datacake Token)")
    protocol: TransportProtocol = Field(default=TransportProtocol.MQTT, description="Protocole de communication (MQTT, HTTP, CoAP)")
    custom_host: Optional[str] = Field(default=None, description="Hôte spécifique (hérite du serveur par défaut si non renseigné)")
    custom_port: Optional[int] = Field(default=None, description="Port spécifique (déduit selon le protocole si non renseigné)")
    use_tls: Optional[bool] = Field(default=None, description="Chiffrement TLS / HTTPS / CoAPS")
    enabled: bool = Field(default=True, description="Équipement actif")
