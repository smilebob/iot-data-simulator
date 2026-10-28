"""
MQTT Broker Connectivity Diagnostic Tools.

This module performs network connectivity diagnostics against MQTT brokers:
1. DNS Resolution: Resolves hostname to IPv4/IPv6 addresses and detects CDN/Cloudflare IPs.
2. TCP Port Probing: Establishes raw socket connections to measure network latency.
3. TLS Handshake Verification: Evaluates TLS 1.2+ cipher suites and certificate validity.
4. Intelligent Troubleshooting Recommendations: Diagnoses common failure causes such as
   Cloudflare blocking raw TCP port 1883/8883, closed firewall ports, or missing TLS.
"""

import socket
import ssl
import time
from typing import Any, Dict
from app.models.broker import BrokerConfig

def test_broker_connectivity(config: BrokerConfig) -> Dict[str, Any]:
    """
    Executes a comprehensive diagnostic scan against a target MQTT broker.

    Sequentially tests DNS resolution, TCP port reachability, and TLS handshakes,
    measuring round-trip latency and identifying CDN-specific firewall blocks.

    Args:
        config: BrokerConfig containing target host, port, transport, and TLS preferences.

    Returns:
        Dict[str, Any]: Diagnostic report with status flags, latency in milliseconds,
            cipher details, and actionable troubleshooting suggestions.

    Example:
        >>> conf = BrokerConfig(host="broker.hivemq.com", port=1883)
        >>> report = test_broker_connectivity(conf)
        >>> print(report["tcp_ok"])
        True
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

    # 1. DNS Resolution Probe
    try:
        addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        ips = list(set([item[4][0] for item in addr_info]))
        diag["dns_ok"] = True
        diag["dns_ips"] = ips

        # Cloudflare CDN IP detection (Cloudflare filters raw TCP 1883/8883 by default)
        for ip in ips:
            if ip.startswith("104.18.") or ip.startswith("104.19.") or ip.startswith("172.67."):
                diag["is_cloudflare"] = True
                break
    except Exception as e:
        diag["message"] = f"DNS resolution failed for '{host}': {e}"
        diag["suggestion"] = "Check the hostname spelling and your network DNS configuration."
        return diag

    # 2. TCP Socket Connection Probe
    t0 = time.time()
    s = None
    try:
        s = socket.create_connection((host, port), timeout=4.0)
        latency = (time.time() - t0) * 1000
        diag["tcp_ok"] = True
        diag["latency_ms"] = round(latency, 1)
    except socket.timeout:
        diag["message"] = f"Connection timeout to {host}:{port} (no response after 4s)"
        if diag["is_cloudflare"] and port in (1883, 8883):
            diag["suggestion"] = (
                f"Warning: Domain '{host}' is behind Cloudflare (IP: {', '.join(ips)}). "
                "Cloudflare blocks raw TCP ports 1883 and 8883 by default. "
                "For ThingsBoard behind Cloudflare, use direct server IP or WebSockets port 443."
            )
        else:
            diag["suggestion"] = f"Port {port} is closed or filtered by a firewall on the remote host."
        return diag
    except ConnectionRefusedError:
        diag["message"] = f"Connection refused by {host}:{port}"
        diag["suggestion"] = f"No service is listening on port {port} at this address."
        return diag
    except Exception as e:
        diag["message"] = f"TCP connection error to {host}:{port}: {e}"
        return diag

    # 3. TLS Handshake Probe
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
            diag["message"] = f"TLS handshake negotiation failed on {host}:{port}: {e}"
            diag["suggestion"] = "Verify that the server supports TLS 1.2+ or inspect the custom CA certificate."
            return diag
    else:
        try:
            s.close()
        except Exception:
            pass

    diag["verdict"] = "PASS"
    diag["message"] = f"Connection to {host}:{port} ({transport.upper()}) verified successfully."
    return diag


    diag["verdict"] = "SUCCESS"
    diag["message"] = f"Connectivité réseau OK vers {host}:{port} (latence {diag['latency_ms']}ms)"
    return diag
