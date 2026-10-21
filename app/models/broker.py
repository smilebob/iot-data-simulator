from pydantic import BaseModel, Field
from typing import Optional

class BrokerConfig(BaseModel):
    host: str = Field(default="mosquitto", description="Adresse IP ou nom d'hôte du broker MQTT")
    port: int = Field(default=1883, description="Port MQTT (1883 standard, 8883 TLS)")
    use_tls: bool = Field(default=False, description="Activer le chiffrement TLS/MQTTS")
    ca_cert_path: Optional[str] = Field(default=None, description="Chemin vers le certificat CA racine si TLS activé")
    username: Optional[str] = Field(default=None, description="Nom d'utilisateur ou Token ThingsBoard")
    password: Optional[str] = Field(default=None, description="Mot de passe MQTT")
    transport: str = Field(default="tcp", description="Protocole de transport: 'tcp' (standard) ou 'websockets' (WSS)")
    ws_path: str = Field(default="/mqtt", description="Chemin WebSocket si transport='websockets'")
    client_id_prefix: str = Field(default="iot_sim_", description="Préfixe du client MQTT")
    keepalive: int = Field(default=60, description="Délai de KeepAlive en secondes")
