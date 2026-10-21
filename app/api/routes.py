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

# --- Équipements (Devices) ---
@router.get("/devices", response_model=List[DeviceConfig])
def list_devices(repo: StorageRepository = Depends(get_repo)):
    return repo.get_devices()

@router.post("/devices", response_model=DeviceConfig)
def save_device(device: DeviceConfig, repo: StorageRepository = Depends(get_repo)):
    repo.save_device(device)
    return device

@router.delete("/devices/{device_id}")
def delete_device(device_id: str, repo: StorageRepository = Depends(get_repo)):
    repo.delete_device(device_id)
    return {"status": "deleted", "device_id": device_id}

# --- Variables ---
@router.get("/variables", response_model=List[VariableConfig])
def list_variables(device_id: Optional[str] = None, repo: StorageRepository = Depends(get_repo)):
    return repo.get_variables(device_id=device_id)

@router.post("/variables", response_model=VariableConfig)
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

@router.delete("/variables/{var_id}")
def delete_variable(var_id: str, repo: StorageRepository = Depends(get_repo)):
    repo.delete_variable(var_id)
    return {"status": "deleted", "var_id": var_id}

# --- Broker MQTT ---
@router.get("/broker", response_model=BrokerConfig)
def get_broker(repo: StorageRepository = Depends(get_repo)):
    return repo.get_broker()

@router.post("/broker", response_model=BrokerConfig)
def update_broker(
    broker: BrokerConfig,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
):
    repo.save_broker(broker)
    mqtt.update_global_config(broker)
    return broker

# --- Statut & Contrôle du Simulateur ---
@router.get("/status")
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

@router.post("/simulation/start")
def start_simulation(engine: SimulationEngine = Depends(get_engine)):
    engine.start()
    return {"status": "running"}

@router.post("/simulation/stop")
def stop_simulation(engine: SimulationEngine = Depends(get_engine)):
    engine.stop()
    return {"status": "stopped"}

# --- Forçage Manuel & Anomalies (ThingsBoard Demo Features) ---
class OverrideRequest(BaseModel):
    manual_override: bool
    manual_value: Optional[Any] = None

@router.post("/variables/{var_id}/override")
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

@router.post("/variables/{var_id}/anomaly")
def trigger_anomaly(
    var_id: str,
    req: AnomalyRequest,
    engine: SimulationEngine = Depends(get_engine),
):
    engine.trigger_anomaly(var_id, req.anomaly, req.magnitude)
    return {"status": "ok", "var_id": var_id, "anomaly": req.anomaly.value}

# --- Importation CSV pour Tableau de Points ---
@router.post("/variables/{var_id}/csv")
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
@router.get("/scenario/export")
def export_scenario(repo: StorageRepository = Depends(get_repo)):
    return repo.export_scenario()

@router.post("/scenario/import")
def import_scenario(
    data: Dict[str, Any],
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
):
    repo.import_scenario(data)
    mqtt.update_global_config(repo.get_broker())
    return {"status": "imported", "devices": len(repo.get_devices()), "variables": len(repo.get_variables())}
