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
    Client de transmission HTTP / HTTPS vers l'API REST v1 de ThingsBoard.
    Supporte :
    - Télémétrie : POST /api/v1/{token}/telemetry
    - Attributs : POST /api/v1/{token}/attributes
    - Fallback transparent (httpx si présent, urllib natif standard en alternative)
    """

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    @staticmethod
    def build_url(host: str, port: int, endpoint: str, use_tls: bool) -> Tuple[str, bool]:
        """
        Assainit l'hôte, déduit le schéma TLS et construit l'URL absolue sans duplication.
        Tolère les préfixes 'http://', 'https://' ou les suffixes de chemin saisis par l'utilisateur.
        """
        h = (host or "localhost").strip()
        actual_tls = use_tls
        if h.lower().startswith("https://"):
            h = h[8:]
            actual_tls = True
        elif h.lower().startswith("http://"):
            h = h[7:]
            actual_tls = False

        # Supprimer tout port ou chemin résiduel dans le champ host
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
        Transmet un payload JSON vers l'endpoint ThingsBoard spécifié.
        Retourne (success, message_ou_erreur).
        """
        url, use_tls = self.build_url(host, port, endpoint, use_tls)
        req_headers = {**DEFAULT_HEADERS, "Content-Type": "application/json"}

        try:
            # Essai avec httpx si disponible
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
                        err_msg = f"HTTP 401 Non Autorisé (Vérifiez le Token de l'équipement) sur {url}"
                        logger.error(err_msg)
                        return False, err_msg
                    elif resp.status_code == 403:
                        err_msg = f"HTTP 403 Interdit (Vérifiez les règles Cloudflare / WAF) sur {url}"
                        logger.error(err_msg)
                        return False, err_msg
                    else:
                        err_msg = f"HTTP {resp.status_code} ({resp.text[:100]}) sur {url}"
                        logger.warning(err_msg)
                        return False, err_msg
            except ImportError:
                # Fallback sur urllib standard
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
                            return False, f"HTTP 401 Non Autorisé (Vérifiez le Token de l'équipement) sur {url}"
                        elif he.code == 403:
                            return False, f"HTTP 403 Interdit (Vérifiez les règles Cloudflare / WAF) sur {url}"
                        return False, f"HTTP {he.code} ({he.reason}) sur {url}"
                    except Exception as ex:
                        return False, f"Erreur réseau: {ex}"

                return await asyncio.to_thread(_sync_post)

        except Exception as e:
            err_msg = f"Erreur transmission HTTP vers {url}: {e}"
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
        Interroge ThingsBoard en Long-Polling HTTP pour recevoir les commandes RPC descendantes.
        GET /api/v1/{token}/rpc?timeout={timeout_ms}
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
                        logger.error(f"❌ [HTTP RPC] HTTP 401 Non Autorisé sur {url} : Token '{token[:4]}***' rejeté par ThingsBoard")
                    elif resp.status_code == 403:
                        logger.error(f"❌ [HTTP RPC] HTTP 403 Interdit sur {url} (Rejeté par Cloudflare / WAF)")
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
                            logger.error(f"❌ [HTTP RPC] HTTP 401 Non Autorisé sur {url} : Token '{token[:4]}***' rejeté par ThingsBoard")
                        elif he.code == 403:
                            logger.error(f"❌ [HTTP RPC] HTTP 403 Interdit sur {url} (Rejeté par Cloudflare / WAF)")
                        elif he.code in (408, 504):
                            pass  # Timeout normal du Long-Polling ThingsBoard
                        else:
                            logger.warning(f"⚠️ [HTTP RPC] Code HTTP {he.code} sur {url}")
                    except (urllib.error.URLError, TimeoutError, OSError) as ue:
                        err_str = str(ue).lower()
                        if "timed out" not in err_str and "timeout" not in err_str:
                            logger.debug(f"[HTTP RPC] Exception polling sur {url} : {ue}")
                    return None

                return await asyncio.to_thread(_sync_get)
        except Exception as e:
            logger.debug(f"[HTTP RPC] Erreur inattendue poll_rpc : {e}")
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
        Interroge ThingsBoard en Long-Polling HTTP pour recevoir les mises à jour des Attributs Partagés.
        GET /api/v1/{token}/attributes/updates?timeout={timeout_ms}
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
                        logger.error(f"❌ [HTTP Attributes] HTTP 401 Non Autorisé sur {url} : Token '{token[:4]}***' rejeté")
                    elif resp.status_code == 403:
                        logger.error(f"❌ [HTTP Attributes] HTTP 403 Interdit sur {url} (Rejeté par Cloudflare / WAF)")
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
                            logger.error(f"❌ [HTTP Attributes] HTTP 401 sur {url}")
                        elif he.code in (408, 504):
                            pass  # Timeout normal du Long-Polling
                    except Exception:
                        pass
                    return None

                return await asyncio.to_thread(_sync_get)
        except Exception as e:
            logger.debug(f"[HTTP Attributes] Erreur poll_attribute_updates : {e}")
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
        Récupère les valeurs actuelles des attributs partagés sur ThingsBoard.
        GET /api/v1/{token}/attributes?sharedKeys=key1,key2
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
            logger.debug(f"[HTTP Attributes] Erreur get_shared_attributes : {e}")
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
        Répond à une commande RPC bidirectionnelle ThingsBoard sur l'API HTTP.
        POST /api/v1/{token}/rpc/{req_id}
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
            logger.info(f"📤 [HTTP RPC] Réponse acquittée avec succès pour req #{req_id} vers {endpoint}")
        else:
            logger.error(f"❌ [HTTP RPC] Échec acquittement réponse {endpoint} : {detail}")
        return success

    async def test_connectivity(
        self,
        host: str,
        port: int,
        token: Optional[str] = None,
        use_tls: bool = True,
    ) -> Dict[str, Any]:
        """
        Diagnostic de connectivité HTTP vers ThingsBoard.
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
