"""
FastAPI REST API Routes for IoT Data Simulator.

This module exposes endpoints for complete simulation orchestration:
- Device Management (`/api/devices`): CRUD, connectivity diagnostics, ThingsBoard dashboard generation.
- Variable Management (`/api/variables`): CRUD, platform default topic resolution, Home Assistant discovery.
- Broker Management (`/api/broker`): Settings persistence, dynamic hot-reload, connectivity diagnostics.
- Simulation Engine (`/api/status`, `/api/simulation/start`, `/api/simulation/stop`): Lifecycle control.
- Manual Overrides & Anomalies (`/api/variables/{id}/override`, `/api/variables/{id}/anomaly`): Demo controls.
- Replay & Data Import (`/api/variables/{id}/csv`): CSV time-series ingestion.
- Scenario Snapshots (`/api/scenario/export`, `/api/scenario/import`): Full state backup and restore.
- Equipment Catalog (`/api/presets/...`): Built-in industrial presets, 1-click instantiation, export/import bundles.
- Logging & Observability (`/api/logs`): In-memory ring buffer inspection and clearance.
"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import Response
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
from app.core.dashboard_generator import generate_thingsboard_dashboard
from app.core.equipment_catalog import (
    get_equipment_catalog,
    EquipmentPreset,
    InstantiatePresetRequest,
    instantiate_preset,
    build_preset_export_package,
    build_all_presets_export_package,
    import_preset_data,
    delete_custom_preset,
)

# RBAC Role Groups
ROLE_ANY = [UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER]
ROLE_OPERATOR_OR_ADMIN = [UserRole.ADMIN, UserRole.OPERATOR]
ROLE_ADMIN_ONLY = [UserRole.ADMIN]

router = APIRouter(prefix="/api")

# Dependencies injected from main.py
def get_repo() -> StorageRepository:
    """Dependency provider returning singleton StorageRepository."""
    from app.main import repository
    return repository

def get_engine() -> SimulationEngine:
    """Dependency provider returning singleton SimulationEngine."""
    from app.main import engine
    return engine

def get_mqtt() -> MqttManager:
    """Dependency provider returning singleton MqttManager."""
    from app.main import mqtt_manager
    return mqtt_manager

def get_transports():
    """Dependency provider returning singleton TransportManager."""
    from app.main import transport_manager
    return transport_manager

# --- Devices ---
@router.get("/devices", response_model=List[DeviceConfig], dependencies=[Depends(require_role(ROLE_ANY))])
def list_devices(repo: StorageRepository = Depends(get_repo)) -> List[DeviceConfig]:
    """Retrieves all registered devices."""
    return repo.get_devices()

@router.post("/devices", response_model=DeviceConfig, dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def save_device(
    device: DeviceConfig,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
) -> DeviceConfig:
    """Saves or updates a device and reconfigures dedicated MQTT client if needed."""
    repo.save_device(device)
    mqtt.remove_device_client(device.id)
    return device

@router.delete("/devices/{device_id}", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def delete_device(
    device_id: str,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
) -> dict:
    """Deletes a device, cascades to child variables, and tears down its MQTT client."""
    repo.delete_device(device_id)
    mqtt.remove_device_client(device_id)
    return {"status": "deleted", "device_id": device_id}

@router.post("/devices/test-custom", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def test_custom_device_communication(
    device: DeviceConfig,
    transports = Depends(get_transports),
) -> Dict[str, Any]:
    """Tests direct communication (MQTT, HTTP, CoAP) according to provided device configuration."""
    return await transports.test_device_communication(device)

@router.post("/devices/{device_id}/test", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def test_device_communication_by_id(
    device_id: str,
    repo: StorageRepository = Depends(get_repo),
    transports = Depends(get_transports),
) -> Dict[str, Any]:
    """Tests communication for an existing registered device."""
    device = repo.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Équipement non trouvé")
    return await transports.test_device_communication(device)

@router.get("/devices/{device_id}/thingsboard-dashboard", dependencies=[Depends(require_role(ROLE_ANY))])
def download_device_thingsboard_dashboard(
    device_id: str,
    repo: StorageRepository = Depends(get_repo),
) -> Response:
    """Generates and downloads a pre-configured ThingsBoard dashboard JSON for this device."""
    device = repo.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Équipement '{device_id}' introuvable.")
    variables = repo.get_variables(device_id)
    dashboard_data = generate_thingsboard_dashboard(device, variables)

    filename = f"dashboard_tb_{device.id}.json"
    content = json.dumps(dashboard_data, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

# --- Variables ---
@router.get("/variables", response_model=List[VariableConfig], dependencies=[Depends(require_role(ROLE_ANY))])
def list_variables(device_id: Optional[str] = None, repo: StorageRepository = Depends(get_repo)) -> List[VariableConfig]:
    """Lists variables, optionally filtered by device ID."""
    return repo.get_variables(device_id=device_id)

@router.post("/variables", response_model=VariableConfig, dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def save_variable(
    var: VariableConfig,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
) -> VariableConfig:
    """Saves a variable, resolving platform default topics and Home Assistant discovery."""
    device = repo.get_device(var.device_id)
    if device and not var.topic:
        adapter = get_adapter(device.platform)
        var.topic = adapter.get_default_topic(device, var)

    repo.save_variable(var)

    if device and device.platform.value == "homeassistant":
        adapter = get_adapter(device.platform)
        disc_msgs = adapter.get_discovery_messages(device, [var])
        client = mqtt.get_or_create_device_client(device.id, device.token)
        if client:
            for top, pay in disc_msgs:
                client.publish(top, pay, qos=1, retain=True)

    return var

@router.delete("/variables/{var_id}", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def delete_variable(var_id: str, repo: StorageRepository = Depends(get_repo)) -> dict:
    """Deletes a variable by ID."""
    repo.delete_variable(var_id)
    return {"status": "deleted", "var_id": var_id}

# --- MQTT Broker ---
@router.get("/broker", response_model=BrokerConfig, dependencies=[Depends(require_role(ROLE_ANY))])
def get_broker(repo: StorageRepository = Depends(get_repo)) -> BrokerConfig:
    """Retrieves current global MQTT broker configuration."""
    return repo.get_broker()

@router.post("/broker", response_model=BrokerConfig, dependencies=[Depends(require_role(ROLE_ADMIN_ONLY))])
def update_broker(
    broker: BrokerConfig,
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
) -> BrokerConfig:
    """Updates and hot-reloads global broker configuration."""
    repo.save_broker(broker)
    mqtt.update_global_config(broker)
    return broker

@router.post("/broker/test", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def test_broker(broker: BrokerConfig) -> Dict[str, Any]:
    """Tests network and TLS connectivity to specified broker parameters."""
    return test_broker_connectivity(broker)

# --- Logs & Error Traceability ---
@router.get("/logs", dependencies=[Depends(require_role(ROLE_ANY))])
def get_logs(level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves recent in-memory log buffer records."""
    return log_handler.get_logs(level=level, limit=limit)

@router.delete("/logs", dependencies=[Depends(require_role(ROLE_ADMIN_ONLY))])
def clear_logs() -> dict:
    """Clears in-memory log buffer."""
    log_handler.clear()
    return {"status": "cleared"}

# --- Status & Engine Control ---
@router.get("/status", dependencies=[Depends(require_role(ROLE_ANY))])
def get_status(
    repo: StorageRepository = Depends(get_repo),
    engine: SimulationEngine = Depends(get_engine),
    mqtt: MqttManager = Depends(get_mqtt),
) -> dict:
    """Retrieves system status, connection states, and variable counts."""
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
async def start_simulation(engine: SimulationEngine = Depends(get_engine)) -> dict:
    """Starts the real-time simulation engine loop."""
    engine.start()
    return {"status": "running"}

@router.post("/simulation/stop", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def stop_simulation(engine: SimulationEngine = Depends(get_engine)) -> dict:
    """Stops the real-time simulation engine loop."""
    engine.stop()
    return {"status": "stopped"}

# --- Manual Overrides & Anomalies ---
class OverrideRequest(BaseModel):
    """Payload for manual value overriding."""
    manual_override: bool
    manual_value: Optional[Any] = None

@router.post("/variables/{var_id}/override", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def override_variable(
    var_id: str,
    req: OverrideRequest,
    repo: StorageRepository = Depends(get_repo),
) -> dict:
    """Forces or releases a manual value override on a variable."""
    var = repo.get_variable(var_id)
    if not var:
        raise HTTPException(status_code=404, detail="Variable non trouvée")
    var.manual_override = req.manual_override
    var.manual_value = req.manual_value
    repo.save_variable(var)
    return {"status": "ok", "var_id": var_id, "manual_override": var.manual_override}

class AnomalyRequest(BaseModel):
    """Payload for injecting anomaly patterns."""
    anomaly: AnomalyType
    magnitude: float = 50.0

@router.post("/variables/{var_id}/anomaly", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def trigger_anomaly(
    var_id: str,
    req: AnomalyRequest,
    engine: SimulationEngine = Depends(get_engine),
) -> dict:
    """Injects an anomaly behavior (spike, drop, freeze, noise) on a variable."""
    engine.trigger_anomaly(var_id, req.anomaly, req.magnitude)
    return {"status": "ok", "var_id": var_id, "anomaly": req.anomaly.value}

# --- CSV Ingestion for Points Table ---
@router.post("/variables/{var_id}/csv", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def upload_csv_points(
    var_id: str,
    file: UploadFile = File(...),
    repo: StorageRepository = Depends(get_repo),
) -> dict:
    """Uploads and parses a CSV time-series file for table-driven simulation."""
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

# --- Full Scenario Export / Import ---
@router.get("/scenario/export", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def export_scenario(repo: StorageRepository = Depends(get_repo)) -> dict:
    """Exports full simulator scenario snapshot (broker, devices, variables)."""
    return repo.export_scenario()

@router.post("/scenario/import", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def import_scenario(
    data: Dict[str, Any],
    repo: StorageRepository = Depends(get_repo),
    mqtt: MqttManager = Depends(get_mqtt),
) -> dict:
    """Restores full simulator scenario snapshot."""
    repo.import_scenario(data)
    mqtt.update_global_config(repo.get_broker())
    return {"status": "imported", "devices": len(repo.get_devices()), "variables": len(repo.get_variables())}

# --- Equipment Presets Catalog ---
@router.get("/presets/catalog", response_model=List[EquipmentPreset], dependencies=[Depends(require_role(ROLE_ANY))])
def get_presets_catalog() -> List[EquipmentPreset]:
    """Retrieves full catalog of industrial equipment presets."""
    return get_equipment_catalog()

@router.post("/presets/instantiate", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def instantiate_equipment_preset(
    req: InstantiatePresetRequest,
    repo: StorageRepository = Depends(get_repo),
    transports = Depends(get_transports),
) -> dict:
    """Instantiates a preset into runnable DeviceConfig and child VariableConfigs."""
    try:
        device, variables = instantiate_preset(req, repo)
        validation_info = None
        if device.token:
            validation_info = await transports.test_device_communication(device)
        return {
            "status": "created",
            "device": device,
            "variables_count": len(variables),
            "variables": variables,
            "validation": validation_info,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du modèle : {e}")

@router.get("/presets/{preset_id}/thingsboard-dashboard", dependencies=[Depends(require_role(ROLE_ANY))])
def download_preset_thingsboard_dashboard(
    preset_id: str,
) -> Response:
    """Generates and downloads a ThingsBoard dashboard JSON for a catalog preset."""
    catalog = get_equipment_catalog()
    preset = next((p for p in catalog if p.id == preset_id), None)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Modèle '{preset_id}' introuvable dans le catalogue.")

    mock_device = DeviceConfig(
        id=preset.id,
        name=preset.name,
        platform=preset.default_platform,
        protocol=preset.default_protocol,
        token="A_RENSEIGNER_DANS_THINGSBOARD",
        enabled=True
    )
    mock_vars = []
    for orig in preset.variables:
        v = orig.model_copy(deep=True)
        v.device_id = mock_device.id
        mock_vars.append(v)

    dashboard_data = generate_thingsboard_dashboard(mock_device, mock_vars)
    filename = f"dashboard_tb_{preset.id}.json"
    content = json.dumps(dashboard_data, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.get("/presets/{preset_id}/export", dependencies=[Depends(require_role(ROLE_ANY))])
def export_single_preset_package(preset_id: str) -> Response:
    """Exports an exhaustive standalone package for a specific equipment preset."""
    catalog = get_equipment_catalog()
    preset = next((p for p in catalog if p.id == preset_id), None)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Modèle '{preset_id}' introuvable dans le catalogue.")

    package = build_preset_export_package(preset)
    filename = f"preset_export_{preset.id}.json"
    content = json.dumps(package, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.get("/presets/export/all", dependencies=[Depends(require_role(ROLE_ANY))])
def export_all_presets_package() -> Response:
    """Exports a multi-preset JSON bundle containing all catalog models."""
    bundle = build_all_presets_export_package()
    filename = "presets_catalog_full_bundle.json"
    content = json.dumps(bundle, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.post("/presets/import", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def import_presets_endpoint(request: Request) -> dict:
    """Imports presets from an uploaded file or direct JSON payload."""
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="Aucun fichier fourni dans le formulaire.")
        raw_bytes = await file.read()
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Fichier JSON invalide : {e}")
    else:
        try:
            payload = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Données JSON invalides : {e}")

    try:
        count, ids = import_preset_data(payload)
        return {
            "status": "imported",
            "imported_count": count,
            "imported_ids": ids,
            "message": f"{count} cas d'usage métier(s) importé(s) avec succès."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'importation : {e}")

@router.delete("/presets/{preset_id}", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def delete_preset_endpoint(preset_id: str) -> dict:
    """Deletes a custom user preset from the catalog (built-ins are protected)."""
    try:
        deleted = delete_custom_preset(preset_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Modèle '{preset_id}' introuvable ou déjà supprimé.")
        return {
            "status": "deleted",
            "preset_id": preset_id,
            "message": f"Modèle personnalisé '{preset_id}' supprimé avec succès."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {e}")

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
async def instantiate_equipment_preset(
    req: InstantiatePresetRequest,
    repo: StorageRepository = Depends(get_repo),
    transports = Depends(get_transports),
):
    """Instancie un équipement métier avec toutes ses grandeurs et formules associées."""
    try:
        device, variables = instantiate_preset(req, repo)
        validation_info = None
        if device.token:
            validation_info = await transports.test_device_communication(device)
        return {
            "status": "created",
            "device": device,
            "variables_count": len(variables),
            "variables": variables,
            "validation": validation_info,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du modèle : {e}")

@router.get("/presets/{preset_id}/thingsboard-dashboard", dependencies=[Depends(require_role(ROLE_ANY))])
def download_preset_thingsboard_dashboard(
    preset_id: str,
):
    """Génère et télécharge le tableau de bord ThingsBoard préconfiguré pour un modèle métier du catalogue."""
    catalog = get_equipment_catalog()
    preset = next((p for p in catalog if p.id == preset_id), None)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Modèle '{preset_id}' introuvable dans le catalogue.")

    mock_device = DeviceConfig(
        id=preset.id,
        name=preset.name,
        platform=preset.default_platform,
        protocol=preset.default_protocol,
        token="A_RENSEIGNER_DANS_THINGSBOARD",
        enabled=True
    )
    mock_vars = []
    for orig in preset.variables:
        v = orig.model_copy(deep=True)
        v.device_id = mock_device.id
        mock_vars.append(v)

    dashboard_data = generate_thingsboard_dashboard(mock_device, mock_vars)
    filename = f"dashboard_tb_{preset.id}.json"
    content = json.dumps(dashboard_data, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.get("/presets/{preset_id}/export", dependencies=[Depends(require_role(ROLE_ANY))])
def export_single_preset_package(preset_id: str):
    """Exporte un package complet et exhaustif pour un cas d'usage métier spécifique."""
    catalog = get_equipment_catalog()
    preset = next((p for p in catalog if p.id == preset_id), None)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Modèle '{preset_id}' introuvable dans le catalogue.")

    package = build_preset_export_package(preset)
    filename = f"preset_export_{preset.id}.json"
    content = json.dumps(package, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.get("/presets/export/all", dependencies=[Depends(require_role(ROLE_ANY))])
def export_all_presets_package():
    """Exporte un bundle JSON complet de l'ensemble des cas d'usage métiers du catalogue."""
    bundle = build_all_presets_export_package()
    filename = "presets_catalog_full_bundle.json"
    content = json.dumps(bundle, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.post("/presets/import", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
async def import_presets_endpoint(request: Request):
    """Importe un ou plusieurs cas d'usage métiers depuis un fichier JSON ou payload direct."""
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="Aucun fichier fourni dans le formulaire.")
        raw_bytes = await file.read()
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Fichier JSON invalide : {e}")
    else:
        try:
            payload = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Données JSON invalides : {e}")

    try:
        count, ids = import_preset_data(payload)
        return {
            "status": "imported",
            "imported_count": count,
            "imported_ids": ids,
            "message": f"{count} cas d'usage métier(s) importé(s) avec succès."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'importation : {e}")

@router.delete("/presets/{preset_id}", dependencies=[Depends(require_role(ROLE_OPERATOR_OR_ADMIN))])
def delete_preset_endpoint(preset_id: str):
    """Supprime un modèle personnalisé du catalogue (les modèles d'usine sont protégés)."""
    try:
        deleted = delete_custom_preset(preset_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Modèle '{preset_id}' introuvable ou déjà supprimé.")
        return {
            "status": "deleted",
            "preset_id": preset_id,
            "message": f"Modèle personnalisé '{preset_id}' supprimé avec succès."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {e}")


