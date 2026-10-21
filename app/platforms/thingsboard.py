import json
from typing import Any, Optional, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType
from app.platforms.base import BasePlatformAdapter

class ThingsBoardAdapter(BasePlatformAdapter):
    """
    Connecteur pour la plateforme ThingsBoard.
    Gère :
    - Télémétrie standard (v1/devices/me/telemetry) avec horodatage millisecondes
    - Attributs client / serveur (v1/devices/me/attributes)
    - Commandes RPC bidirectionnelles (v1/devices/me/rpc/request/+)
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        if variable.var_type == VariableType.ATTRIBUTE:
            return "v1/devices/me/attributes"
        return "v1/devices/me/telemetry"

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        # Topic personnalisé ou défaut ThingsBoard
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)

        # Structure native ThingsBoard avec horodatage
        if variable.var_type == VariableType.ATTRIBUTE:
            payload = json.dumps({variable.id: value})
        else:
            # Format horodaté ThingsBoard
            payload = json.dumps({
                "ts": timestamp_ms,
                "values": {
                    variable.id: value
                }
            })

        return topic, payload

    def handle_incoming_message(
        self,
        topic: str,
        payload: str,
    ) -> Optional[Tuple[str, Any]]:
        # Analyse des requêtes RPC ThingsBoard
        if "v1/devices/me/rpc/request/" in topic:
            try:
                data = json.loads(payload)
                method = data.get("method")
                params = data.get("params")
                return method, params
            except Exception:
                return None
        return None
