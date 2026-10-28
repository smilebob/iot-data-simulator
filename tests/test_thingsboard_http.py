"""
Unit Tests for ThingsBoard HTTP Client and REST Diagnostics
===========================================================
Validates browser-compliant User-Agent header generation, URL prefix sanitization,
RPC response endpoints, and connectivity diagnostics.
"""

import sys
import os
import types
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Standalone mocks for test execution outside container
if 'pydantic' not in sys.modules:
    pyd = types.ModuleType('pydantic')
    class BaseModel:
        """Mock BaseModel."""
        def __init__(self, **kwargs):
            for k, v in kwargs.items(): setattr(self, k, v)
    pyd.BaseModel = BaseModel
    pyd.Field = lambda default=None, **kwargs: default
    pyd.field_validator = lambda *a, **k: (lambda f: f)
    sys.modules['pydantic'] = pyd

for mod in ['paho', 'paho.mqtt', 'paho.mqtt.client', 'fastapi', 'fastapi.responses', 'aiocoap', 'httpx']:
    if mod not in sys.modules:
        m = types.ModuleType(mod)
        m.Client = lambda *a, **k: None
        m.Response = lambda *a, **k: None
        sys.modules[mod] = m

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.transports.http_client import ThingsBoardHttpClient, DEFAULT_HEADERS


def test_headers_and_rpc():
    """Validates HTTP headers and RPC response formatting."""
    print("Testing DEFAULT_HEADERS and RPC headers...")
    assert "User-Agent" in DEFAULT_HEADERS
    assert "Mozilla" in DEFAULT_HEADERS["User-Agent"]
    assert DEFAULT_HEADERS.get("Accept") == "application/json"

    client = ThingsBoardHttpClient()

    async def _test():
        # Test respond_rpc calls post_payload with correct endpoint and format
        with patch.object(client, 'post_payload', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (True, "HTTP 200")
            success = await client.respond_rpc(
                host="thingsboard.example.com",
                port=443,
                token="pac_tok_123",
                req_id=7,
                resp_payload='{"status": "SUCCESS", "value": false}',
                use_tls=True
            )
            assert success is True
            mock_post.assert_called_once_with(
                host="thingsboard.example.com",
                port=443,
                endpoint="/api/v1/pac_tok_123/rpc/7",
                payload='{"status": "SUCCESS", "value": false}',
                use_tls=True
            )

    asyncio.run(_test())
    print("✓ Headers & RPC response formatting validated successfully!")


def test_build_url_sanitization():
    """Validates host URI sanitization across protocols and port overrides."""
    print("Testing ThingsBoardHttpClient.build_url sanitization...")
    # 1. Host with https://
    url, tls = ThingsBoardHttpClient.build_url("https://thingsboard.example.com", 443, "/api/v1/tok123/telemetry", use_tls=False)
    assert url == "https://thingsboard.example.com/api/v1/tok123/telemetry"
    assert tls is True

    # 2. Host with http:// and custom port
    url, tls = ThingsBoardHttpClient.build_url("http://thingsboard.example.com:8080", 8080, "api/v1/tok123/telemetry", use_tls=True)
    assert url == "http://thingsboard.example.com:8080/api/v1/tok123/telemetry"
    assert tls is False

    # 3. Standard Cloud host on port 443
    url, tls = ThingsBoardHttpClient.build_url("thingsboard.cloud", 443, "/api/v1/tok123/attributes", use_tls=True)
    assert url == "https://thingsboard.cloud/api/v1/tok123/attributes"
    assert tls is True

    # 4. Standard local host on port 80
    url, tls = ThingsBoardHttpClient.build_url("localhost", 80, "/api/v1/tok123/telemetry", use_tls=False)
    assert url == "http://localhost/api/v1/tok123/telemetry"
    assert tls is False
    print("✓ URL sanitization validated successfully!")


def test_connectivity_diagnostic():
    """Validates HTTP diagnostic responses (200 OK vs 401 Unauthorized vs network error)."""
    print("Testing test_connectivity responses (200 OK vs 401 Unauthorized)...")
    client = ThingsBoardHttpClient()

    async def _test():
        # Simulation 200 OK
        with patch.object(client, 'post_payload', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (True, "HTTP 200")
            diag = await client.test_connectivity("thingsboard.example.com", 443, "valid_token", use_tls=True)
            assert diag["success"] is True
            assert diag["token_valid"] is True
            assert "validé avec succès" in diag["recommendations"][0]

        # Simulation 401 Unauthorized
        with patch.object(client, 'post_payload', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (False, "HTTP 401 Non Autorisé")
            diag = await client.test_connectivity("thingsboard.example.com", 443, "bad_token", use_tls=True)
            assert diag["success"] is True       # Host is reachable
            assert diag["token_valid"] is False  # Token rejected
            assert "rejeté" in diag["recommendations"][0]

        # Simulation Network Outage
        with patch.object(client, 'post_payload', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (False, "Connection refused")
            diag = await client.test_connectivity("offline.host", 443, "token", use_tls=True)
            assert diag["success"] is False
            assert diag["token_valid"] is False

    asyncio.run(_test())
    print("✓ test_connectivity diagnostic logic validated successfully!")


if __name__ == "__main__":
    test_headers_and_rpc()
    test_build_url_sanitization()
    test_connectivity_diagnostic()
    print("\n🎉 ALL THINGSBOARD HTTP TESTS PASSED!")
