"""
Site Blueprints & Multi-Equipment Hypervision Dashboard Generator.

Allows pre-sales engineers and bid managers to instantiate an entire coherent
client site (multiple interconnected devices) in 1 click, and export a consolidated
ThingsBoard Master Hypervision Dashboard aggregating all devices of the site.
"""

import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.device import TransportProtocol, PlatformType
from app.core.equipment_catalog import (
    InstantiatePresetRequest,
    instantiate_preset,
    get_equipment_catalog,
)
from app.storage.repository import StorageRepository


class SiteEquipmentSpec(BaseModel):
    """Single equipment slot inside a multi-device Site Blueprint."""
    preset_id: str
    role_suffix: str
    display_name: str


class SiteBlueprint(BaseModel):
    """Definition of a complete multi-equipment client site."""
    id: str
    name: str
    sector: str
    description: str
    equipments: List[SiteEquipmentSpec]


class InstantiateSiteRequest(BaseModel):
    """Request payload for 1-click multi-equipment site instantiation."""
    blueprint_id: str
    site_prefix: str = Field(default="site_demo", description="Prefix used for created device IDs")
    protocol: TransportProtocol = Field(default=TransportProtocol.MQTT)
    force_http_rest: bool = Field(default=False, description="Force HTTP REST v1 transport for all instantiated site devices")
    platform: PlatformType = Field(default=PlatformType.THINGSBOARD)
    clear_existing: bool = Field(default=False, description="Clear existing simulator devices before instantiating")


def get_site_blueprints() -> List[SiteBlueprint]:
    """Returns curated multi-equipment site blueprints for Eiffage Énergie Systèmes verticals."""
    return [
        SiteBlueprint(
            id="site_tertiaire_bacs",
            name="Immeuble Tertiaire Connecté (Décret BACS)",
            sector="Tertiaire & Smart Building",
            description="Site complet conforme Décret BACS / Tertiaire : GTB Classe A, Centrale de Traitement d'Air, PAC, TGBT et Bornes IRVE.",
            equipments=[
                SiteEquipmentSpec(preset_id="bldg_bacs_class_a", role_suffix="gtb", display_name="GTB Classe A Bâtiment"),
                SiteEquipmentSpec(preset_id="bldg_cta", role_suffix="cta", display_name="CTA Double Flux"),
                SiteEquipmentSpec(preset_id="bldg_heatpump", role_suffix="pac", display_name="Pompe à Chaleur"),
                SiteEquipmentSpec(preset_id="bldg_tgbt", role_suffix="tgbt", display_name="TGBT Principal"),
                SiteEquipmentSpec(preset_id="infra_irve_charger", role_suffix="irve", display_name="Parking Bornes IRVE"),
            ],
        ),
        SiteBlueprint(
            id="site_usine_decarbonee",
            name="Usine Industrielle Décarbonée (ISO 50001)",
            sector="Industrie & Utilités",
            description="Site industriel complet avec plan de comptage multi-fluides ISO 50001, air comprimé, groupe froid et autoconsommation PV.",
            equipments=[
                SiteEquipmentSpec(preset_id="ind_iso50001_multifluid", role_suffix="comptage", display_name="Comptage Multi-Fluides ISO 50001"),
                SiteEquipmentSpec(preset_id="ind_compressor", role_suffix="compresseur", display_name="Centrale Air Comprimé"),
                SiteEquipmentSpec(preset_id="ind_chiller", role_suffix="chiller", display_name="Groupe Froid Process"),
                SiteEquipmentSpec(preset_id="infra_solar_pv", role_suffix="pv", display_name="Ombrière Solaire PV"),
            ],
        ),
        SiteBlueprint(
            id="site_microgrid_energie",
            name="Microgrid Énergie & Stockage (PV + BESS + IRVE)",
            sector="Infrastructures & Énergie",
            description="Architecture complète de flexibilité énergétique : production solaire PV, stockage batterie BESS, poste HTA et recharge rapide IRVE.",
            equipments=[
                SiteEquipmentSpec(preset_id="infra_solar_pv", role_suffix="pv", display_name="Centrale Solaire PV"),
                SiteEquipmentSpec(preset_id="infra_bess_storage", role_suffix="bess", display_name="Stockage Batterie BESS"),
                SiteEquipmentSpec(preset_id="infra_transfo_hta", role_suffix="hta", display_name="Poste Source HTA/BT"),
                SiteEquipmentSpec(preset_id="infra_irve_charger", role_suffix="irve", display_name="Station Charge Rapide IRVE"),
            ],
        ),
    ]


def instantiate_site_blueprint(
    req: InstantiateSiteRequest,
    repo: Optional[StorageRepository] = None,
) -> Dict[str, Any]:
    """Instantiates all equipments of a SiteBlueprint into the simulator repository."""
    storage = repo or StorageRepository()
    blueprints = {bp.id: bp for bp in get_site_blueprints()}
    if req.blueprint_id not in blueprints:
        raise ValueError(f"Site blueprint '{req.blueprint_id}' introuvable.")

    bp = blueprints[req.blueprint_id]
    catalog = {p.id: p for p in get_equipment_catalog()}

    if req.clear_existing:
        for d in storage.get_devices():
            storage.delete_device(d.id)

    clean_prefix = "".join(c if c.isalnum() or c == "_" else "_" for c in req.site_prefix.lower()).strip("_") or "site"
    created_devices = []
    total_vars = 0

    effective_protocol = TransportProtocol.HTTP if req.force_http_rest else req.protocol

    for idx, eq in enumerate(bp.equipments):
        if eq.preset_id not in catalog:
            continue
        device_id = f"{clean_prefix}_{eq.role_suffix}"
        inst_req = InstantiatePresetRequest(
            preset_id=eq.preset_id,
            device_id=device_id,
            device_name=eq.display_name,
            protocol=effective_protocol,
            platform=req.platform,
            token=f"{clean_prefix}_{eq.role_suffix}_tok",
        )
        dev, created_vars = instantiate_preset(inst_req, repo=storage)
        created_devices.append({
            "device_id": dev.id,
            "name": dev.name,
            "preset_id": eq.preset_id,
            "variables_count": len(created_vars),
        })
        total_vars += len(created_vars)

    return {
        "status": "instantiated",
        "blueprint_id": bp.id,
        "blueprint_name": bp.name,
        "devices_created": len(created_devices),
        "total_variables": total_vars,
        "devices": created_devices,
    }


def generate_site_hypervision_dashboard(blueprint_id: str, site_prefix: str = "site_demo") -> Dict[str, Any]:
    """Generates a consolidated ThingsBoard 4.3 Master Hypervision Dashboard for a SiteBlueprint."""
    blueprints = {bp.id: bp for bp in get_site_blueprints()}
    if blueprint_id not in blueprints:
        raise ValueError(f"Site blueprint '{blueprint_id}' introuvable.")

    bp = blueprints[blueprint_id]
    catalog = {p.id: p for p in get_equipment_catalog()}

    entity_aliases: Dict[str, Any] = {}
    widgets: Dict[str, Any] = {}
    layout_widgets: Dict[str, Any] = {}

    # 1. Header Banner
    header_id = str(uuid.uuid4())
    widgets[header_id] = {
        "typeFullFqn": "system.cards.html_card",
        "isSystemType": True,
        "bundleAlias": "cards",
        "typeAlias": "html_card",
        "type": "static",
        "title": f"Hypervision Site — {bp.name}",
        "sizeX": 24,
        "sizeY": 2,
        "config": {
            "datasources": [],
            "settings": {
                "cardHtml": (
                    f"<div style='padding:14px 20px; background:#E5E7EB; color:#0F172A; border-radius:8px; border:1px solid #CBD5E1; display:flex; justify-content:space-between; align-items:center;'>"
                    f"<div><strong style='font-size:15px; color:#0F172A;'>HYPERVISION SITE • {bp.name}</strong>"
                    f"<div style='font-size:11px; color:#475569; margin-top:2px;'>{bp.description}</div></div>"
                    f"<div style='font-size:12px; background:#CBD5E1; padding:6px 12px; border-radius:6px; color:#1E293B; font-weight:700;'>{len(bp.equipments)} Équipements Connectés</div>"
                    f"</div>"
                )
            },
        },
    }
    layout_widgets[header_id] = {"sizeX": 24, "sizeY": 2, "row": 0, "col": 0}
    current_row = 2

    # 2. One Timeseries Card + Key Metrics per Equipment in the Site (ISA-101 palette)
    colors = ["#334155", "#0369A1", "#475569", "#0F766E", "#1E40AF", "#64748B"]
    for idx, eq in enumerate(bp.equipments):
        alias_id = str(uuid.uuid4())
        entity_aliases[alias_id] = {
            "id": alias_id,
            "alias": eq.display_name,
            "filter": {
                "type": "singleEntity",
                "resolveMultiple": False,
                "singleEntity": {"entityType": "DEVICE", "id": "00000000-0000-0000-0000-000000000000"},
            },
        }

        preset = catalog.get(eq.preset_id)
        telems = [v for v in (preset.variables if preset else []) if v.var_type.value == "telemetry"][:4]
        data_keys = [
            {
                "name": v.id,
                "label": f"{v.name} ({v.unit})" if v.unit else v.name,
                "type": "timeseries",
                "color": colors[(idx + j) % len(colors)],
                "units": v.unit or "",
                "decimals": 2,
            }
            for j, v in enumerate(telems)
        ]

        col = 0 if idx % 2 == 0 else 12
        w_id = str(uuid.uuid4())
        widgets[w_id] = {
            "typeFullFqn": "system.charts.basic_timeseries",
            "isSystemType": True,
            "bundleAlias": "charts",
            "typeAlias": "basic_timeseries",
            "type": "timeseries",
            "title": eq.display_name,
            "sizeX": 12,
            "sizeY": 6,
            "config": {
                "showTitle": True,
                "datasources": [{"type": "entity", "entityAliasId": alias_id, "dataKeys": data_keys}],
                "settings": {"showLegend": True},
            },
        }
        layout_widgets[w_id] = {"sizeX": 12, "sizeY": 6, "row": current_row, "col": col}
        if idx % 2 == 1:
            current_row += 6

    return {
        "title": f"Hypervision Site — {bp.name}",
        "configuration": {
            "description": f"Dashboard Master Multi-Équipements pour {bp.name} (préfixe: {site_prefix})",
            "entityAliases": entity_aliases,
            "widgets": widgets,
            "states": {
                "default": {
                    "name": f"Hypervision Site — {bp.name}",
                    "root": True,
                    "layouts": {
                        "main": {
                            "gridAppearance": {"layoutDimension": {"type": "percentage", "percentage": 100}},
                            "widgets": layout_widgets,
                        }
                    },
                }
            },
        },
    }
