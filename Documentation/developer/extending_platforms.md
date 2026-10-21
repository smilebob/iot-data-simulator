# 🔌 Guide d'Extension : Ajouter une Nouvelle Plateforme IoT

L'application est conçue pour être étendue très facilement grâce au pattern **Adapter**. Ce guide explique comment ajouter le support d'une nouvelle plateforme (par exemple **AWS IoT Core** ou **Azure IoT Hub**).

---

## Étape 1 : Déclarer la nouvelle plateforme dans l'Enum

Dans [app/models/device.py](file:///home/pierre/Projets/iot-data-simulator/app/models/device.py), ajoutez la valeur à l'énumération `PlatformType` :

```python
class PlatformType(str, Enum):
    THINGSBOARD = "thingsboard"
    HOMEASSISTANT = "homeassistant"
    DATACAKE = "datacake"
    GENERIC = "generic"
    AWSIOT = "awsiot"  # <-- Nouvelle plateforme
```

---

## Étape 2 : Créer la classe Adaptateur

Créez un nouveau fichier dans `app/platforms/awsiot.py` héritant de `BasePlatformAdapter` :

```python
import json
from typing import Any, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig
from app.platforms.base import BasePlatformAdapter

class AwsIotAdapter(BasePlatformAdapter):
    """
    Connecteur pour AWS IoT Core.
    Publie sur le topic 'dt/myorg/{device_id}/{var_id}' au format shadow ou JSON standard.
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        return f"dt/simulated/{device.id}/{variable.id}"

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        # Utiliser le topic customisé si renseigné, sinon le topic par défaut
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)

        # Structure de message AWS IoT
        payload = json.dumps({
            "deviceId": device.id,
            "metric": variable.id,
            "val": value,
            "unit": variable.unit,
            "timestamp": timestamp_ms
        })

        return topic, payload
```

---

## Étape 3 : Enregistrer l'Adaptateur dans la Factory

Dans [app/platforms/__init__.py](file:///home/pierre/Projets/iot-data-simulator/app/platforms/__init__.py), importez et déclarez votre adaptateur :

```python
from app.platforms.awsiot import AwsIotAdapter

_ADAPTERS: dict[PlatformType, BasePlatformAdapter] = {
    PlatformType.THINGSBOARD: ThingsBoardAdapter(),
    PlatformType.HOMEASSISTANT: HomeAssistantAdapter(),
    PlatformType.DATACAKE: DatacakeAdapter(),
    PlatformType.GENERIC: GenericMqttAdapter(),
    PlatformType.AWSIOT: AwsIotAdapter(),  # <-- Enregistrement ici
}
```

---

## Étape 4 : Ajouter l'option dans la Web GUI

Dans [app/static/index.html](file:///home/pierre/Projets/iot-data-simulator/app/static/index.html), ajoutez l'option dans le menu déroulant du modal équipement (`#dev-platform`) :

```html
<option value="awsiot">AWS IoT Core (Topics dt/...)</option>
```

C'est terminé ! Votre nouvelle plateforme est immédiatement reconnue par l'interface web, le moteur de publication, et le stockage persistant.
