"""
Cross-platform path resolution for standard, Docker, and portable (PyInstaller) runtimes.

Supports zero-admin execution on Windows and Linux:
- Static web assets are resolved from PyInstaller's `sys._MEIPASS` when frozen,
  or from `app/static` in normal source/Docker execution.
- Persistent `data/` directory is resolved as:
  1. Explicit `IOT_SIM_DATA_DIR` environment variable if set.
  2. When running in portable/frozen mode (`sys.frozen` or `IOT_SIM_PORTABLE=1`):
     `<executable_or_project_dir>/data` if writable (USB-ready), with automatic
     fallback to `%LOCALAPPDATA%/IoT-Data-Simulator/data` (Windows) or
     `~/.local/share/iot-data-simulator/data` (Linux/macOS) if read-only.
  3. Standard relative `data` directory in normal/Docker execution.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Returns True when running inside a PyInstaller frozen bundle."""
    return bool(getattr(sys, "frozen", False))


def get_base_dir() -> Path:
    """Returns the runtime root directory containing application resources."""
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent


def get_static_dir() -> Path:
    """Returns the absolute path to the frontend static assets directory."""
    return get_base_dir() / "app" / "static"


def _is_dir_writable(path: Path) -> bool:
    """Tests whether a directory can be created and written to by the current non-admin user."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def get_user_fallback_data_dir() -> Path:
    """Returns the OS-standard per-user writable data directory (no admin required)."""
    if sys.platform.startswith("win"):
        local_app_data = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local_app_data) / "IoT-Data-Simulator" / "data"
    xdg_data = os.getenv("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(xdg_data) / "iot-data-simulator" / "data"


def resolve_data_dir(portable: bool = False) -> Path:
    """Resolves the writable persistent data directory with automatic non-admin fallback."""
    explicit = os.getenv("IOT_SIM_DATA_DIR")
    if explicit:
        target = Path(explicit)
        target.mkdir(parents=True, exist_ok=True)
        return target

    if portable or is_frozen() or os.getenv("IOT_SIM_PORTABLE") == "1":
        anchor = Path(sys.executable).resolve().parent if is_frozen() else Path(__file__).resolve().parent.parent.parent
        candidate = anchor / "data"
        if _is_dir_writable(candidate):
            return candidate
        fallback = get_user_fallback_data_dir()
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    return Path("data")
