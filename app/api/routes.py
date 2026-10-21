from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.models.broker import BrokerConfig
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, AnomalyType
from app.core.replay import ReplayEngine
from app.platforms import get_adapter
from app.storage.repository import StorageRepository
from app.mqtt.client import MqttManager
from app.core.engine import SimulationEngine
from app.core.logger import log_handler
from app.mqtt.diagnostics import test_broker_connectivity
from app.api.auth import require_role
from app.models.user import UserRole
from app.core.equipment_catalog import (
    get_equipment_catalog,
    EquipmentPreset,
    InstantiatePresetRequest,
    instantiate_preset,
)

# Groupes de rôles RBAC
ROLE_ANY = [UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER]
ROLE_OPERATOR_OR_ADMIN = [UserRole.ADMIN, UserRole.OPERATOR]
ROLE_ADMIN_ONLY = [UserRole.ADMIN]

router = APIRouter(prefix="/api")

# Dépendances injectées depuis main.py
def get_repo() -> StorageRepository:
    from app.main import repository
    return repository

def get_engine() -> SimulationEngine:
    from app.main import engine
    return engine

def get_mqtt() -> MqttManager:
    from app.main import mqtt_manager
    return mqtt_manager

def get_transports():
    from app.main import transport_manager
    return transport_manager

# --- Équipements (Devices) ---
@router.get("/devices", response_model=List[DeviceConfig], dependencies=[Depends(require_role(ROLE_ANY))])
def list_devices(repo: StorageRepository = Depends(get_repo)):
    return repo.get_devices()

@router.post("/devices", response_model=DeviceConfig, dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def save_device(
    device: DeviceConfig,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
):
    repo.save_device(device)
    # Réinitialiser le client MQTT dédié pour appliquer les nouveaux tokens / paramètres
    mqtt.remove_device_client(device.id)
    return device

@router.delete("/devices/{device_id}", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def delete_device(
    device_id: str,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
):
    repo.delete_device(device_id)
    mqtt.remove_device_client(device_id)
    return {"status": "deleted", "device_id": device_id}

@router.post("/devices/test-custom", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def test_custom_device_communication(
    device: DeviceConfig,
    transports = Depends(get_transports),
):
    """Teste la communication directe (MQTT, HTTP, CoAP) selon la configuration spécifiée."""
    return await transports.test_device_communication(device)

@router.post("/devices/{device_id}/test", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def test_device_communication_by_id(
    device_id: str,
    repo: StorageRepository = Depends(get_repo),
    transports = Depends(get_transports),
):
    """Teste la communication d'un équipement existant."""
    device = repo.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Équipement non trouvé")
    return await transports.test_device_communication(device)

# --- Variables ---
@router.get("/variables", response_model=List[VariableConfig], dependencies=[Depends(require_role(ROLE_ANY))])
def list_variables(device_id: Optional[str] = None, repo: StorageRepository = Depends(get_repo)):
    return repo.get_variables(device_id=device_id)

@router.post("/variables", response_model=VariableConfig, dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def save_variable(
    var: VariableConfig,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
):
    # Si topic non défini, calculer le topic par défaut de la plateforme
    device = repo.get_device(var.device_id)
    if device and not var.topic:
        adapter = get_adapter(device.platform)
        var.topic = adapter.get_default_topic(device, var)

    repo.save_variable(var)

    # Si c'est Home Assistant, envoyer le message de découverte MQTT Discovery
    if device and device.platform.value == "homeassistant":
        adapter = get_adapter(device.platform)
        disc_msgs = adapter.get_discovery_messages(device, [var])
        client = mqtt.get_or_create_device_client(device.id, device.token)
        if client:
            for top, pay in disc_msgs:
                client.publish(top, pay, qos=1, retain=True)

    return var

@router.delete("/variables/{var_id}", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def delete_variable(var_id: str, repo: StorageRepository = Depends(get_repo)):
    repo.delete_variable(var_id)
    return {"status": "deleted", "var_id": var_id}

# --- Broker MQTT ---
@router.get("/broker", response_model=BrokerConfig, dependencies=[Depends(require_role(ROLE_ANY))])
def get_broker(repo: StorageRepository = Depends(get_repo)):
    return repo.get_broker()

@router.post("/broker", response_model=BrokerConfig, dependencies=[Depends(require_role(ROLE_ADMIN_ONLY))])
def update_broker(
    broker: BrokerConfig,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
):
    repo.save_broker(broker)
    mqtt.update_global_config(broker)
    return broker

@router.post("/broker/test", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def test_broker(broker: BrokerConfig):
    return test_broker_connectivity(broker)

# --- Logs & Outil de Traçabilité des Erreurs ---
@router.get("/logs", dependencies=[Depends(require_role(ROLE_ANY))])
def get_logs(level: Optional[str] = None, limit: int = 100):
    return log_handler.get_logs(level=level, limit=limit)

@router.delete("/logs", dependencies=[Depends(require_role(ROLE_ADMIN_ONLY))])
def clear_logs():
    log_handler.clear()
    return {"status": "cleared"}

# --- Statut & Contrôle du Simulateur ---
@router.get("/status", dependencies=[Depends(require_role(ROLE_ANY))])
def get_status(
    repo: StorageRepository = Depends(get_repo),
    engine: SimulationEngine = Depends(get_engine),
    mqtt: MqttManager = Depends(get_mqtt),
):
    from app.main import APP_VERSION
    client = mqtt.default_client
    return {
        "version": APP_VERSION,
        "engine_running": engine.is_running,
        "mqtt_connected": client.is_connected if client else False,
        "mqtt_error": client.last_error if client else None,
        "messages_published": client.messages_published if client else 0,
        "devices_count": len(repo.get_devices()),
        "variables_count": len(repo.get_variables()),
    }

@router.post("/simulation/start", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def start_simulation(engine: SimulationEngine = Depends(get_engine)):
    engine.start()
    return {"status": "running"}

@router.post("/simulation/stop", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def stop_simulation(engine: SimulationEngine = Depends(get_engine)):
    engine.stop()
    return {"status": "stopped"}

# --- Forçage Manuel & Anomalies (ThingsBoard Demo Features) ---
class OverrideRequest(BaseModel):
    manual_override: bool
    manual_value: Optional[Any] = None

@router.post("/variables/{var_id}/override", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def override_variable(
    var_id: str,
    req: OverrideRequest,
    repo: StorageRepository = Depends(get_repo),
):
    var = repo.get_variable(var_id)
    if not var:
        raise HTTPException(status_code=404, detail="Variable non trouvée")
    var.manual_override = req.manual_override
    var.manual_value = req.manual_value
    repo.save_variable(var)
    return {"status": "ok", "var_id": var_id, "manual_override": var.manual_override}

class AnomalyRequest(BaseModel):
    anomaly: AnomalyType
    magnitude: float = 50.0

@router.post("/variables/{var_id}/anomaly", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def trigger_anomaly(
    var_id: str,
    req: AnomalyRequest,
    engine: SimulationEngine = Depends(get_engine),
):
    engine.trigger_anomaly(var_id, req.anomaly, req.magnitude)
    return {"status": "ok", "var_id": var_id, "anomaly": req.anomaly.value}

# --- Importation CSV pour Tableau de Points ---
@router.post("/variables/{var_id}/csv", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def upload_csv_points(
    var_id: str,
    file: UploadFile = File(...),
    repo: StorageRepository = Depends(get_repo),
):
    var = repo.get_variable(var_id)
    if not var:
        raise HTTPException(status_code=404, detail="Variable non trouvée")
    
    content = (await file.read()).decode("utf-8", errors="replace")
    points = ReplayEngine.parse_csv_points(content)
    if not points:
        raise HTTPException(status_code=400, detail="Aucun point valide trouvé dans le fichier CSV")

    var.points_config.points = points
    repo.save_variable(var)
    return {"status": "ok", "points_imported": len(points)}

# --- Export / Import Scénario Complet ---
@router.get("/scenario/export", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def export_scenario(repo: StorageRepository = Depends(get_repo)):
    return repo.export_scenario()

@router.post("/scenario/import", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def import_scenario(
    data: Dict[str, Any],
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
):
    repo.import_scenario(data)
    mqtt.update_global_config(repo.get_broker())
    return {"status": "imported", "devices": len(repo.get_devices()), "variables": len(repo.get_variables())}

# --- Catalogue des Modèles d'Équipements Métiers ---
@router.get("/presets/catalog", response_model=List[EquipmentPreset], dependencies=[Depends(require_role(ROLE_ANY))])
def get_presets_catalog():
    """Retourne la bibliothèque des modèles d'équipements par axe métier."""
    return get_equipment_catalog()

@router.post("/presets/instantiate", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def instantiate_equipment_preset(
    req: InstantiatePresetRequest,
    repo: StorageRepository = Depends(get_repo),
):
    """Instancie un équipement métier avec toutes ses grandeurs et formules associées."""
    try:
        device, variables = instantiate_preset(req, repo)
        return {
            "status": "created",
            "device": device,
            "variables_count": len(variables),
            "variables": variables,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du modèle : {e}")

