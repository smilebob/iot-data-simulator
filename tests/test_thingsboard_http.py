import sys
import os
import types
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Standalone mocks for test execution outside container
if 'pydantic' not in sys.modules:
    pyd = types.ModuleType('pydantic')
    class BaseModel:
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

from app.transports.http_client import ThingsBoardHttpClient


def test_build_url_sanitization():
    print("Testing ThingsBoardHttpClient.build_url sanitization...")
    # 1. Hôte avec https://
    url, tls = ThingsBoardHttpClient.build_url("https://easythings.app.eiffageenergiesystemes.com", 443, "/api/v1/tok123/telemetry", use_tls=False)
    assert url == "https://easythings.app.eiffageenergiesystemes.com/api/v1/tok123/telemetry"
    assert tls is True

    # 2. Hôte avec http:// et port personnalisé
    url, tls = ThingsBoardHttpClient.build_url("http://192.168.1.50:8080", 8080, "api/v1/tok123/telemetry", use_tls=True)
    assert url == "http://192.168.1.50:8080/api/v1/tok123/telemetry"
    assert tls is False

    # 3. Hôte standard cloud avec port 443
    url, tls = ThingsBoardHttpClient.build_url("thingsboard.cloud", 443, "/api/v1/tok123/attributes", use_tls=True)
    assert url == "https://thingsboard.cloud/api/v1/tok123/attributes"
    assert tls is True

    # 4. Hôte local standard port 80
    url, tls = ThingsBoardHttpClient.build_url("localhost", 80, "/api/v1/tok123/telemetry", use_tls=False)
    assert url == "http://localhost/api/v1/tok123/telemetry"
    assert tls is False
    print("✓ URL sanitization validated successfully!")


def test_connectivity_diagnostic():
    print("Testing test_connectivity responses (200 OK vs 401 Unauthorized)...")
    client = ThingsBoardHttpClient()

    async def _test():
        # Simulation 200 OK
        with patch.object(client, 'post_payload', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (True, "HTTP 200")
            diag = await client.test_connectivity("easythings.app.eiffageenergiesystemes.com", 443, "valid_token", use_tls=True)
            assert diag["success"] is True
            assert diag["token_valid"] is True
            assert "validé avec succès" in diag["recommendations"][0]

        # Simulation 401 Unauthorized
        with patch.object(client, 'post_payload', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (False, "HTTP 401 Non Autorisé")
            diag = await client.test_connectivity("easythings.app.eiffageenergiesystemes.com", 443, "bad_token", use_tls=True)
            assert diag["success"] is True       # Le serveur est bien joignable
            assert diag["token_valid"] is False  # Mais le token est invalide
            assert "rejeté" in diag["recommendations"][0]

        # Simulation Panne Réseau
        with patch.object(client, 'post_payload', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (False, "Connection refused")
            diag = await client.test_connectivity("offline.host", 443, "token", use_tls=True)
            assert diag["success"] is False
            assert diag["token_valid"] is False

    asyncio.run(_test())
    print("✓ test_connectivity diagnostic logic validated successfully!")


if __name__ == "__main__":
    test_build_url_sanitization()
    test_connectivity_diagnostic()
    print("\n🎉 ALL THINGSBOARD HTTP TESTS PASSED!")
