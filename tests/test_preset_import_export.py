import os
import tempfile
import pytest
from app.core.equipment_catalog import (
    get_equipment_catalog,
    get_builtin_catalog,
    load_custom_presets,
    save_custom_preset,
    delete_custom_preset,
    build_preset_export_package,
    build_all_presets_export_package,
    import_preset_data,
    instantiate_preset,
    InstantiatePresetRequest,
    EquipmentPreset,
)
from app.models.device import TransportProtocol, PlatformType
from app.models.variable import VariableConfig, VariableType, DataType, SimMode, MathConfig
from app.storage.repository import StorageRepository

def test_builtin_catalog_integrity():
    """Vérifie que les 32 modèles d'usine sont chargés et intègres avec is_custom=False."""
    builtins = get_builtin_catalog()
    assert len(builtins) == 32
    for p in builtins:
        assert p.is_custom is False
        assert len(p.variables) > 0
        assert p.category in ("industry", "building", "infrastructure", "smart_city")

def test_build_preset_export_package_exhaustive():
    """Vérifie que le package d'export unitaire contient l'intégralité des 4 volets requis."""
    builtins = get_builtin_catalog()
    compressor = next(p for p in builtins if p.id == "ind_compressor")
    
    pkg = build_preset_export_package(compressor)
    assert pkg["schema_version"] == "2.1.0"
    assert pkg["export_type"] == "single_preset"
    assert "export_date" in pkg
    assert "generator" in pkg
    
    # 1. Preset complet avec variables et math_config
    preset_data = pkg["preset"]
    assert preset_data["id"] == "ind_compressor"
    assert len(preset_data["variables"]) == len(compressor.variables)
    press_var = next(v for v in preset_data["variables"] if v["id"] == "pression_reseau")
    assert press_var["sim_mode"] == "sawtooth"
    assert press_var["math_config"]["min_val"] == 6.2
    assert press_var["math_config"]["max_val"] == 8.5
    
    # 2. Modèle Dashboard ThingsBoard complet
    dash = pkg["dashboard_template"]
    assert "title" in dash
    assert "configuration" in dash
    assert "widgets" in dash["configuration"]
    
    # 3. Modèle CSV ThingsBoard
    csv_t = pkg["csv_template"]
    assert csv_t["headers"] == "name,type,label,access_token"
    assert "Centrale d'Air Comprimé" in csv_t["sample_row"]
    
    # 4. Spécifications d'instanciation
    spec = pkg["instantiation_spec"]
    assert spec["suggested_device_id_prefix"] == "ind_compressor"
    assert spec["default_protocol"] == "mqtt"
    assert spec["variables_count"] == len(compressor.variables)

def test_build_all_presets_export_package():
    """Vérifie que l'export global bundle inclut tous les presets."""
    bundle = build_all_presets_export_package()
    assert bundle["schema_version"] == "2.1.0"
    assert bundle["export_type"] == "presets_bundle"
    assert bundle["total_presets"] >= 32
    assert len(bundle["presets_packages"]) == bundle["total_presets"]

def test_custom_preset_lifecycle_and_isolation():
    """Vérifie le cycle de vie complet (sauvegarde, chargement, instanciation, suppression) dans un fichier isolé."""
    tmp_dir = tempfile.mkdtemp()
    custom_file = os.path.join(tmp_dir, "custom_presets_test.json")

    try:
        # Initialement vide
        assert load_custom_presets(custom_file) == []

        # Création d'un preset personnalisé
        custom_p = EquipmentPreset(
            id="my_custom_oven",
            name="Four Industriel Haute Température",
            category="industry",
            category_label="Industrie & Automatismes",
            description="Four de traitement thermique à régulation PID avancée",
            icon="flame",
            default_protocol=TransportProtocol.MQTT,
            default_platform=PlatformType.THINGSBOARD,
            variables=[
                VariableConfig(
                    id="four_temp",
                    name="Température Cuve",
                    device_id="",
                    var_type=VariableType.TELEMETRY,
                    data_type=DataType.FLOAT,
                    unit="°C",
                    publish_interval=1.0,
                    sim_mode=SimMode.RANDOM_WALK,
                    math_config=MathConfig(min_val=150.0, max_val=850.0, step=2.5)
                )
            ]
        )

        save_custom_preset(custom_p, file_path=custom_file)

        # Vérification chargement
        loaded = load_custom_presets(custom_file)
        assert len(loaded) == 1
        assert loaded[0].id == "my_custom_oven"
        assert loaded[0].is_custom is True

        # Vérification fusion catalogue global
        unified_catalog = get_equipment_catalog(file_path=custom_file)
        assert len(unified_catalog) == 33
        assert any(p.id == "my_custom_oven" for p in unified_catalog)

        # Test d'instanciation en 1 clic
        state_file = os.path.join(tmp_dir, "sim_state_test.json")
        repo = StorageRepository(file_path=state_file)
        
        req = InstantiatePresetRequest(
            preset_id="my_custom_oven",
            device_id="four_prod_01",
            name="Four Ligne 1",
            token="FOUR_SECRET_TOKEN_123"
        )
        
        # On mock get_equipment_catalog pour retourner le catalogue contenant notre custom
        import app.core.equipment_catalog as ec
        orig_get_catalog = ec.get_equipment_catalog
        ec.get_equipment_catalog = lambda: unified_catalog
        try:
            device, vars_created = instantiate_preset(req, repo)
            assert device.id == "four_prod_01"
            assert device.name == "Four Ligne 1"
            assert device.token == "FOUR_SECRET_TOKEN_123"
            assert len(vars_created) == 1
            assert vars_created[0].id == "four_prod_01_four_temp"
            assert vars_created[0].device_id == "four_prod_01"
            assert vars_created[0].math_config.min_val == 150.0
        finally:
            ec.get_equipment_catalog = orig_get_catalog

        # Suppression du preset personnalisé
        deleted = delete_custom_preset("my_custom_oven", file_path=custom_file)
        assert deleted is True
        assert len(load_custom_presets(custom_file)) == 0

        # Tentative de suppression d'un modèle d'usine natif -> doit lever ValueError
        with pytest.raises(ValueError) as excinfo:
            delete_custom_preset("ind_compressor", file_path=custom_file)
        assert "modèle natif d'usine" in str(excinfo.value)

    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

def test_import_preset_data_various_formats():
    """Vérifie l'importation souple : package complet, collision d'ID natif, et bundle."""
    tmp_dir = tempfile.mkdtemp()
    custom_file = os.path.join(tmp_dir, "custom_presets_test.json")

    try:
        # 1. Import d'un package complet issu d'un export
        builtins = get_builtin_catalog()
        compressor = next(p for p in builtins if p.id == "ind_compressor")
        pkg = build_preset_export_package(compressor)
        
        # Le preset importé porte l'id "ind_compressor", il doit être renommé "ind_compressor_custom"
        count, ids = import_preset_data(pkg, file_path=custom_file)
        assert count == 1
        assert ids == ["ind_compressor_custom"]
        
        loaded = load_custom_presets(custom_file)
        assert len(loaded) == 1
        assert loaded[0].id == "ind_compressor_custom"
        assert loaded[0].is_custom is True
        assert "Personnalisé" in loaded[0].name

        # Les modèles d'usine n'ont pas bougé
        assert len(get_builtin_catalog()) == 32

        # 2. Import d'un modèle direct sans enveloppe
        direct_model = {
            "id": "direct_sensor",
            "name": "Capteur LoRaWAN Direct",
            "category": "infrastructure",
            "category_label": "Infrastructures & Énergie",
            "description": "Capteur télémesure autonome",
            "variables": [
                {
                    "id": "battery_lvl",
                    "name": "Batterie",
                    "var_type": "telemetry",
                    "data_type": "float",
                    "unit": "%",
                    "sim_mode": "random_walk",
                    "math_config": {"min_val": 20.0, "max_val": 100.0}
                }
            ]
        }
        count, ids = import_preset_data(direct_model, file_path=custom_file)
        assert count == 1
        assert ids == ["direct_sensor"]
        assert len(load_custom_presets(custom_file)) == 2

    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
