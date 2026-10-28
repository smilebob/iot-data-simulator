"""
Cryptographic Security, Password Hashing, and JWT Session Management.

Implements CIS Docker Benchmark and OWASP-compliant security mechanisms:
- Scrypt password hashing (RFC 7914) with constant-time equality checks.
- Native HMAC-SHA256 JSON Web Token (JWT RFC 7519) generation and decoding without external dependencies.
- Persistent file-backed 256-bit signing key with restricted Unix file permissions (0600).
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import stat
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("iot_sim.security")

# Scrypt configuration parameters conforming to OWASP recommendations:
# N=16384 (CPU/memory cost 2^14), r=8 (RAM block size 1024 bytes), p=1 (parallelization)
SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1


def _b64url_encode(data: bytes) -> str:
    """Encodes binary bytes to base64url string without trailing padding (RFC 7515).

    Args:
        data: Raw binary byte sequence.

    Returns:
        str: URL-safe base64 encoded ASCII string.
    """
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    """Decodes a base64url string after restoring standard '=' padding.

    Args:
        s: Base64url encoded ASCII string.

    Returns:
        bytes: Decoded raw binary byte sequence.
    """
    padding = "=" * (4 - (len(s) % 4)) if (len(s) % 4) != 0 else ""
    return base64.urlsafe_b64decode(s + padding)


def hash_password(password: str) -> str:
    """Computes a salted Scrypt cryptographic password hash.

    Generates a cryptographically random 16-byte salt and derives a 64-byte key
    using RFC 7914 Scrypt.

    Args:
        password: Plain-text password to hash.

    Returns:
        str: Serialized hash formatted as '$scrypt$N$r$p$salt_b64$key_b64'.

    Example:
        >>> h = hash_password("SuperSecret123!")
        >>> h.startswith("$scrypt$16384$8$1$")
        True
    """
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P
    )
    return f"$scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64url_encode(salt)}${_b64url_encode(key)}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a stored Scrypt hash in constant time.

    Protects against timing side-channel attacks using `secrets.compare_digest`.

    Args:
        plain_password: Input password provided by user.
        hashed_password: Stored Scrypt hash string from user repository.

    Returns:
        bool: True if password matches hash, False otherwise.
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 7 or parts[1] != "scrypt":
            return False

        n = int(parts[2])
        r = int(parts[3])
        p = int(parts[4])
        salt = _b64url_decode(parts[5])
        expected_key = _b64url_decode(parts[6])

        computed_key = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p
        )
        return secrets.compare_digest(computed_key, expected_key)
    except Exception as e:
        logger.warning(f"Error during password verification: {e}")
        return False


def get_or_create_jwt_secret(secret_file_path: str = "data/.jwt_secret") -> str:
    """Retrieves or provisions the 256-bit cryptographic HMAC signing key.

    Priority resolution:
    1. Environment variable `JWT_SECRET_KEY` (if set and >= 32 characters).
    2. File on persistent volume with strict POSIX permissions `0600` (read/write user only).
    3. Freshly generated 256-bit hex token securely persisted to disk.

    Args:
        secret_file_path: Path where the secret file is stored.

    Returns:
        str: Hex-encoded 256-bit secret signing key.
    """
    # 1. Check environment variable override
    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret and len(env_secret.strip()) >= 32:
        return env_secret.strip()

    # 2. Check existing file on disk
    if os.path.exists(secret_file_path):
        try:
            with open(secret_file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if len(content) >= 32:
                    return content
        except Exception as e:
            logger.warning(f"Unable to read existing JWT secret file: {e}")

    # 3. Generate a new cryptographically secure 256-bit random key
    new_secret = secrets.token_hex(32)
    try:
        os.makedirs(os.path.dirname(secret_file_path), exist_ok=True)
        # Create file with strict 0600 permissions (owner read/write only, CIS benchmark rule)
        fd = os.open(
            secret_file_path,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        with open(fd, "w", encoding="utf-8") as f:
            f.write(new_secret)
        logger.info(f"Generated new JWT signing secret persisted to {secret_file_path} (mode 0600)")
    except Exception as e:
        logger.warning(f"Failed to persist JWT secret to disk: {e}")

    return new_secret


# Initialize application-wide JWT signing secret at import
JWT_SECRET = get_or_create_jwt_secret()


def create_jwt_token(
    payload: Dict[str, Any],
    expires_in_seconds: int = 28800,  # 8 hours default session expiration
    secret_key: Optional[str] = None,
) -> str:
    """Creates a signed HMAC-SHA256 JSON Web Token (JWT RFC 7519).

    Args:
        payload: Dictionary containing user claims ('sub', 'role', 'name').
        expires_in_seconds: Lifetime duration of the token in seconds.
        secret_key: Optional custom HMAC signing key (defaults to global JWT_SECRET).

    Returns:
        str: Compact three-part JWT token formatted as 'header.payload.signature'.
    """
    key = secret_key or JWT_SECRET
    now = int(time.time())
    full_payload = {
        **payload,
        "iat": now,
        "exp": now + expires_in_seconds,
    }

    header = {"alg": "HS256", "typ": "JWT"}
    h_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_b64 = _b64url_encode(json.dumps(full_payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{h_b64}.{p_b64}".encode("utf-8")

    sig = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return f"{h_b64}.{p_b64}.{sig_b64}"


def decode_jwt_token(
    token: str,
    secret_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Validates the cryptographic signature and expiration of a JWT token.

    Args:
        token: Compact three-part JWT string to verify.
        secret_key: Optional custom HMAC key (defaults to global JWT_SECRET).

    Returns:
        Optional[Dict[str, Any]]: Decoded payload claims dictionary if valid and unexpired;
            None if signature is invalid, token is malformed, or expired.
    """
    key = secret_key or JWT_SECRET
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        h_b64, p_b64, sig_b64 = parts
        signing_input = f"{h_b64}.{p_b64}".encode("utf-8")
        expected_sig = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        # Constant-time comparison prevents timing analysis
        if not secrets.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64url_decode(p_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Enforce temporal expiration timestamp claim
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None
