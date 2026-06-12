"""Small import and smoke tests for the new smart plant modules.

Run with: python -m tests.import_check
"""
import importlib
import importlib.util
import traceback
from pathlib import Path


MODULE_FILES = [
    Path("pages") / "smart_plant_dashboard.py",
    Path("pages") / "smart_plant_config.py",
    Path("components") / "threejs_plant.py",
]


def try_import_path(path: Path):
    print(f"--- Loading {path}")
    try:
        if not path.exists():
            print("file missing:", path)
            return None
        name = path.stem
        spec = importlib.util.spec_from_file_location(name, str(path.resolve()))
        mod = importlib.util.module_from_spec(spec)
        loader = spec.loader
        assert loader is not None
        loader.exec_module(mod)
        print(str(path), "loaded OK")
        return mod
    except Exception:
        traceback.print_exc()
        return None


def smoke_tests():
    mods = {}
    for p in MODULE_FILES:
        mods[str(p)] = try_import_path(p)

    # Test load_config from dashboard
    dash = mods.get(str(Path("pages") / "smart_plant_dashboard.py"))
    if dash:
        try:
            cfg = dash.load_config()
            print("dashboard.load_config() keys:", list(cfg.keys()))
        except Exception:
            traceback.print_exc()
    # Test load_config from config page
    cfg_mod = mods.get(str(Path("pages") / "smart_plant_config.py"))
    if cfg_mod:
        try:
            cfg2 = cfg_mod.load_config()
            print("config.load_config() keys:", list(cfg2.keys()))
        except Exception:
            traceback.print_exc()

    # Test threejs component function presence
    three = mods.get("components.threejs_plant")
    if three:
        print("threejs has render_3d_plant:", hasattr(three, "render_3d_plant"))

    # Check config file exists
    p = Path("data/smart_plant_config.json")
    print("config file exists:", p.exists(), str(p.resolve()))


if __name__ == "__main__":
    smoke_tests()
