"""
ThingsBoard Platform Adapter.

This adapter formats data for ThingsBoard Community and Professional Editions:
- Telemetry payload: `{"ts": <timestamp_ms>, "values": {"<key>": <value>}}`
- Attributes payload: `{"<key>": <value>}`
- Default MQTT topics: `v1/devices/me/telemetry` and `v1/devices/me/attributes`
- HTTP endpoints: `/api/v1/{token}/telemetry` and `/api/v1/{token}/attributes`
- CoAP path segments: `["api", "v1", token, "telemetry"]`
- Incoming RPC command decoding from `v1/devices/me/rpc/request/{id}`
"""

import json
from typing import Any, List, Optional, Tuple
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig, VariableType
from app.platforms.base import BasePlatformAdapter

class ThingsBoardAdapter(BasePlatformAdapter):
    """
    Adapter implementing ThingsBoard gateway protocols (MQTT, HTTP, CoAP).

    Handles timestamped telemetry formatting, shared attribute synchronization,
    and server-side RPC parsing.
    """

    def get_default_topic(self, device: DeviceConfig, variable: VariableConfig) -> str:
        """
        Returns standard ThingsBoard MQTT topics.

        Args:
            device: Target device.
            variable: Variable to publish.

        Returns:
            str: 'v1/devices/me/attributes' for attributes, 'v1/devices/me/telemetry' otherwise.
        """
        if variable.var_type == VariableType.ATTRIBUTE:
            return "v1/devices/me/attributes"
        return "v1/devices/me/telemetry"

    def get_http_endpoint(self, device: DeviceConfig, variable: VariableConfig) -> str:
        """
        Returns ThingsBoard v1 REST API endpoint.

        Args:
            device: Target device containing access token.
            variable: Variable to publish.

        Returns:
            str: REST API path string.
        """
        token = device.token or "default"
        if variable.var_type == VariableType.ATTRIBUTE:
            return f"/api/v1/{token}/attributes"
        return f"/api/v1/{token}/telemetry"

    def get_coap_path_segments(self, device: DeviceConfig, variable: VariableConfig) -> List[str]:
        """
        Returns RFC 7252 CoAP URI path segments for ThingsBoard.

        Args:
            device: Target device containing access token.
            variable: Variable to publish.

        Returns:
            List[str]: Path segments list (e.g. ['api', 'v1', token, 'telemetry']).
        """
        token = device.token or "default"
        action = "attributes" if variable.var_type == VariableType.ATTRIBUTE else "telemetry"
        return ["api", "v1", token, action]

    def get_telemetry_key(self, variable: VariableConfig) -> str:
        """
        Extracts clean metric key without internal simulator device prefix.

        Args:
            variable: VariableConfig instance.

        Returns:
            str: Clean physical key name.
        """
        if variable.device_id and variable.id.startswith(f"{variable.device_id}_"):
            return variable.id[len(variable.device_id) + 1:]
        return variable.id

    def format_message(
        self,
        device: DeviceConfig,
        variable: VariableConfig,
        value: Any,
        timestamp_ms: int,
    ) -> Tuple[str, str]:
        """
        Formats payload into ThingsBoard native JSON structures.

        Args:
            device: Source device.
            variable: Variable being published.
            value: Current variable value.
            timestamp_ms: Millisecond epoch timestamp.

        Returns:
            Tuple[str, str]: (Topic, serialized JSON payload).
        """
        topic = variable.topic.strip() if variable.topic and variable.topic.strip() else self.get_default_topic(device, variable)
        key = self.get_telemetry_key(variable)

        if variable.var_type == VariableType.ATTRIBUTE:
            payload = json.dumps({key: value})
        else:
            payload = json.dumps({
                "ts": timestamp_ms,
                "values": {
                    key: value
                }
            })

        return topic, payload

    def handle_incoming_message(
        self,
        topic: str,
        payload: str,
    ) -> Optional[Tuple[str, Any]]:
        """
        Decodes incoming ThingsBoard RPC commands (`v1/devices/me/rpc/request/{id}`).

        Args:
            topic: MQTT arrival topic.
            payload: JSON command string.

        Returns:
            Optional[Tuple[str, Any]]: (method, params) tuple if valid RPC, else None.
        """
        if "v1/devices/me/rpc/request/" in topic:
            try:
                data = json.loads(payload)
                method = data.get("method")
                params = data.get("params")
                return method, params
            except Exception:
                return None
        return None
