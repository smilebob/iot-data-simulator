"""
Constrained Application Protocol (CoAP - RFC 7252) UDP Client for ThingsBoard.

This module implements a lightweight, native binary CoAP client over UDP without
third-party dependencies. It is specifically tailored for constrained IoT telemetry
transmission to ThingsBoard:
- Target URI: `coap://{host}:{port}/api/v1/{token}/telemetry`
- Message format: RFC 7252 binary headers with Uri-Path (option 11) delta compression
  and Content-Format: application/json (option 12, value 50).
- Supports Non-Confirmable (NON) mode for high-frequency low-overhead telemetry,
  and Confirmable (CON) mode with ACK parsing for diagnostic ping verification.
"""

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
    Native CoAP client over UDP (RFC 7252) for ThingsBoard IoT gateways.

    Provides high-throughput, low-bandwidth telemetry transmission without TCP handshakes.

    Attributes:
        timeout: Socket receive timeout duration in seconds.
    """

    def __init__(self, timeout: float = 3.0) -> None:
        """
        Initializes the CoAP UDP client.

        Args:
            timeout: Socket timeout in seconds. Defaults to 3.0.
        """
        self.timeout: float = timeout
        self._msg_id: int = 1

    def _next_msg_id(self) -> int:
        """
        Generates the next sequential 16-bit message ID (rolls over at 0xFFFF).

        Returns:
            int: Unsigned 16-bit integer message ID.
        """
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
        Encodes a binary RFC 7252 CoAP datagram with options delta packing.

        Header layout (4 bytes):
        - Bits 0-1: Version (1)
        - Bits 2-3: Type (0=CON, 1=NON)
        - Bits 4-7: Token length (4 bytes)
        - Byte 1: Code (0.02 = POST)
        - Bytes 2-3: Message ID (16-bit unsigned)

        Options:
        - Uri-Path (Option 11): Repeated for each path segment.
        - Content-Format (Option 12): Value 50 (`application/json`).
        - Payload Marker: `0xFF` followed by UTF-8 JSON payload bytes.

        Args:
            path_segments: List of URI path strings (e.g., ['api', 'v1', token, 'telemetry']).
            payload: Encoded UTF-8 payload bytes.
            is_con: If True, marks message as CON (Confirmable). Otherwise NON.

        Returns:
            bytes: Assembled binary CoAP packet.
        """
        t_val = 0 if is_con else 1
        token = os.urandom(4)
        msg_id = self._next_msg_id()

        # CoAP Header (4 bytes): Ver (2 bits = 1), Type (2 bits), TKL (4 bits), Code (0x02 POST), Message ID
        header = struct.pack("!BBH", (1 << 6) | (t_val << 4) | len(token), 0x02, msg_id)
        packet = bytearray(header)
        packet.extend(token)

        last_opt_num = 0

        # Encode Uri-Path options (Option 11) with delta compression
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

        # Encode Content-Format: application/json (Option 12 = 50)
        delta = 12 - last_opt_num
        last_opt_num = 12
        packet.append((delta << 4) | 1)
        packet.append(50)

        # Payload marker (0xFF) followed by payload content
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
        Transmits a CoAP UDP datagram to the target ThingsBoard server.

        Args:
            host: Server hostname or IP address.
            port: UDP port (typically 5683).
            path_segments: Path hierarchy segments.
            payload: JSON payload string.
            wait_response: If True, waits synchronously for an ACK/response datagram.

        Returns:
            Tuple[bool, str]: (Success boolean, descriptive status message).
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
                            return True, f"CoAP {code_str} Success"
                        elif code_str == "4.01":
                            return False, f"CoAP 4.01 Unauthorized (Invalid Token)"
                        return False, f"CoAP Code {code_str}"
                return True, "CoAP NON sent"
            finally:
                sock.close()

        try:
            success, msg = await asyncio.to_thread(_sync_udp_send)
            return success, msg
        except socket.timeout:
            err_msg = f"CoAP UDP timeout ({self.timeout}s) to {host}:{port}"
            logger.warning(err_msg)
            return False, err_msg
        except Exception as e:
            err_msg = f"CoAP error to {host}:{port}: {e}"
            logger.error(err_msg)
            return False, str(e)

    async def test_connectivity(
        self,
        host: str,
        port: int,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a diagnostic CoAP ping against ThingsBoard.

        Sends a Confirmable (CON) probe datagram and awaits an acknowledgement
        to evaluate port reachability, token authorization, and latency.

        Args:
            host: Target server host.
            port: Target CoAP port (usually 5683).
            token: Optional device access token.

        Returns:
            Dict[str, Any]: Comprehensive diagnostic report.
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
            recommendations.append(f"The ThingsBoard server acknowledged the CoAP packet ({message}).")
        elif "4.01" in message:
            recommendations.append("ThingsBoard CoAP service is running and responded, but Token was rejected (4.01 Unauthorized).")
        elif "Timeout" in message:
            recommendations.append("CoAP UDP port 5683 timed out. Verify that the ThingsBoard CoAP transport service is enabled.")
            recommendations.append("Note: If the server is behind Cloudflare or a standard HTTP CDN, UDP packets are usually filtered.")
        else:
            recommendations.append(f"CoAP Error: {message}")

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
