# 💻 Exécuter IoT Data Simulator sans droits Administrateur (Windows & Linux)

Ce guide explique comment lancer **IoT Data Simulator** sur un PC d'entreprise verrouillé (**0 droit administrateur**, **0 Docker**, **0 installation système**), aussi bien sous **Windows 10/11** que sous **Linux**.

---

## 🛡️ Pourquoi ça fonctionne sans droits Admin ?

- **Écoute stricte sur `127.0.0.1`** : le simulateur n'ouvre aucun port entrant sur le réseau local, ce qui **évite complètement la fenêtre UAC Administrateur du Pare-feu Windows**.
- **Port automatique** : démarre sur `8032` et bascule automatiquement sur le premier port libre (`8033`, `8034`...) si `8032` est déjà occupé.
- **Ouverture automatique du navigateur** dès que le serveur local est prêt.
- **Stockage 100 % portable (`data/`)** : vos équipements, comptes et presets personnalisés sont enregistrés dans le dossier `data/` à côté de l'exécutable *(prêt pour clé USB)*. Si le dossier est en lecture seule, le simulateur bascule automatiquement vers votre profil utilisateur (`%LOCALAPPDATA%\IoT-Data-Simulator\data` sous Windows ou `~/.local/share/iot-data-simulator/data` sous Linux).
- **100 % compatible Pare-feu d'entreprise** : grâce à l'option **« Forcer HTTP REST »**, tous les 35 cas d'usage communiquent avec ThingsBoard via **HTTPS (port 443)** sans nécessiter l'ouverture du port MQTT `1883` ni d'un broker Mosquitto local.

---

## Option A (Recommandée) — Binaire Portable Autonome (.ZIP)

Idéale pour les **commerciaux et avant-ventes** : **zéro Python requis**, **fonctionne hors-ligne**.

1. Rendez-vous dans l'onglet **Releases** du dépôt GitHub et téléchargez l'archive correspondant à votre PC :
   - **Windows** : `IoT-Data-Simulator-Windows-x64.zip`
   - **Linux** : `IoT-Data-Simulator-Linux-x64.zip`
2. Décompressez le dossier dans un répertoire utilisateur *(ex. `C:\Users\<vous>\Documents\IoT-Data-Simulator\` ou sur une clé USB)*.
3. Lancez l'exécutable :
   - **Windows** : double-cliquez sur **`IoT-Data-Simulator.exe`**
   - **Linux** : ouvrez un terminal dans le dossier et lancez `./IoT-Data-Simulator`
4. Votre navigateur s'ouvre automatiquement sur `http://127.0.0.1:8032` *(identifiants par défaut : `admin` / `admin123`)*.
5. Pour arrêter le simulateur, fermez simplement la fenêtre console (ou `Ctrl+C`).

> **Astuce IT** : Les binaires sont générés automatiquement par GitHub Actions (`.github/workflows/build-portable.yml`) à chaque tag `v*` (ou à la demande via *Actions → Run workflow*).

---

## Option B (Plan B si l'antivirus/EDR bloque les `.exe` non signés) — Lanceur Script Portable

Si la politique sécurité de votre PC bloque l'exécution de fichiers `.exe` téléchargés, utilisez les scripts transparents fournis dans le dossier [`portable/`](../../portable/) :

### Sous Windows (sans droits admin)
1. Téléchargez le dépôt (ZIP ou `git clone`) dans `Documents\iot-data-simulator`.
2. Double-cliquez sur **`portable\start_windows.bat`**.
3. Le script détecte automatiquement `uv` ou `python` en espace utilisateur, crée un environnement isolé dans `%LOCALAPPDATA%\IoT-Data-Simulator\venv` (1ère exécution uniquement) et démarre le simulateur.

### Sous Linux (sans droits admin)
```bash
chmod +x portable/start_linux.sh
./portable/start_linux.sh
```

---

## ⚙️ Options avancées en ligne de commande

Le lanceur [`launcher.py`](../../launcher.py) accepte les options suivantes :

```bash
# Choisir un port de départ personnalisé
python3 launcher.py --port 8080

# Lancer sans ouvrir automatiquement le navigateur
python3 launcher.py --no-browser

# Forcer un dossier de données spécifique
IOT_SIM_DATA_DIR=/chemin/perso python3 launcher.py
```
