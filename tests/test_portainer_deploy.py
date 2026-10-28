"""
Unit Tests for Portainer Deployment Automation
==============================================
Validates environment file parsing, webhook triggering, and REST API redeployment.
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import deployment automation module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import portainer_deploy


def test_load_env_file(tmp_path):
    """Verifies that .env configuration files are parsed without external dependencies."""
    env_content = """
    # Comment to ignore
    PORTAINER_WEBHOOK_URL=http://localhost:9000/api/stacks/webhooks/test-uuid
    PORTAINER_URL="https://portainer.lan:9443"
    PORTAINER_API_KEY='ptr_123456789'
    PORTAINER_STACK_NAME=iot-simulator
    PORTAINER_ENDPOINT_ID=2
    """
    env_file = tmp_path / ".env.test"
    env_file.write_text(env_content, encoding="utf-8")

    res = portainer_deploy.load_env_file(env_file)
    assert res["PORTAINER_WEBHOOK_URL"] == "http://localhost:9000/api/stacks/webhooks/test-uuid"
    assert res["PORTAINER_URL"] == "https://portainer.lan:9443"
    assert res["PORTAINER_API_KEY"] == "ptr_123456789"
    assert res["PORTAINER_STACK_NAME"] == "iot-simulator"
    assert res["PORTAINER_ENDPOINT_ID"] == "2"


def test_trigger_webhook_success():
    """Tests successful Portainer webhook invocation handling HTTP 204 No Content."""
    with patch("portainer_deploy.make_request") as mock_req:
        mock_req.return_value = {
            "success": True,
            "status_code": 204,
            "data": None,
            "raw": ""
        }
        ok = portainer_deploy.trigger_webhook("http://192.168.1.50:9000/api/stacks/webhooks/dummy")
        assert ok is True
        mock_req.assert_called_once_with("http://192.168.1.50:9000/api/stacks/webhooks/dummy", method="POST", insecure=False)


def test_trigger_webhook_failure():
    """Tests webhook invocation error handling on HTTP 404 Not Found."""
    with patch("portainer_deploy.make_request") as mock_req:
        mock_req.return_value = {
            "success": False,
            "status_code": 404,
            "data": "Stack not found",
            "raw": "Stack not found",
            "error": "HTTP Error 404"
        }
        ok = portainer_deploy.trigger_webhook("http://192.168.1.50:9000/api/stacks/webhooks/dummy")
        assert ok is False


def test_redeploy_via_api_git_stack():
    """Tests the full API redeployment sequence against a Git-backed Portainer stack."""
    with patch("portainer_deploy.make_request") as mock_req:
        # Call 1: GET /api/endpoints
        # Call 2: GET /api/stacks
        # Call 3: PUT /api/stacks/42/git/redeploy
        def side_effect(url, method="GET", **kwargs):
            if "/api/endpoints" in url:
                return {
                    "success": True,
                    "status_code": 200,
                    "data": [{"Id": 1, "Name": "primary"}],
                    "raw": ""
                }
            elif "/api/stacks/" in url and "/git/redeploy" in url:
                return {
                    "success": True,
                    "status_code": 200,
                    "data": {"Id": 42, "Name": "iot-simulator", "Status": 1},
                    "raw": ""
                }
            elif "/api/stacks" in url:
                return {
                    "success": True,
                    "status_code": 200,
                    "data": [
                        {"Id": 42, "Name": "iot-simulator", "GitConfig": {"URL": "https://github.com/smilebob/iot-data-simulator"}}
                    ],
                    "raw": ""
                }
            return {"success": False, "status_code": 404, "data": None, "raw": ""}

        mock_req.side_effect = side_effect

        ok = portainer_deploy.redeploy_via_api(
            base_url="http://192.168.1.50:9000",
            api_key="ptr_secret_test",
            stack_name="iot-simulator",
            pull_image=True
        )
        assert ok is True
        assert mock_req.call_count == 3
