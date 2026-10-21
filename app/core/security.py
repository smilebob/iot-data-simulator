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

# Configuration de l'algorithme Scrypt conforme OWASP & CIS Benchmark
SCRYPT_N = 16384  # Coût CPU/mémoire (2^14)
SCRYPT_R = 8      # Taille de bloc
SCRYPT_P = 1      # Parallélisation

def _b64url_encode(data: bytes) -> str:
    """Encode en base64url sans padding pour conformité RFC 7515."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64url_decode(s: str) -> bytes:
    """Décode du base64url en restaurant le padding requis."""
    padding = "=" * (4 - (len(s) % 4)) if (len(s) % 4) != 0 else ""
    return base64.urlsafe_b64decode(s + padding)

def hash_password(password: str) -> str:
    """
    Calcule une empreinte Scrypt renforcée avec sel cryptographique de 16 octets.
    Format de stockage : $scrypt$N$r$p$sel_b64$cle_b64
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
    """
    Vérifie un mot de passe contre une empreinte Scrypt en temps constant (anti-timing attack).
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
        logger.warning(f"Erreur lors de la vérification du mot de passe: {e}")
        return False

def get_or_create_jwt_secret(secret_file_path: str = "data/.jwt_secret") -> str:
    """
    Récupère la clé secrète de signature JWT depuis l'environnement
    ou depuis un fichier protégé (chmod 0600) dans le volume persistant.
    """
    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret and len(env_secret.strip()) >= 32:
        return env_secret.strip()

    if os.path.exists(secret_file_path):
        try:
            with open(secret_file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if len(content) >= 32:
                    return content
        except Exception as e:
            logger.warning(f"Impossible de lire le secret JWT existant: {e}")

    # Génération d'une nouvelle clé cryptographiquement sécurisée (256 bits)
    new_secret = secrets.token_hex(32)
    try:
        os.makedirs(os.path.dirname(secret_file_path), exist_ok=True)
        # Écriture avec permissions restreintes 0600 (lecture/écriture propriétaire seul)
        fd = os.open(
            secret_file_path,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        with open(fd, "w", encoding="utf-8") as f:
            f.write(new_secret)
        logger.info(f"Clé de signature JWT générée et sécurisée dans {secret_file_path} (0600)")
    except Exception as e:
        logger.warning(f"Impossible de persister le secret JWT sur disque: {e}")

    return new_secret

# Clé de signature initialisée pour le processus
JWT_SECRET = get_or_create_jwt_secret()

def create_jwt_token(
    payload: Dict[str, Any],
    expires_in_seconds: int = 28800,  # 8 heures par défaut
    secret_key: Optional[str] = None,
) -> str:
    """
    Crée un jeton JWT HMAC-SHA256 (RFC 7519) conforme et autonome.
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
    """
    Valide la signature et l'expiration d'un jeton JWT.
    Retourne le dictionnaire de payload ou None en cas d'altération ou d'expiration.
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

        if not secrets.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64url_decode(p_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Vérification expiration
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None
