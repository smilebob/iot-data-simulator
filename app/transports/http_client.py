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
        protocol = "https" if use_tls else "http"
        # Omission du port si standard
        if (use_tls and port == 443) or (not use_tls and port == 80):
            url = f"{protocol}://{host}{endpoint}"
        else:
            url = f"{protocol}://{host}:{port}{endpoint}"

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
            "success": success or ("401" in message),  # Le serveur répond si 401
            "status_code": message,
            "latency_ms": latency_ms,
            "host": host,
            "port": port,
            "endpoint": endpoint,
            "use_tls": use_tls,
            "token_valid": success,
            "message": "Connexion ThingsBoard HTTP validée" if success else message,
            "recommendations": recommendations,
        }
