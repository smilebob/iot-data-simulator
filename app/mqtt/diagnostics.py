import socket
import ssl
import time
from typing import Any, Dict
from app.models.broker import BrokerConfig

def test_broker_connectivity(config: BrokerConfig) -> Dict[str, Any]:
    """
    Diagnostique complet de connectivité réseau vers un broker MQTT.
    Vérifie la résolution DNS, l'accessibilité du port TCP, le handshake TLS et fournit des conseils clairs.
    """
    host = config.host.strip()
    port = config.port
    use_tls = config.use_tls or port in (8883, 443)
    transport = getattr(config, "transport", "tcp").lower()

    diag = {
        "host": host,
        "port": port,
        "transport": transport,
        "dns_ok": False,
        "dns_ips": [],
        "tcp_ok": False,
        "tls_ok": False if use_tls else None,
        "latency_ms": None,
        "is_cloudflare": False,
        "verdict": "FAIL",
        "message": "",
        "suggestion": "",
    }

    # 1. Test Résolution DNS
    try:
        addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        ips = list(set([item[4][0] for item in addr_info]))
        diag["dns_ok"] = True
        diag["dns_ips"] = ips

        # Détection Cloudflare
        for ip in ips:
            if ip.startswith("104.18.") or ip.startswith("104.19.") or ip.startswith("172.67."):
                diag["is_cloudflare"] = True
                break
    except Exception as e:
        diag["message"] = f"Échec résolution DNS pour '{host}': {e}"
        diag["suggestion"] = "Vérifiez l'orthographe du nom d'hôte ou votre connexion réseau."
        return diag

    # 2. Test Socket TCP
    t0 = time.time()
    s = None
    try:
        s = socket.create_connection((host, port), timeout=4.0)
        latency = (time.time() - t0) * 1000
        diag["tcp_ok"] = True
        diag["latency_ms"] = round(latency, 1)
    except socket.timeout:
        diag["message"] = f"Timeout de connexion vers {host}:{port} (aucune réponse après 4s)"
        if diag["is_cloudflare"] and port in (1883, 8883):
            diag["suggestion"] = (
                f"Attention : Le domaine '{host}' est hébergé derrière Cloudflare (IP: {', '.join(ips)}). "
                "Cloudflare bloque par défaut les ports TCP bruts 1883 et 8883. "
                "Pour ThingsBoard sous Cloudflare, utilisez l'adresse IP directe du serveur ou le port WebSockets 443."
            )
        else:
            diag["suggestion"] = f"Le port {port} est fermé ou filtré par un pare-feu sur le serveur distant."
        return diag
    except ConnectionRefusedError:
        diag["message"] = f"Connexion refusée par {host}:{port}"
        diag["suggestion"] = f"Aucun service n'écoute sur le port {port} à cette adresse."
        return diag
    except Exception as e:
        diag["message"] = f"Erreur de connexion TCP vers {host}:{port}: {e}"
        return diag

    # 3. Test Handshake TLS si requis
    if use_tls:
        try:
            ctx = ssl.create_default_context()
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            if not config.ca_cert_path:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

            wrapped = ctx.wrap_socket(s, server_hostname=host)
            diag["tls_ok"] = True
            cipher = wrapped.cipher()
            diag["tls_cipher"] = cipher[0] if cipher else "Unknown"
            wrapped.close()
        except Exception as e:
            diag["tls_ok"] = False
            diag["message"] = f"Échec de négociation TLS sur {host}:{port}: {e}"
            diag["suggestion"] = "Vérifiez que le serveur supporte TLS 1.2+ ou vérifiez le certificat CA."
            return diag
    else:
        try:
            s.close()
        except Exception:
            pass

    diag["verdict"] = "SUCCESS"
    diag["message"] = f"Connectivité réseau OK vers {host}:{port} (latence {diag['latency_ms']}ms)"
    return diag
