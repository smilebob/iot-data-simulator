from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType

class BasePlatformAdapter(ABC):
    """
    Classe de base abstraite pour les connecteurs de plateformes IoT.
    Permet une extensibilité totale (ThingsBoard, Home Assistant, Datacake, etc.).
    """

    @abstractmethod
    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        """Retourne le topic MQTT par défaut pour cette plateforme et cette variable."""
        pass

    @abstractmethod
    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        """
        Formate le message MQTT.
        Retourne (topic, payload_string).
        """
        pass

    def get_discovery_messages(
        self,
        device: DeviceConfig,
        variables: List[VariableConfig],
    ) -> List[Tuple[str, str]]:
        """
        Génère les messages de découverte automatique (ex: MQTT Discovery pour Home Assistant).
        Par défaut vide.
        """
        return []

    def handle_incoming_message(
        self,
        topic: str,
        payload: str,
    ) -> Optional[Tuple[str, Any]]:
        """
        Traite un message entrant (ex: RPC ThingsBoard, commande Home Assistant).
        Retourne (variable_id_ou_method, value) ou None.
        """
        return None
