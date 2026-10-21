import asyncio
import json
import logging
import os
import socket
import struct
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("iot_sim.coap")

class ThingsBoardCoapClient:
    """
    Client CoAP (Constrained Application Protocol - RFC 7252) sur UDP
    pour la plateforme ThingsBoard.
    
    Permet la transmission directe de télémétrie et d'attributs sans overhead TCP/HTTP.
    URI Cible : coap://{host}:{port}/api/v1/{token}/telemetry
    """

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self._msg_id = 1

    def _next_msg_id(self) -> int:
        mid = self._msg_id
        self._msg_id = (self._msg_id + 1) & 0xFFFF
        if self._msg_id == 0:
            self._msg_id = 1
        return mid

    def _build_coap_packet(
        self,
        path_segments: List[str],
        payload: bytes,
        is_con: bool = False,
    ) -> bytes:
        """
        Construit un paquet CoAP binaire conforme RFC 7252 :
        - Type : NON (Non-Confirmable = 1) par défaut pour cadence rapide, ou CON (0)
        - Code : 0.02 (POST)
        - Options : Uri-Path (11) répétée par segment, Content-Format = 50 (12)
        - Payload : UTF-8 JSON
        """
        t_val = 0 if is_con else 1
        token = os.urandom(4)
        msg_id = self._next_msg_id()

        # En-tête CoAP (4 octets) : Ver (2 bits = 1), Type (2 bits), TKL (4 bits), Code, Message ID
        header = struct.pack("!BBH", (1 << 6) | (t_val << 4) | len(token), 0x02, msg_id)
        packet = bytearray(header)
        packet.extend(token)

        last_opt_num = 0

        # Encodage des segments de l'Uri-Path (Option 11)
        for segment in path_segments:
            seg_bytes = segment.encode("utf-8")
            delta = 11 - last_opt_num
            last_opt_num = 11

            d_nibble = delta if delta < 13 else 13
            d_extra = bytearray([delta - 13]) if delta >= 13 else bytearray()
            
            l_len = len(seg_bytes)
            l_nibble = l_len if l_len < 13 else 13
            l_extra = bytearray([l_len - 13]) if l_len >= 13 else bytearray()

            packet.append((d_nibble << 4) | l_nibble)
            packet.extend(d_extra)
            packet.extend(l_extra)
            packet.extend(seg_bytes)

        # Encodage de Content-Format: application/json (Option 12 = 50)
        delta = 12 - last_opt_num
        last_opt_num = 12
        packet.append((delta << 4) | 1)
        packet.append(50)

        # Marqueur de payload (0xFF) puis données utiles
        if payload:
            packet.append(0xFF)
            packet.extend(payload)

        return bytes(packet)

    async def send_payload(
        self,
        host: str,
        port: int,
        path_segments: List[str],
        payload: str,
        wait_response: bool = False,
    ) -> Tuple[bool, str]:
        """
        Envoie un datagramme CoAP UDP vers ThingsBoard.
        """
        payload_bytes = payload.encode("utf-8")
        packet = self._build_coap_packet(path_segments, payload_bytes, is_con=wait_response)

        def _sync_udp_send():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            try:
                sock.sendto(packet, (host, port))
                if wait_response:
                    data, _ = sock.recvfrom(2048)
                    if len(data) >= 2:
                        code = data[1]
                        code_class = code >> 5
                        code_detail = code & 0x1F
                        code_str = f"{code_class}.{code_detail:02d}"
                        # 2.01 Created, 2.04 Changed, 2.05 Content
                        if code_class == 2:
                            return True, f"CoAP {code_str} Succès"
                        elif code_str == "4.01":
                            return False, f"CoAP 4.01 Non Autorisé (Token invalide)"
                        return False, f"CoAP Code {code_str}"
                return True, "CoAP NON envoyé"
            finally:
                sock.close()

        try:
            success, msg = await asyncio.to_thread(_sync_udp_send)
            return success, msg
        except socket.timeout:
            err_msg = f"Timeout CoAP UDP ({self.timeout}s) vers {host}:{port}"
            logger.warning(err_msg)
            return False, err_msg
        except Exception as e:
            err_msg = f"Erreur CoAP vers {host}:{port}: {e}"
            logger.error(err_msg)
            return False, str(e)

    async def test_connectivity(
        self,
        host: str,
        port: int,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Diagnostic de connectivité CoAP UDP vers ThingsBoard.
        """
        token_str = token.strip() if token and token.strip() else "test_token"
        segments = ["api", "v1", token_str, "telemetry"]
        test_payload = json.dumps({"_test_ping": 1})

        t0 = time.perf_counter()
        success, message = await self.send_payload(
            host=host,
            port=port,
            path_segments=segments,
            payload=test_payload,
            wait_response=True,
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        recommendations = []
        if success:
            recommendations.append(f"Le serveur ThingsBoard a accusé réception du paquet CoAP ({message}).")
        elif "4.01" in message:
            recommendations.append("Le service CoAP ThingsBoard écoute et répond, mais le Token a été rejeté (4.01 Unauthorized).")
        elif "Timeout" in message:
            recommendations.append("Le port CoAP UDP 5683 ne répond pas. Vérifiez que le service CoAP de ThingsBoard est activé et accessible.")
            recommendations.append("Attention : si l'hôte est derrière Cloudflare ou un pare-feu standard, les paquets UDP sont généralement filtrés.")
        else:
            recommendations.append(f"Erreur CoAP : {message}")

        return {
            "protocol": "coap",
            "success": success or ("4.01" in message),
            "status_code": message,
            "latency_ms": latency_ms,
            "host": host,
            "port": port,
            "path": "/" + "/".join(segments),
            "token_valid": success,
            "message": message,
            "recommendations": recommendations,
        }
