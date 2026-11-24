"""
Unit Tests for Lot 2: Site Blueprints & Live Storyboards.
"""

import asyncio
import os
import tempfile
from app.core.site_blueprints import (
    InstantiateSiteRequest,
    get_site_blueprints,
    instantiate_site_blueprint,
    generate_site_hypervision_dashboard,
)
from app.core.storyboard_engine import get_storyboards, StoryboardManager
from app.models.device import TransportProtocol
from app.storage.repository import StorageRepository


def test_site_blueprints_and_instantiation():
    """Validates 1-click multi-equipment site instantiation in an isolated storage file."""
    bps = get_site_blueprints()
    assert len(bps) == 3
    bp_ids = {b.id for b in bps}
    assert {"site_tertiaire_bacs", "site_usine_decarbonee", "site_microgrid_energie"}.issubset(bp_ids)

    tmp_dir = tempfile.mkdtemp()
    db_file = os.path.join(tmp_dir, "site_test_db.json")
    repo = StorageRepository(file_path=db_file)

    res = instantiate_site_blueprint(
        InstantiateSiteRequest(
            blueprint_id="site_tertiaire_bacs",
            site_prefix="client_alpha",
            clear_existing=True,
        ),
        repo=repo,
    )
    assert res["status"] == "instantiated"
    assert res["devices_created"] == 5
    assert res["total_variables"] > 20

    devices = repo.get_devices()
    assert len(devices) == 5
    assert any(d.id == "client_alpha_gtb" for d in devices)

    # Verify force_http_rest=True forces HTTP REST transport on all site devices
    res_http = instantiate_site_blueprint(
        InstantiateSiteRequest(
            blueprint_id="site_usine_decarbonee",
            site_prefix="usine_rest",
            force_http_rest=True,
            clear_existing=True,
        ),
        repo=repo,
    )
    assert res_http["devices_created"] == 4
    http_devices = repo.get_devices()
    assert len(http_devices) == 4
    assert all(d.protocol == TransportProtocol.HTTP for d in http_devices)


def test_site_hypervision_dashboard_generation():
    """Validates Master Hypervision Site ThingsBoard dashboard structure."""
    dash = generate_site_hypervision_dashboard("site_microgrid_energie", site_prefix="mg_test")
    assert "Hypervision Site" in dash["title"]
    cfg = dash["configuration"]
    assert len(cfg["entityAliases"]) == 4
    # 1 header card + 4 equipment timeseries cards
    assert len(cfg["widgets"]) == 5


def test_storyboards_and_manager_lifecycle():
    """Validates live storyboard definitions and start/stop async execution."""
    boards = get_storyboards()
    assert len(boards) >= 2
    assert any(b.id == "demo_bacs_derive" for b in boards)

    async def _run():
        mgr = StoryboardManager()
        st = await mgr.start("demo_bacs_derive")
        assert st["running"] is True
        assert st["storyboard_id"] == "demo_bacs_derive"
        await asyncio.sleep(0.05)
        st2 = await mgr.stop()
        assert st2["running"] is False

    asyncio.run(_run())
