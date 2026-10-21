import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("iot_sim.http")

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

        try:
            # Essai avec httpx si disponible
            try:
                import httpx
                async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
                    resp = await client.post(
                        url,
                        content=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    if resp.status_code in (200, 204):
                        return True, f"HTTP {resp.status_code}"
                    elif resp.status_code == 401:
                        err_msg = f"HTTP 401 Non Autorisé (Vérifiez le Token de l'équipement) sur {url}"
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
                import urllib.request

                def _sync_post():
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request(
                        url,
                        data=payload.encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=self.timeout, context=ctx if use_tls else None) as resp:
                        return resp.status

                code = await asyncio.to_thread(_sync_post)
                if code in (200, 204):
                    return True, f"HTTP {code}"
                return False, f"HTTP {code}"

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

        try:
            try:
                import httpx
                async with httpx.AsyncClient(verify=False, timeout=timeout_sec + 5.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200 and resp.text.strip():
                        return resp.json()
                    return None
            except ImportError:
                import asyncio
                import ssl
                import urllib.request

                def _sync_get():
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request(url, method="GET")
                    with urllib.request.urlopen(req, timeout=timeout_sec + 5.0, context=ctx if use_tls else None) as resp:
                        if resp.status == 200:
                            body = resp.read().decode("utf-8")
                            if body.strip():
                                return json.loads(body)
                    return None

                return await asyncio.to_thread(_sync_get)
        except Exception:
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
        success, _ = await self.post_payload(
            host=host,
            port=port,
            endpoint=endpoint,
            payload=resp_payload,
            use_tls=use_tls,
        )
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
