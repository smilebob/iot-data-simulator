"""
Unit tests for portable zero-admin path resolution and local launcher helpers.
"""

import os
import socket
from pathlib import Path
from app.core.paths import get_static_dir, resolve_data_dir, get_user_fallback_data_dir
from launcher import find_free_port


def test_get_static_dir_points_to_index_html():
    static_dir = get_static_dir()
    assert (static_dir / "index.html").is_file()


def test_resolve_data_dir_explicit_env_override(tmp_path, monkeypatch):
    custom_dir = tmp_path / "portable_data"
    monkeypatch.setenv("IOT_SIM_DATA_DIR", str(custom_dir))
    resolved = resolve_data_dir(portable=True)
    assert resolved == custom_dir
    assert custom_dir.is_dir()


def test_resolve_data_dir_readonly_falls_back_to_user_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("IOT_SIM_DATA_DIR", raising=False)
    monkeypatch.setattr("app.core.paths._is_dir_writable", lambda _p: False)
    resolved = resolve_data_dir(portable=True)
    assert resolved == get_user_fallback_data_dir()


def test_find_free_port_skips_occupied_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
        blocker.bind(("127.0.0.1", 0))
        busy_port = blocker.getsockname()[1]
        blocker.listen(1)

        chosen = find_free_port("127.0.0.1", preferred_port=busy_port, max_tries=10)
        assert chosen != busy_port
        assert chosen > 0
