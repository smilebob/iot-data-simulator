"""
Ephemeral Multi-Tenant & Multi-Customer ThingsBoard 4.3 Provisioner.

Connects to a target ThingsBoard instance using ephemeral credentials (never stored
on disk), auto-detects SYS_ADMIN vs TENANT_ADMIN authority, allows selecting or
creating Tenants and Customers, creates Devices, retrieves real Access Tokens back
into the simulator repository, and pushes live-bound Dashboards assigned to the Customer.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import json
import uuid
import httpx
from pydantic import BaseModel
from app.core.dashboard_generator import generate_thingsboard_dashboard
from app.core.scada_synoptics import get_clean_var_key
from app.core.svg_components import generate_thingsboard_widget_bundle
from app.models.device import DeviceConfig, TransportProtocol
from app.models.variable import DataType, SimMode, VariableConfig, VariableType
from app.storage.repository import StorageRepository


class TbCredentialsRequest(BaseModel):
    """Ephemeral connection request (never persisted)."""
    tb_url: str
    username: str
    password: str
    insecure: bool = False


class TbTenantContextRequest(BaseModel):
    """Request to inspect customers inside a specific Tenant (for SYS_ADMIN) or create one."""
    tb_url: str
    sysadmin_token: str
    tenant_id: Optional[str] = None
    new_tenant_title: Optional[str] = None
    insecure: bool = False


class TbProvisionRequest(BaseModel):
    """Full 1-click provisioning request."""
    tb_url: str
    access_token: str
    customer_id: Optional[str] = None
    new_customer_title: Optional[str] = None
    device_ids: Optional[List[str]] = None
    push_dashboards: bool = True
    force_http_rest: bool = True
    create_site_asset: bool = True
    site_asset_name: Optional[str] = None
    create_alarm_profiles: bool = True
    push_isa101_widgets: bool = False
    insecure: bool = False


def build_isa101_device_profile(device: DeviceConfig, dev_vars: List[VariableConfig]) -> Optional[Dict[str, Any]]:
    """Builds a ThingsBoard 4.3 DeviceProfile payload with ISA-101 WARNING & CRITICAL alarm rules."""
    alarms = []
    for v in dev_vars:
        if v.var_type != VariableType.TELEMETRY or v.data_type not in (DataType.FLOAT, DataType.INTEGER):
            continue
        if v.sim_mode in (SimMode.INTEGRATOR, SimMode.CONSTANT, SimMode.DERIVED):
            continue
        if not v.math_config or v.math_config.max_val <= v.math_config.min_val:
            continue

        clean_key = get_clean_var_key(v)
        min_v = float(v.math_config.min_val)
        max_v = float(v.math_config.max_val)
        span = max_v - min_v
        warn_high = round(min_v + 0.90 * span, 2)
        crit_high = round(max_v + 0.05 * span, 2)

        def _pred(op: str, val: float) -> Dict[str, Any]:
            return {
                "key": {"type": "TIME_SERIES", "key": clean_key},
                "valueType": "NUMERIC",
                "predicate": {
                    "type": "NUMERIC",
                    "operation": op,
                    "value": {"defaultValue": val, "dynamicValue": None},
                },
            }

        alarms.append({
            "id": str(uuid.uuid4()),
            "alarmType": f"ISA101_{clean_key.upper()}_HORS_PLAGE",
            "createRules": {
                "WARNING": {
                    "condition": {"condition": [_pred("GREATER", warn_high)], "spec": {"type": "SIMPLE"}},
                    "alarmDetails": f"▲ Avertissement ISA-101 : {v.name} > {warn_high} {v.unit or ''}".strip(),
                },
                "CRITICAL": {
                    "condition": {"condition": [_pred("GREATER", crit_high)], "spec": {"type": "SIMPLE"}},
                    "alarmDetails": f"■ ! Critique ISA-101 : {v.name} > {crit_high} {v.unit or ''}".strip(),
                },
            },
            "clearRule": {
                "condition": {"condition": [_pred("LESS_OR_EQUAL", warn_high)], "spec": {"type": "SIMPLE"}},
                "alarmDetails": f"Retour nominal ISA-101 : {v.name}",
            },
            "propagate": True,
            "propagateToOwner": True,
        })

    if not alarms:
        return None

    return {
        "name": f"ISA101_Profile_{device.id}",
        "type": "DEFAULT",
        "transportType": "DEFAULT",
        "provisionType": "DISABLED",
        "description": f"Profil d'alarmes ANSI/ISA-101 généré automatiquement pour {device.name}",
        "profileData": {
            "configuration": {"type": "DEFAULT"},
            "transportConfiguration": {"type": "DEFAULT"},
            "provisionConfiguration": {"type": "DISABLED"},
            "alarms": alarms[:10],
        },
    }


def _clean_url(url: str) -> str:
    return url.strip().rstrip("/")


def _parse_tb_url_target(tb_url: str) -> Tuple[str, int, bool]:
    """Extracts (host, port, use_tls) from a ThingsBoard base URL for HTTP REST auto-configuration."""
    raw = tb_url.strip()
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    use_tls = parsed.scheme.lower() == "https"
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if use_tls else 80)
    return host, port, use_tls


async def _tb_login(client: httpx.AsyncClient, base_url: str, username: str, password: str) -> str:
    resp = await client.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
    )
    if resp.status_code != 200:
        raise ValueError(f"Échec authentification ThingsBoard ({resp.status_code}) : {resp.text}")
    data = resp.json()
    return data["token"]


async def _tb_get_user(client: httpx.AsyncClient, base_url: str, token: str) -> Dict[str, Any]:
    resp = await client.get(
        f"{base_url}/api/auth/user",
        headers={"X-Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        raise ValueError(f"Impossible de lire le profil utilisateur ThingsBoard ({resp.status_code})")
    return resp.json()


async def tb_inspect_context(req: TbCredentialsRequest) -> Dict[str, Any]:
    """Authenticates ephemerally and returns authority, Tenants (if SYS_ADMIN) or Customers (if TENANT_ADMIN)."""
    base_url = _clean_url(req.tb_url)
    async with httpx.AsyncClient(timeout=20.0, verify=not req.insecure) as client:
        token = await _tb_login(client, base_url, req.username, req.password)
        user = await _tb_get_user(client, base_url, token)
        authority = user.get("authority", "TENANT_ADMIN")
        headers = {"X-Authorization": f"Bearer {token}"}

        tenants = []
        customers = []

        if authority == "SYS_ADMIN":
            t_resp = await client.get(f"{base_url}/api/tenants?pageSize=50&page=0", headers=headers)
            if t_resp.status_code == 200:
                for t in t_resp.json().get("data", []):
                    tenants.append({"id": t["id"]["id"], "title": t.get("title", "Tenant")})
        else:
            c_resp = await client.get(f"{base_url}/api/customers?pageSize=100&page=0", headers=headers)
            if c_resp.status_code == 200:
                for c in c_resp.json().get("data", []):
                    customers.append({"id": c["id"]["id"], "title": c.get("title", "Client")})

        return {
            "authority": authority,
            "access_token": token,
            "tenants": tenants,
            "customers": customers,
        }


async def tb_switch_tenant_context(req: TbTenantContextRequest) -> Dict[str, Any]:
    """Switches SYS_ADMIN into a Tenant context (impersonating a Tenant Admin) and lists its Customers."""
    base_url = _clean_url(req.tb_url)
    sys_headers = {"X-Authorization": f"Bearer {req.sysadmin_token}"}

    async with httpx.AsyncClient(timeout=20.0, verify=not req.insecure) as client:
        tenant_id = req.tenant_id
        if req.new_tenant_title:
            t_resp = await client.post(
                f"{base_url}/api/tenant",
                headers=sys_headers,
                json={"title": req.new_tenant_title.strip()},
            )
            if t_resp.status_code not in (200, 201):
                raise ValueError(f"Erreur création Tenant ({t_resp.status_code}) : {t_resp.text}")
            tenant_id = t_resp.json()["id"]["id"]

        if not tenant_id:
            raise ValueError("tenant_id ou new_tenant_title requis.")

        # Find a TENANT_ADMIN user in that tenant to obtain a tenant-scoped JWT
        u_resp = await client.get(f"{base_url}/api/tenant/{tenant_id}/users?pageSize=20&page=0", headers=sys_headers)
        if u_resp.status_code != 200:
            raise ValueError(f"Impossible de lister les utilisateurs du Tenant ({u_resp.status_code})")

        users = u_resp.json().get("data", [])
        if not users:
            raise ValueError(
                "Ce Tenant ne possède aucun administrateur (TENANT_ADMIN). "
                "Créez un utilisateur Tenant Admin dans ThingsBoard ou connectez-vous directement avec celui-ci."
            )

        admin_user_id = users[0]["id"]["id"]
        tok_resp = await client.get(f"{base_url}/api/user/{admin_user_id}/token", headers=sys_headers)
        if tok_resp.status_code != 200:
            raise ValueError(f"Impossible d'obtenir le jeton Tenant Admin ({tok_resp.status_code})")

        tenant_token = tok_resp.json()["token"]
        t_headers = {"X-Authorization": f"Bearer {tenant_token}"}

        customers = []
        c_resp = await client.get(f"{base_url}/api/customers?pageSize=100&page=0", headers=t_headers)
        if c_resp.status_code == 200:
            for c in c_resp.json().get("data", []):
                customers.append({"id": c["id"]["id"], "title": c.get("title", "Client")})

        return {
            "tenant_id": tenant_id,
            "tenant_token": tenant_token,
            "customers": customers,
        }


async def tb_provision_stack(
    req: TbProvisionRequest,
    repo: Optional[StorageRepository] = None,
) -> Dict[str, Any]:
    """Provisions devices & dashboards into ThingsBoard, assigns to Customer, and syncs real tokens."""
    storage = repo or StorageRepository()
    base_url = _clean_url(req.tb_url)
    headers = {"X-Authorization": f"Bearer {req.access_token}"}

    all_devices = storage.get_devices()
    target_devices = (
        [d for d in all_devices if d.id in req.device_ids]
        if req.device_ids
        else [d for d in all_devices if d.enabled] or all_devices
    )
    if not target_devices:
        raise ValueError("Aucun équipement à provisionner dans le simulateur.")

    all_vars = storage.get_variables()
    provisioned_devices = []
    provisioned_dashboards = []
    provisioned_profiles = []
    site_asset_id = None
    widgets_pushed = 0

    async with httpx.AsyncClient(timeout=25.0, verify=not req.insecure) as client:
        # 1. Resolve or create Customer if requested
        customer_id = req.customer_id
        if req.new_customer_title and req.new_customer_title.strip():
            c_resp = await client.post(
                f"{base_url}/api/customer",
                headers=headers,
                json={"title": req.new_customer_title.strip()},
            )
            if c_resp.status_code not in (200, 201):
                raise ValueError(f"Erreur création Client ({c_resp.status_code}) : {c_resp.text}")
            customer_id = c_resp.json()["id"]["id"]

        # 1b. Optionally create Site Asset hierarchy root
        if req.create_site_asset:
            asset_name = (req.site_asset_name or req.new_customer_title or "Site_IoT_Demo").strip()
            a_resp = await client.post(
                f"{base_url}/api/asset",
                headers=headers,
                json={"name": asset_name, "type": "Site", "label": asset_name},
            )
            if a_resp.status_code in (200, 201):
                site_asset_id = a_resp.json().get("id", {}).get("id")
                if site_asset_id and customer_id:
                    await client.post(
                        f"{base_url}/api/customer/{customer_id}/asset/{site_asset_id}",
                        headers=headers,
                    )

        # 1c. Optionally push 70 ISA-101 SVG Widgets Bundle into the Tenant
        if req.push_isa101_widgets:
            bundle_json = generate_thingsboard_widget_bundle()
            b_meta = bundle_json.get("widgetsBundle", {})
            wb_resp = await client.post(
                f"{base_url}/api/widgetsBundle",
                headers=headers,
                json={
                    "title": b_meta.get("title", "SCADA ISA-101 — Composants Modulaires (70)"),
                    "description": b_meta.get("description", ""),
                },
            )
            if wb_resp.status_code in (200, 201):
                bundle_alias = wb_resp.json().get("alias") or b_meta.get("alias", "scada_isa101_modular")
                for wt in bundle_json.get("widgetTypes", []):
                    wt_payload = dict(wt)
                    wt_payload["bundleAlias"] = bundle_alias
                    wt_resp = await client.post(f"{base_url}/api/widgetType", headers=headers, json=wt_payload)
                    if wt_resp.status_code in (200, 201):
                        widgets_pushed += 1

        # 2. Provision each Device, Alarm Profile, Asset Relation, Access Token, Customer & Dashboard
        for dev in target_devices:
            dev_vars = [v for v in all_vars if v.device_id == dev.id]

            # 2a. Optional ISA-101 Device Profile with native ThingsBoard alarm rules
            tb_profile_id = None
            if req.create_alarm_profiles:
                profile_payload = build_isa101_device_profile(dev, dev_vars)
                if profile_payload:
                    p_resp = await client.post(
                        f"{base_url}/api/deviceProfile",
                        headers=headers,
                        json=profile_payload,
                    )
                    if p_resp.status_code in (200, 201):
                        tb_profile_id = p_resp.json().get("id", {}).get("id")
                        if tb_profile_id:
                            provisioned_profiles.append({
                                "name": profile_payload["name"],
                                "tb_profile_id": tb_profile_id,
                                "alarm_rules_count": len(profile_payload["profileData"]["alarms"]),
                            })

            tb_dev_id = None
            lookup = await client.get(
                f"{base_url}/api/tenant/devices",
                params={"deviceName": dev.name},
                headers=headers,
            )
            if lookup.status_code == 200:
                tb_dev_id = lookup.json()["id"]["id"]
            else:
                dev_body: Dict[str, Any] = {"name": dev.name, "type": "default", "label": dev.id}
                if tb_profile_id:
                    dev_body["deviceProfileId"] = {"entityType": "DEVICE_PROFILE", "id": tb_profile_id}
                create_dev = await client.post(
                    f"{base_url}/api/device",
                    headers=headers,
                    json=dev_body,
                )
                if create_dev.status_code not in (200, 201):
                    raise ValueError(f"Erreur création device '{dev.name}' : {create_dev.text}")
                tb_dev_id = create_dev.json()["id"]["id"]

            # 2b. Create Asset -> Device 'Contains' relation if Site Asset exists
            if site_asset_id and tb_dev_id:
                await client.post(
                    f"{base_url}/api/relation",
                    headers=headers,
                    json={
                        "from": {"entityType": "ASSET", "id": site_asset_id},
                        "to": {"entityType": "DEVICE", "id": tb_dev_id},
                        "type": "Contains",
                        "typeGroup": "COMMON",
                    },
                )

            # Retrieve real Access Token from ThingsBoard
            cred_resp = await client.get(f"{base_url}/api/device/{tb_dev_id}/credentials", headers=headers)
            real_token = None
            dev_modified = False
            if cred_resp.status_code == 200:
                real_token = cred_resp.json().get("credentialsId")
                if real_token:
                    dev.token = real_token
                    dev_modified = True

            if req.force_http_rest:
                target_host, target_port, target_tls = _parse_tb_url_target(base_url)
                dev.protocol = TransportProtocol.HTTP
                dev.custom_host = target_host
                dev.custom_port = target_port
                dev.use_tls = target_tls
                dev_modified = True

            if dev_modified:
                storage.save_device(dev)

            # Assign Device to Customer
            if customer_id:
                await client.post(f"{base_url}/api/customer/{customer_id}/device/{tb_dev_id}", headers=headers)

            provisioned_devices.append({
                "simulator_id": dev.id,
                "name": dev.name,
                "tb_device_id": tb_dev_id,
                "token_synced": bool(real_token),
                "protocol": dev.protocol.value,
                "http_rest_forced": bool(req.force_http_rest),
            })

            # 3. Push Dashboard bound to real ThingsBoard Device UUID
            if req.push_dashboards:
                dev_vars = [v for v in all_vars if v.device_id == dev.id]
                dash_json = generate_thingsboard_dashboard(dev, dev_vars)
                dash_str = json.dumps(dash_json).replace("00000000-0000-0000-0000-000000000000", tb_dev_id)
                dash_payload = json.loads(dash_str)

                d_resp = await client.post(f"{base_url}/api/dashboard", headers=headers, json=dash_payload)
                if d_resp.status_code in (200, 201):
                    tb_dash_id = d_resp.json()["id"]["id"]
                    if customer_id:
                        await client.post(
                            f"{base_url}/api/customer/{customer_id}/dashboard/{tb_dash_id}",
                            headers=headers,
                        )
                    provisioned_dashboards.append({
                        "title": dash_payload.get("title"),
                        "tb_dashboard_id": tb_dash_id,
                        "url": f"{base_url}/dashboards/{tb_dash_id}",
                    })

    return {
        "status": "provisioned",
        "customer_id": customer_id,
        "site_asset_id": site_asset_id,
        "devices_count": len(provisioned_devices),
        "dashboards_count": len(provisioned_dashboards),
        "alarm_profiles_count": len(provisioned_profiles),
        "widgets_pushed_count": widgets_pushed,
        "devices": provisioned_devices,
        "dashboards": provisioned_dashboards,
        "alarm_profiles": provisioned_profiles,
    }
