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
import httpx
from pydantic import BaseModel
from app.core.dashboard_generator import generate_thingsboard_dashboard
from app.models.device import TransportProtocol
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
    insecure: bool = False


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

        # 2. Provision each Device, sync Access Token, assign to Customer, push Dashboard
        for dev in target_devices:
            tb_dev_id = None
            lookup = await client.get(
                f"{base_url}/api/tenant/devices",
                params={"deviceName": dev.name},
                headers=headers,
            )
            if lookup.status_code == 200:
                tb_dev_id = lookup.json()["id"]["id"]
            else:
                create_dev = await client.post(
                    f"{base_url}/api/device",
                    headers=headers,
                    json={"name": dev.name, "type": "default", "label": dev.id},
                )
                if create_dev.status_code not in (200, 201):
                    raise ValueError(f"Erreur création device '{dev.name}' : {create_dev.text}")
                tb_dev_id = create_dev.json()["id"]["id"]

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
        "devices_count": len(provisioned_devices),
        "dashboards_count": len(provisioned_dashboards),
        "devices": provisioned_devices,
        "dashboards": provisioned_dashboards,
    }
