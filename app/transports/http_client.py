"""
ThingsBoard HTTP / HTTPS REST API Client with Long-Polling and Dual Fallback.

This module implements an asynchronous HTTP client optimized for ThingsBoard's
REST v1 device gateway API:
- Telemetry: `POST /api/v1/{token}/telemetry`
- Client Attributes: `POST /api/v1/{token}/attributes`
- Shared Attribute Polling: `GET /api/v1/{token}/attributes/updates?timeout={ms}`
- Bidirectional RPC Polling: `GET /api/v1/{token}/rpc?timeout={ms}`
- RPC Response: `POST /api/v1/{token}/rpc/{id}`

Execution Engine & Fault Tolerance:
- Uses `httpx.AsyncClient` with non-blocking async sockets when available.
- Seamlessly falls back to `asyncio.to_thread` wrapping standard library `urllib.request`
  if `httpx` is not installed, eliminating external dependencies.
- Handles Cloudflare / WAF security challenges, TLS verification bypass, and HTTP 401/403 diagnostics.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("iot_sim.http")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

class ThingsBoardHttpClient:
    """
    HTTP/HTTPS communication client for ThingsBoard v1 REST API.

    Supports one-way telemetry publishing, bidirectional RPC execution,
    and long-polling for real-time shared attribute updates.

    Attributes:
        timeout: Request timeout duration in seconds.
    """

    def __init__(self, timeout: float = 5.0) -> None:
        """
        Initializes the HTTP client.

        Args:
            timeout: Connection and read timeout in seconds. Defaults to 5.0.
        """
        self.timeout: float = timeout

    @staticmethod
    def build_url(host: str, port: int, endpoint: str, use_tls: bool) -> Tuple[str, bool]:
        """
        Sanitizes hostname inputs, resolves scheme, and constructs an absolute URL.

        Gracefully strips accidental protocol prefixes ('http://', 'https://'),
        inline port numbers, or trailing slashes in user-provided host strings.

        Args:
            host: Target hostname or IP address.
            port: Target port number.
            endpoint: URL path endpoint (e.g., '/api/v1/{token}/telemetry').
            use_tls: Flag requesting HTTPS encryption.

        Returns:
            Tuple[str, bool]: Canonical URL and effective TLS boolean state.
        """
        h = (host or "localhost").strip()
        actual_tls = use_tls
        if h.lower().startswith("https://"):
            h = h[8:]
            actual_tls = True
        elif h.lower().startswith("http://"):
            h = h[7:]
            actual_tls = False

        # Strip lingering port or path parts from the host string
        h = h.split("/")[0].strip()
        if ":" in h:
            parts = h.split(":")
            h = parts[0].strip()
            try:
                port = int(parts[1])
            except ValueError:
                pass

        protocol = "https" if actual_tls else "http"
        ep = "/" + endpoint.lstrip("/")
        if (actual_tls and port == 443) or (not actual_tls and port == 80):
            url = f"{protocol}://{h}{ep}"
        else:
            url = f"{protocol}://{h}:{port}{ep}"
        return url, actual_tls

    async def post_payload(
        self,
        host: str,
        port: int,
        endpoint: str,
        payload: str,
        use_tls: bool = True,
    ) -> Tuple[bool, str]:
        """
        Transmits a JSON payload to a specified ThingsBoard REST endpoint.

        Attempts execution via `httpx` first; falls back to standard `urllib` on ImportError.

        Args:
            host: Target server host.
            port: Target port.
            endpoint: Relative path endpoint.
            payload: Serialized JSON payload string.
            use_tls: Whether to use HTTPS. Defaults to True.

        Returns:
            Tuple[bool, str]: Success boolean and HTTP status or error description.
        """
        url, use_tls = self.build_url(host, port, endpoint, use_tls)
        req_headers = {**DEFAULT_HEADERS, "Content-Type": "application/json"}

        try:
            # Attempt with httpx if installed
            try:
                import httpx
                async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
                    resp = await client.post(
                        url,
                        content=payload,
                        headers=req_headers
                    )
                    if resp.status_code in (200, 204):
                        return True, f"HTTP {resp.status_code}"
                    elif resp.status_code == 401:
                        err_msg = f"HTTP 401 Unauthorized (Check Device Access Token) on {url}"
                        logger.error(err_msg)
                        return False, err_msg
                    elif resp.status_code == 403:
                        err_msg = f"HTTP 403 Forbidden (Check Cloudflare / WAF rules) on {url}"
                        logger.error(err_msg)
                        return False, err_msg
                    else:
                        err_msg = f"HTTP {resp.status_code} ({resp.text[:100]}) on {url}"
                        logger.warning(err_msg)
                        return False, err_msg
            except ImportError:
                # Fallback to standard library urllib
                import asyncio
                import ssl
                import urllib.error
                import urllib.request

                def _sync_post():
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request(
                        url,
                        data=payload.encode("utf-8"),
                        headers=req_headers,
                        method="POST"
                    )
                    try:
                        with urllib.request.urlopen(req, timeout=self.timeout, context=ctx if use_tls else None) as resp:
                            return True, f"HTTP {resp.status}"
                    except urllib.error.HTTPError as he:
                        if he.code == 401:
                            return False, f"HTTP 401 Unauthorized (Check Device Access Token) on {url}"
                        elif he.code == 403:
                            return False, f"HTTP 403 Forbidden (Check Cloudflare / WAF rules) on {url}"
                        return False, f"HTTP {he.code} ({he.reason}) on {url}"
                    except Exception as ex:
                        return False, f"Network error: {ex}"

                return await asyncio.to_thread(_sync_post)

        except Exception as e:
            err_msg = f"HTTP transmission error to {url}: {e}"
            logger.error(err_msg)
            return False, str(e)

    async def poll_rpc(
        self,
        host: str,
        port: int,
        token: str,
        timeout_sec: int = 15,
        use_tls: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Polls ThingsBoard via HTTP Long-Polling for pending downstream RPC commands.

        Issues a GET request to `/api/v1/{token}/rpc?timeout={timeout_ms}`.

        Args:
            host: ThingsBoard server hostname.
            port: ThingsBoard server port.
            token: Device access token.
            timeout_sec: Long-polling hold duration in seconds. Defaults to 15.
            use_tls: HTTPS encryption flag. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: Deserialized RPC request dictionary if received, else None.
        """
        endpoint = f"/api/v1/{token}/rpc?timeout={int(timeout_sec * 1000)}"
        url, use_tls = self.build_url(host, port, endpoint, use_tls)
        req_headers = dict(DEFAULT_HEADERS)

        try:
            try:
                import httpx
                async with httpx.AsyncClient(verify=False, timeout=timeout_sec + 5.0) as client:
                    resp = await client.get(url, headers=req_headers)
                    if resp.status_code == 200 and resp.text.strip():
                        return resp.json()
                    elif resp.status_code == 401:
                        logger.error(f"❌ [HTTP RPC] HTTP 401 Unauthorized on {url}: Token '{token[:4]}***' rejected by ThingsBoard")
                    elif resp.status_code == 403:
                        logger.error(f"❌ [HTTP RPC] HTTP 403 Forbidden on {url} (Blocked by Cloudflare / WAF)")
                    return None
            except ImportError:
                import asyncio
                import ssl
                import urllib.error
                import urllib.request

                def _sync_get():
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request(url, headers=req_headers, method="GET")
                    try:
                        with urllib.request.urlopen(req, timeout=timeout_sec + 5.0, context=ctx if use_tls else None) as resp:
                            if resp.status == 200:
                                body = resp.read().decode("utf-8")
                                if body.strip():
                                    return json.loads(body)
                    except urllib.error.HTTPError as he:
                        if he.code == 401:
                            logger.error(f"❌ [HTTP RPC] HTTP 401 Unauthorized on {url}: Token '{token[:4]}***' rejected by ThingsBoard")
                        elif he.code == 403:
                            logger.error(f"❌ [HTTP RPC] HTTP 403 Forbidden on {url} (Blocked by Cloudflare / WAF)")
                        elif he.code in (408, 504):
                            pass  # Standard ThingsBoard long-polling timeout
                        else:
                            logger.warning(f"⚠️ [HTTP RPC] HTTP status code {he.code} on {url}")
                    except (urllib.error.URLError, TimeoutError, OSError) as ue:
                        err_str = str(ue).lower()
                        if "timed out" not in err_str and "timeout" not in err_str:
                            logger.debug(f"[HTTP RPC] Polling exception on {url}: {ue}")
                    return None

                return await asyncio.to_thread(_sync_get)
        except Exception as e:
            logger.debug(f"[HTTP RPC] Unexpected poll_rpc error: {e}")
            return None

    async def poll_attribute_updates(
        self,
        host: str,
        port: int,
        token: str,
        timeout_sec: int = 20,
        use_tls: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Polls ThingsBoard via HTTP Long-Polling for updates to Shared Attributes.

        Issues a GET request to `/api/v1/{token}/attributes/updates?timeout={timeout_ms}`.

        Args:
            host: ThingsBoard server hostname.
            port: ThingsBoard server port.
            token: Device access token.
            timeout_sec: Long-polling hold duration in seconds. Defaults to 20.
            use_tls: HTTPS encryption flag. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: Dictionary of updated shared attributes, or None if timed out.
        """
        endpoint = f"/api/v1/{token}/attributes/updates?timeout={int(timeout_sec * 1000)}"
        url, use_tls = self.build_url(host, port, endpoint, use_tls)
        req_headers = dict(DEFAULT_HEADERS)

        try:
            try:
                import httpx
                async with httpx.AsyncClient(verify=False, timeout=timeout_sec + 5.0) as client:
                    resp = await client.get(url, headers=req_headers)
                    if resp.status_code == 200 and resp.text.strip():
                        return resp.json()
                    elif resp.status_code == 401:
                        logger.error(f"❌ [HTTP Attributes] HTTP 401 Unauthorized on {url}: Token '{token[:4]}***' rejected")
                    elif resp.status_code == 403:
                        logger.error(f"❌ [HTTP Attributes] HTTP 403 Forbidden on {url} (Blocked by Cloudflare / WAF)")
                    return None
            except ImportError:
                import asyncio
                import ssl
                import urllib.error
                import urllib.request

                def _sync_get():
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request(url, headers=req_headers, method="GET")
                    try:
                        with urllib.request.urlopen(req, timeout=timeout_sec + 5.0, context=ctx if use_tls else None) as resp:
                            if resp.status == 200:
                                body = resp.read().decode("utf-8")
                                if body.strip():
                                    return json.loads(body)
                    except urllib.error.HTTPError as he:
                        if he.code == 401:
                            logger.error(f"❌ [HTTP Attributes] HTTP 401 on {url}")
                        elif he.code in (408, 504):
                            pass  # Standard long-polling timeout
                    except Exception:
                        pass
                    return None

                return await asyncio.to_thread(_sync_get)
        except Exception as e:
            logger.debug(f"[HTTP Attributes] Error poll_attribute_updates: {e}")
            return None

    async def get_shared_attributes(
        self,
        host: str,
        port: int,
        token: str,
        shared_keys: Optional[List[str]] = None,
        use_tls: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches current values of shared attributes from ThingsBoard.

        Issues a GET request to `/api/v1/{token}/attributes?sharedKeys=key1,key2`.

        Args:
            host: ThingsBoard server hostname.
            port: ThingsBoard server port.
            token: Device access token.
            shared_keys: Optional list of attribute keys to retrieve.
            use_tls: HTTPS encryption flag. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: Key-value dictionary of shared attributes, or None on failure.
        """
        query = f"?sharedKeys={','.join(shared_keys)}" if shared_keys else ""
        endpoint = f"/api/v1/{token}/attributes{query}"
        url, use_tls = self.build_url(host, port, endpoint, use_tls)
        req_headers = dict(DEFAULT_HEADERS)

        try:
            try:
                import httpx
                async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                    resp = await client.get(url, headers=req_headers)
                    if resp.status_code == 200 and resp.text.strip():
                        res_json = resp.json()
                        return res_json.get("shared", res_json)
                    return None
            except ImportError:
                import asyncio
                import ssl
                import urllib.error
                import urllib.request

                def _sync_get():
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request(url, headers=req_headers, method="GET")
                    try:
                        with urllib.request.urlopen(req, timeout=10.0, context=ctx if use_tls else None) as resp:
                            if resp.status == 200:
                                res_json = json.loads(resp.read().decode("utf-8"))
                                return res_json.get("shared", res_json)
                    except Exception:
                        pass
                    return None

                return await asyncio.to_thread(_sync_get)
        except Exception as e:
            logger.debug(f"[HTTP Attributes] Error get_shared_attributes: {e}")
            return None

    async def respond_rpc(
        self,
        host: str,
        port: int,
        token: str,
        req_id: Any,
        resp_payload: str,
        use_tls: bool = True,
    ) -> bool:
        """
        Sends an acknowledgement and result for a bidirectional ThingsBoard RPC request.

        Issues a POST request to `/api/v1/{token}/rpc/{req_id}`.

        Args:
            host: ThingsBoard server hostname.
            port: ThingsBoard server port.
            token: Device access token.
            req_id: Unique RPC request ID issued by ThingsBoard.
            resp_payload: Serialized JSON response string.
            use_tls: HTTPS encryption flag. Defaults to True.

        Returns:
            bool: True if response was accepted by ThingsBoard, False otherwise.
        """
        endpoint = f"/api/v1/{token}/rpc/{req_id}"
        success, detail = await self.post_payload(
            host=host,
            port=port,
            endpoint=endpoint,
            payload=resp_payload,
            use_tls=use_tls,
        )
        if success:
            logger.info(f"📤 [HTTP RPC] Successfully acknowledged response for req #{req_id} to {endpoint}")
        else:
            logger.error(f"❌ [HTTP RPC] Failed acknowledging response to {endpoint}: {detail}")
        return success

    async def test_connectivity(
        self,
        host: str,
        port: int,
        token: Optional[str] = None,
        use_tls: bool = True,
    ) -> Dict[str, Any]:
        """
        Performs a full connectivity and authentication diagnostic to ThingsBoard REST API.

        Sends a probe ping to the telemetry endpoint to evaluate round-trip latency,
        WAF/firewall blocks, TLS handshake, and token validity.

        Args:
            host: Target server host.
            port: Target port.
            token: Optional device access token.
            use_tls: Whether HTTPS is expected.

        Returns:
            Dict[str, Any]: Diagnostic report with latency, validity flags, and guidance recommendations.
        """
        token_str = token.strip() if token and token.strip() else "test_token"
        endpoint = f"/api/v1/{token_str}/telemetry"
        test_payload = json.dumps({"_test_ping": 1})

        t0 = time.perf_counter()
        success, message = await self.post_payload(
            host=host,
            port=port,
            endpoint=endpoint,
            payload=test_payload,
            use_tls=use_tls,
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        token_valid = success
        server_reachable = success or ("401" in message)

        recommendations = []
        if success:
            recommendations.append("La passerelle HTTP ThingsBoard est joignable et le Token a été validé avec succès (HTTP 200 OK).")
        elif "401" in message:
            recommendations.append("Le serveur ThingsBoard répond en HTTP/HTTPS, mais le Token d'authentification a été rejeté (401 Unauthorized).")
            recommendations.append("Vérifiez l'Access Token de votre équipement dans la console ThingsBoard.")
        elif "403" in message:
            recommendations.append("Le serveur ou pare-feu Cloudflare/WAF a retourné une interdiction (403 Forbidden).")
            recommendations.append("Vérifiez l'autorisation de votre adresse IP ou vos règles de sécurité Cloudflare.")
        else:
            recommendations.append(f"Échec de connexion HTTP : {message}")
            if use_tls:
                recommendations.append("Vérifiez si le port 443 est ouvert ou tentez en HTTP non sécurisé (port 80).")
            else:
                recommendations.append("Tentez d'activer le chiffrement TLS / HTTPS (port 443).")

        return {
            "protocol": "http",
            "success": server_reachable,
            "status_code": message,
            "latency_ms": latency_ms,
            "host": host,
            "port": port,
            "endpoint": endpoint,
            "use_tls": use_tls,
            "token_valid": token_valid,
            "message": "Connexion ThingsBoard HTTP validée" if success else message,
            "recommendations": recommendations,
        }
