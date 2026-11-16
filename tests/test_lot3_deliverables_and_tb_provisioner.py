"""
Unit Tests for Lot 3: Bid Deliverables (IO List CSV + Markdown Dossier)
and Ephemeral Multi-Tenant/Customer ThingsBoard 4.3 Provisioner.
"""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.bid_deliverables import (
    generate_io_list_csv,
    generate_architecture_dossier_md,
)
from app.core.sizing_calculator import SizingRequest, calculate_sizing
from app.core.tb_provisioner import (
    TbCredentialsRequest,
    TbTenantContextRequest,
    TbProvisionRequest,
    tb_inspect_context,
    tb_switch_tenant_context,
    tb_provision_stack,
)
from app.models.device import DeviceConfig, TransportProtocol, PlatformType
from app.models.variable import VariableConfig, VariableType, DataType, SimMode, MathConfig
from app.storage.repository import StorageRepository


def test_bid_deliverables_csv_and_markdown():
    """Validates UTF-8 BOM semicolon IO List CSV and Markdown Technical Dossier."""
    devices = [
        DeviceConfig(
            id="gtb_01",
            name="GTB Classe A",
            protocol=TransportProtocol.MQTT,
            platform=PlatformType.THINGSBOARD,
            publish_interval=5.0,
        )
    ]
    variables = [
        VariableConfig(
            id="temp_ambiante",
            name="Température Ambiante",
            device_id="gtb_01",
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="°C",
            sim_mode=SimMode.RANDOM_WALK,
            math_config=MathConfig(min_val=19.0, max_val=22.0),
        ),
        VariableConfig(
            id="ipe_surfacique",
            name="IPE Surfacique",
            device_id="gtb_01",
            var_type=VariableType.TELEMETRY,
            data_type=DataType.FLOAT,
            unit="kWh/m².an",
            sim_mode=SimMode.CONSTANT,
        ),
    ]

    csv_out = generate_io_list_csv(devices, variables)
    assert csv_out.startswith("\ufeff")
    assert "Équipement;ID Équipement;Protocole;" in csv_out
    assert "GTB Classe A;gtb_01;MQTT;temp_ambiante;Température Ambiante;Télémétrie;" in csv_out
    assert "Hors plage [19.0; 22.0] °C" in csv_out

    sizing = calculate_sizing(SizingRequest(device_count=1, variables_per_device=2))
    md_out = generate_architecture_dossier_md(devices, variables, sizing)
    assert "```mermaid" in md_out
    assert "| **GTB Classe A** | `gtb_01` |" in md_out
    assert "Indicateurs de Performance Énergétique" in md_out
    assert "Dimensionnement Architecture IoT" in md_out


def _mock_response(status_code: int, payload: dict):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.text = json.dumps(payload)
    return resp


def test_tb_provisioner_sysadmin_to_customer_flow():
    """Validates ephemeral SYS_ADMIN login, tenant switch, customer assignment, and token sync."""
    tmp_dir = tempfile.mkdtemp()
    db_file = os.path.join(tmp_dir, "tb_prov_test.json")
    repo = StorageRepository(file_path=db_file)
    repo.save_device(DeviceConfig(id="dev_pac", name="PAC Site Alpha", token="OLD_DUMMY_TOK"))
    repo.save_variable(VariableConfig(id="temp_eau", name="Temp Eau", device_id="dev_pac", var_type=VariableType.TELEMETRY))

    async def _run():
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        async def _post(url, **kwargs):
            if url.endswith("/api/auth/login"):
                return _mock_response(200, {"token": "sys_jwt_123"})
            if url.endswith("/api/customer"):
                return _mock_response(200, {"id": {"id": "cust_uuid_99"}, "title": "Client Demo Alpha"})
            if url.endswith("/api/device"):
                return _mock_response(200, {"id": {"id": "tb_dev_uuid_42"}, "name": "PAC Site Alpha"})
            if "/api/customer/cust_uuid_99/device/tb_dev_uuid_42" in url:
                return _mock_response(200, {})
            if url.endswith("/api/dashboard"):
                # Verify real device UUID replaced the placeholder UUID!
                dash_json_str = json.dumps(kwargs.get("json", {}))
                assert "tb_dev_uuid_42" in dash_json_str
                assert "00000000-0000-0000-0000-000000000000" not in dash_json_str
                return _mock_response(200, {"id": {"id": "tb_dash_uuid_77"}})
            if "/api/customer/cust_uuid_99/dashboard/tb_dash_uuid_77" in url:
                return _mock_response(200, {})
            return _mock_response(404, {})

        async def _get(url, **kwargs):
            if url.endswith("/api/auth/user"):
                return _mock_response(200, {"authority": "SYS_ADMIN"})
            if "/api/tenants" in url:
                return _mock_response(200, {"data": [{"id": {"id": "ten_1"}, "title": "Tenant Principal"}]})
            if "/api/tenant/ten_1/users" in url:
                return _mock_response(200, {"data": [{"id": {"id": "u_admin_1"}}]})
            if "/api/user/u_admin_1/token" in url:
                return _mock_response(200, {"token": "tenant_jwt_456"})
            if "/api/customers" in url:
                return _mock_response(200, {"data": []})
            if "/api/tenant/devices" in url:
                return _mock_response(404, {})
            if "/api/device/tb_dev_uuid_42/credentials" in url:
                return _mock_response(200, {"credentialsId": "REAL_TB_ACCESS_TOKEN_XYZ"})
            return _mock_response(404, {})

        mock_client.post.side_effect = _post
        mock_client.get.side_effect = _get

        with patch("app.core.tb_provisioner.httpx.AsyncClient", return_value=mock_client, create=True):
            ctx = await tb_inspect_context(
                TbCredentialsRequest(tb_url="https://tb.example.com", username="sys@tb.local", password="secret")
            )
            assert ctx["authority"] == "SYS_ADMIN"
            assert ctx["tenants"][0]["id"] == "ten_1"

            t_ctx = await tb_switch_tenant_context(
                TbTenantContextRequest(
                    tb_url="https://tb.example.com",
                    sysadmin_token=ctx["access_token"],
                    tenant_id="ten_1",
                )
            )
            assert t_ctx["tenant_token"] == "tenant_jwt_456"

            prov = await tb_provision_stack(
                TbProvisionRequest(
                    tb_url="https://tb.example.com",
                    access_token=t_ctx["tenant_token"],
                    new_customer_title="Client Demo Alpha",
                    device_ids=["dev_pac"],
                    push_dashboards=True,
                ),
                repo=repo,
            )
            assert prov["status"] == "provisioned"
            assert prov["customer_id"] == "cust_uuid_99"
            assert prov["devices_count"] == 1
            assert prov["dashboards_count"] == 1

            updated_dev = repo.get_device("dev_pac")
            assert updated_dev.token == "REAL_TB_ACCESS_TOKEN_XYZ"

    asyncio.run(_run())
