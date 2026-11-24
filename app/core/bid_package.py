"""
1-Click Pre-Sales Bid Pack (.ZIP) Exporter.

Bundles all technical deliverables for an RFP / client proposal into a single ZIP archive:
1. 01_IO_List_Points.csv (French Excel UTF-8 BOM + Modbus TCP register map)
2. 02_Dossier_Architecture_IoT.md (Mermaid architecture + ThingsBoard sourced sizing)
3. 03_ThingsBoard_IoT_Gateway_modbus.json (Ready-to-import Modbus TCP Gateway config)
4. 04_Widgets_ISA101_Bundle_70.json (70 ANSI/ISA-101 modular widgets for ThingsBoard 4.3)
5. dashboards/<device_id>_dashboard.json (All active device ThingsBoard 4.3 dashboards)
6. Catalogue_Commercial_Cas_Usage.pdf (Included if available on disk)
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import List

from app.core.bid_deliverables import generate_architecture_dossier_md, generate_io_list_csv
from app.core.dashboard_generator import generate_thingsboard_dashboard
from app.core.paths import get_base_dir
from app.core.sizing_calculator import SizingResult, calculate_sizing_from_active_devices
from app.core.svg_components import generate_thingsboard_widget_bundle
from app.models.device import DeviceConfig
from app.models.variable import VariableConfig
from app.transports.modbus_server import generate_tb_gateway_modbus_config


def build_bid_pack_zip(
    devices: List[DeviceConfig],
    variables: List[VariableConfig],
    sizing: SizingResult | None = None,
) -> bytes:
    """Builds a complete in-memory ZIP archive of all pre-sales & engineering deliverables."""
    effective_sizing = sizing or calculate_sizing_from_active_devices(devices, variables)
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. IO List CSV
        io_csv = generate_io_list_csv(devices, variables)
        zf.writestr("01_IO_List_Points.csv", io_csv.encode("utf-8"))

        # 2. Technical Architecture Dossier Markdown
        dossier_md = generate_architecture_dossier_md(devices, variables, effective_sizing)
        zf.writestr("02_Dossier_Architecture_IoT.md", dossier_md.encode("utf-8"))

        # 3. ThingsBoard IoT Gateway Modbus TCP Config
        mb_cfg = generate_tb_gateway_modbus_config(devices, variables)
        zf.writestr(
            "03_ThingsBoard_IoT_Gateway_modbus.json",
            json.dumps(mb_cfg, indent=2, ensure_ascii=False).encode("utf-8"),
        )

        # 4. 70 ISA-101 Modular Widgets Bundle
        bundle = generate_thingsboard_widget_bundle()
        zf.writestr(
            "04_Widgets_ISA101_Bundle_70.json",
            json.dumps(bundle, indent=2, ensure_ascii=False).encode("utf-8"),
        )

        # 5. All Device Dashboards
        for dev in devices:
            dev_vars = [v for v in variables if v.device_id == dev.id]
            dash = generate_thingsboard_dashboard(dev, dev_vars)
            safe_id = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in dev.id)
            zf.writestr(
                f"dashboards/{safe_id}_dashboard.json",
                json.dumps(dash, indent=2, ensure_ascii=False).encode("utf-8"),
            )

        # 6. Commercial PDF Catalog if present on disk
        pdf_path = get_base_dir() / "Documentation" / "user" / "catalogue_commercial_cas_usage.pdf"
        if pdf_path.is_file():
            zf.write(pdf_path, arcname="Catalogue_Commercial_Cas_Usage.pdf")

    return buf.getvalue()
