#!/usr/bin/env python3
"""
Script de déploiement direct d'un cas d'usage métier (Preset Package)
dans une instance active d'IoT Data Simulator via son API REST.
Exécutable avec Python 3 standard (zéro dépendance externe).
"""

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Optional, Dict, Any


def http_json_request(
    url: str,
    payload: Dict[str, Any],
    token: Optional[str] = None,
    timeout: int = 15,
) -> tuple[int, Dict[str, Any]]:
    """Envoie une requête POST JSON et retourne (code_http, reponse_json)."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(body) if body else {"detail": str(e)}
        except Exception:
            err_json = {"detail": body or str(e)}
        return e.code, err_json
    except urllib.error.URLError as e:
        raise ConnectionError(f"Impossible de joindre '{url}' : {e.reason}")


def authenticate(base_url: str, username: str, password: str) -> str:
    """Authentifie l'utilisateur sur /api/auth/login et retourne le token JWT."""
    login_url = f"{base_url.rstrip('/')}/api/auth/login"
    code, resp = http_json_request(
        login_url,
        {"username": username, "password": password},
    )
    if code == 200 and "access_token" in resp:
        return resp["access_token"]
    detail = resp.get("detail", f"HTTP {code}")
    raise RuntimeError(f"Échec de l'authentification : {detail}")


def main():
    parser = argparse.ArgumentParser(
        description="Déploie un package de cas d'usage dans l'IoT Data Simulator."
    )
    parser.add_argument(
        "--file", "-f", required=True, help="Chemin du fichier JSON du preset/package à importer"
    )
    parser.add_argument(
        "--url",
        "-u",
        default="http://localhost:8032",
        help="URL de l'instance IoT Data Simulator (défaut: http://localhost:8032)",
    )
    parser.add_argument("--username", help="Nom d'utilisateur (si RBAC actif)")
    parser.add_argument("--password", help="Mot de passe (si RBAC actif)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ Erreur : Fichier introuvable '{args.file}'", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"❌ Erreur de lecture JSON '{args.file}' : {e}", file=sys.stderr)
        sys.exit(1)

    base_url = args.url.rstrip("/")
    import_url = f"{base_url}/api/presets/import"
    token = None

    # Si identifiants fournis directement, s'authentifier d'abord
    if args.username and args.password:
        try:
            token = authenticate(base_url, args.username, args.password)
        except Exception as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

    try:
        code, resp = http_json_request(import_url, payload, token=token)

        # Si 401 Unauthorized et terminal interactif, demander les identifiants à la volée
        if code == 401 and sys.stdin.isatty() and not token:
            print("🔒 Authentification requise sur cette instance du simulateur.")
            user = args.username or input("Nom d'utilisateur : ").strip()
            pwd = args.password or getpass.getpass("Mot de passe : ")
            token = authenticate(base_url, user, pwd)
            code, resp = http_json_request(import_url, payload, token=token)

        if 200 <= code < 300:
            count = resp.get("imported_count", 1)
            ids = resp.get("imported_ids", [])
            print(f"✅ Succès : {count} modèle(s) importé(s) sur {base_url} ({', '.join(ids)}) !")
            sys.exit(0)
        else:
            detail = resp.get("detail", resp)
            print(f"❌ Échec de l'importation (HTTP {code}) : {detail}", file=sys.stderr)
            sys.exit(1)

    except ConnectionError as ce:
        print(f"❌ {ce}", file=sys.stderr)
        sys.exit(1)
    except Exception as ex:
        print(f"❌ Erreur inattendue : {ex}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
