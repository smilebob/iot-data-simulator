#!/usr/bin/env python3
"""
IoT Data Simulator — Portable Zero-Admin Launcher (Windows & Linux).

Designed for non-administrator corporate workstations:
- Binds strictly to 127.0.0.1 (avoids Windows Defender Firewall admin UAC prompts).
- Auto-detects a free local TCP port starting at 8032.
- Resolves persistent `data/` next to the executable (USB-portable) with automatic
  fallback to %LOCALAPPDATA%/IoT-Data-Simulator/data (Windows) or
  ~/.local/share/iot-data-simulator/data (Linux/macOS) if the folder is read-only.
- Automatically opens the Web GUI in the user's default browser once ready.
"""

from __future__ import annotations

import argparse
import os
import socket
import threading
import time
import webbrowser

# Mark portable mode BEFORE importing app.main so singletons resolve portable data/
os.environ.setdefault("IOT_SIM_PORTABLE", "1")

from app.core.paths import resolve_data_dir  # noqa: E402


def find_free_port(host: str = "127.0.0.1", preferred_port: int = 8032, max_tries: int = 20) -> int:
    """Finds the first available TCP port on `host` starting at `preferred_port`."""
    for candidate in range(preferred_port, preferred_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, candidate))
                return candidate
            except OSError:
                continue
    # Fallback to OS-assigned ephemeral free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _open_browser_when_ready(host: str, port: int, timeout: float = 15.0) -> None:
    """Polls the local TCP socket and opens the default browser as soon as Uvicorn is listening."""
    deadline = time.time() + timeout
    url = f"http://{host}:{port}"
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.4):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.25)


def main() -> None:
    parser = argparse.ArgumentParser(description="IoT Data Simulator (Mode Portable Sans Droits Admin)")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute locale (défaut: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8032, help="Port de départ (défaut: 8032, auto-incrémenté si occupé)")
    parser.add_argument("--no-browser", action="store_true", help="Ne pas ouvrir automatiquement le navigateur")
    args = parser.parse_args()

    data_dir = resolve_data_dir(portable=True)
    os.environ["IOT_SIM_DATA_DIR"] = str(data_dir)
    os.environ.setdefault("CUSTOM_PRESETS_FILE", str(data_dir / "custom_presets.json"))

    port = find_free_port(args.host, args.port)
    url = f"http://{args.host}:{port}"

    # Late imports ensure FastAPI singletons pick up IOT_SIM_DATA_DIR
    import uvicorn  # noqa: E402
    from app.main import APP_VERSION, BUILD_DATE, app  # noqa: E402

    print("=" * 64)
    print(f"  IoT Data Simulator v{APP_VERSION} (build {BUILD_DATE}) — Mode Portable")
    print("=" * 64)
    print(f"  Interface Web : {url}")
    print(f"  Dossier Data  : {data_dir}")
    print("  Identifiants  : admin / admin123 (modifiable dans l'interface)")
    print("  Mode Réseau   : 127.0.0.1 uniquement (aucun droit admin requis)")
    print("  Arrêt         : Fermez cette fenêtre ou appuyez sur Ctrl+C")
    print("=" * 64)

    if not args.no_browser:
        threading.Thread(target=_open_browser_when_ready, args=(args.host, port), daemon=True).start()

    uvicorn.run(app, host=args.host, port=port, log_level="info")


if __name__ == "__main__":
    main()
