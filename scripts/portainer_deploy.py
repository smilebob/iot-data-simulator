#!/usr/bin/env python3
"""
IoT Data Simulator - Portainer Automated Deployment CLI
======================================================
Script d'automatisation pour déclencher le déploiement ou la mise à jour
de la stack IoT Data Simulator sur une instance Portainer (locale ou distante).

Modes supportés :
1. Déclenchement par Webhook Portainer (local ou public) :
   python3 scripts/portainer_deploy.py --webhook "http://192.168.1.50:9000/api/stacks/webhooks/xxxx"

2. Déclenchement via l'API REST Portainer (avec clé d'API) :
   python3 scripts/portainer_deploy.py --url "http://192.168.1.50:9000" --api-key "ptr_xxx" --stack "iot-simulator" --pull

3. Détection automatique via fichier de configuration (.env.portainer) :
   python3 scripts/portainer_deploy.py
"""

import argparse
import json
import os
import sys
import ssl
from pathlib import Path
from typing import Dict, Any, Optional
import urllib.request
import urllib.error


def load_env_file(env_path: Path) -> Dict[str, str]:
    """Charge un fichier .env simple sans dépendance externe."""
    env_vars = {}
    if not env_path.exists():
        return env_vars
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    env_vars[key] = val
    except Exception as e:
        print(f"⚠️ Avertissement : impossible de lire {env_path}: {e}")
    return env_vars


def make_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    insecure: bool = False,
    timeout: int = 30
) -> Dict[str, Any]:
    """Effectue une requête HTTP(S) avec la bibliothèque standard."""
    req_headers = headers.copy() if headers else {}
    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        if "Content-Type" not in req_headers:
            req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

    context = None
    if insecure and url.startswith("https://"):
        context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
            status_code = response.getcode()
            raw_body = response.read().decode("utf-8", errors="replace")
            parsed_data = None
            if raw_body:
                try:
                    parsed_data = json.loads(raw_body)
                except json.JSONDecodeError:
                    parsed_data = raw_body
            return {
                "success": 200 <= status_code < 300,
                "status_code": status_code,
                "data": parsed_data,
                "raw": raw_body,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        return {
            "success": False,
            "status_code": e.code,
            "data": err_body,
            "raw": err_body,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "data": None,
            "raw": "",
            "error": str(e)
        }


def trigger_webhook(webhook_url: str, insecure: bool = False) -> bool:
    """Déclenche la mise à jour automatique via l'URL de webhook Portainer."""
    print(f"🚀 Déclenchement du Webhook Portainer : {webhook_url}")
    res = make_request(webhook_url, method="POST", insecure=insecure)
    if res["success"]:
        print(f"✅ Succès ! Portainer a accusé réception du signal (Code HTTP: {res['status_code']}).")
        print("📦 Portainer procède au pull de l'image GHCR et au redémarrage de la stack.")
        return True
    else:
        print(f"❌ Échec de l'appel Webhook (Code HTTP: {res['status_code']})")
        if res.get("error"):
            print(f"   Détail : {res['error']}")
        if res.get("data"):
            print(f"   Réponse : {res['data']}")
        return False


def redeploy_via_api(
    base_url: str,
    api_key: str,
    stack_name: str,
    endpoint_id: Optional[int] = None,
    pull_image: bool = True,
    insecure: bool = False
) -> bool:
    """Redéploie la stack via l'API REST officielle Portainer."""
    base_url = base_url.rstrip("/")
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }

    print(f"🔍 Connexion à l'API Portainer sur {base_url}...")

    # 1. Obtenir les endpoints si endpoint_id non précisé
    if endpoint_id is None:
        print("📋 Recherche de l'environnement Docker (Endpoint)...")
        res_ep = make_request(f"{base_url}/api/endpoints", headers=headers, insecure=insecure)
        if not res_ep["success"]:
            print(f"❌ Impossible de lister les endpoints Portainer (Code: {res_ep['status_code']})")
            print(f"   Erreur: {res_ep.get('error') or res_ep.get('data')}")
            return False
        
        endpoints = res_ep["data"]
        if not isinstance(endpoints, list) or len(endpoints) == 0:
            print("❌ Aucun environnement Docker trouvé dans cette instance Portainer.")
            return False
        
        endpoint_id = endpoints[0]["Id"]
        print(f"ℹ️ Environnement sélectionné par défaut : ID {endpoint_id} ({endpoints[0].get('Name', 'Local')})")

    # 2. Rechercher la stack par son nom
    print(f"🔎 Recherche de la stack '{stack_name}' dans l'environnement {endpoint_id}...")
    res_stacks = make_request(f"{base_url}/api/stacks", headers=headers, insecure=insecure)
    if not res_stacks["success"]:
        print(f"❌ Impossible de lister les stacks (Code: {res_stacks['status_code']})")
        return False

    target_stack = None
    for st in res_stacks["data"]:
        if st.get("Name") == stack_name:
            target_stack = st
            break

    if not target_stack:
        print(f"❌ Stack '{stack_name}' introuvable dans Portainer.")
        print("   Stacks disponibles : " + ", ".join([s.get("Name", "sans nom") for s in res_stacks["data"]]))
        return False

    stack_id = target_stack["Id"]
    stack_type = target_stack.get("Type")
    is_git = bool(target_stack.get("GitConfig"))
    print(f"✅ Stack trouvée : ID {stack_id} (Type: {stack_type}, Git Stack: {is_git})")

    # 3. Déclencher le redéploiement
    if is_git:
        # Stack déployée depuis Git : utiliser /git/redeploy
        redeploy_url = f"{base_url}/api/stacks/{stack_id}/git/redeploy?endpointId={endpoint_id}"
        payload = {
            "prune": True,
            "pullImage": pull_image
        }
        print(f"🚀 Déclenchement du redéploiement Git (pullImage={pull_image}, prune=True)...")
        res_dep = make_request(redeploy_url, method="PUT", headers=headers, data=payload, insecure=insecure, timeout=120)
    else:
        # Stack standard : update stack
        redeploy_url = f"{base_url}/api/stacks/{stack_id}?endpointId={endpoint_id}"
        # Conserver le contenu actuel de stack_file si disponible
        payload = {
            "id": stack_id,
            "prune": True,
            "pullImage": pull_image
        }
        print("🚀 Mise à jour et redéploiement de la stack...")
        res_dep = make_request(redeploy_url, method="PUT", headers=headers, data=payload, insecure=insecure, timeout=120)

    if res_dep["success"]:
        print("✅ Déploiement Portainer terminé avec succès !")
        print(f"ℹ️ La stack '{stack_name}' a été actualisée avec la dernière image.")
        return True
    else:
        print(f"❌ Erreur lors du redéploiement (Code HTTP: {res_dep['status_code']})")
        print(f"   Détails : {res_dep.get('error') or res_dep.get('data')}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Déploiement et mise à jour automatisés de la stack IoT Data Simulator sur Portainer."
    )
    parser.add_argument("--webhook", help="URL de Webhook Portainer générée dans la stack")
    parser.add_argument("--url", help="URL de base de Portainer (ex: http://192.168.1.50:9000 ou https://portainer.local:9443)")
    parser.add_argument("--api-key", help="Clé d'API Portainer (X-API-Key générée dans Mon Compte > Access Tokens)")
    parser.add_argument("--stack", default="iot-simulator", help="Nom de la stack Portainer (défaut: iot-simulator)")
    parser.add_argument("--endpoint-id", type=int, help="ID de l'environnement Docker dans Portainer (défaut: automatique)")
    parser.add_argument("--no-pull", action="store_true", help="Ne pas forcer le pull de la dernière image Docker")
    parser.add_argument("--insecure", "-k", action="store_true", help="Ignorer les erreurs de certificat SSL/TLS auto-signé")
    parser.add_argument("--env-file", default=".env.portainer", help="Fichier de configuration local (défaut: .env.portainer)")

    args = parser.parse_args()

    # Charger le fichier .env.portainer si présent
    project_root = Path(__file__).resolve().parent.parent
    env_file_path = project_root / args.env_file
    file_vars = load_env_file(env_file_path)

    webhook_url = args.webhook or file_vars.get("PORTAINER_WEBHOOK_URL") or os.environ.get("PORTAINER_WEBHOOK_URL")
    portainer_url = args.url or file_vars.get("PORTAINER_URL") or os.environ.get("PORTAINER_URL")
    api_key = args.api_key or file_vars.get("PORTAINER_API_KEY") or os.environ.get("PORTAINER_API_KEY")
    stack_name = args.stack or file_vars.get("PORTAINER_STACK_NAME") or os.environ.get("PORTAINER_STACK_NAME") or "iot-simulator"
    endpoint_id = args.endpoint_id
    if endpoint_id is None and "PORTAINER_ENDPOINT_ID" in file_vars:
        try:
            endpoint_id = int(file_vars["PORTAINER_ENDPOINT_ID"])
        except ValueError:
            pass

    # Option 1 : Déclenchement via Webhook
    if webhook_url:
        success = trigger_webhook(webhook_url, insecure=args.insecure)
        sys.exit(0 if success else 1)

    # Option 2 : Déclenchement via API REST Portainer
    if portainer_url and api_key:
        success = redeploy_via_api(
            base_url=portainer_url,
            api_key=api_key,
            stack_name=stack_name,
            endpoint_id=endpoint_id,
            pull_image=not args.no_pull,
            insecure=args.insecure
        )
        sys.exit(0 if success else 1)

    # Si aucun paramètre n'a été fourni
    print("❌ Aucun paramètre de connexion Portainer détecté.")
    print("\n💡 Pour automatiser le déploiement sur votre réseau local privé :")
    print("   1. Option A (Webhook local) :")
    print("      python3 scripts/portainer_deploy.py --webhook 'http://<IP_LOCALE>:9000/api/stacks/webhooks/<TOKEN>'")
    print("\n   2. Option B (Clé d'API Portainer) :")
    print("      python3 scripts/portainer_deploy.py --url 'http://<IP_LOCALE>:9000' --api-key 'ptr_xxx'")
    print("\n   3. Option C (Fichier de configuration) :")
    print("      Créez un fichier '.env.portainer' à partir du template '.env.portainer.example'.")
    print("\n   Consultez 'Documentation/devops/portainer_deployment.md' pour les instructions complètes.")
    sys.exit(1)


if __name__ == "__main__":
    main()
