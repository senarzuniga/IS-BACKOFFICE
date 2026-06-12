"""Runtime smoke tests for Smart Plant modules.

Performs safe backups of `data/smart_plant_config.json`, tests load/save
behaviour and calls rendering helpers to ensure they don't raise exceptions.
"""
from pathlib import Path
import shutil
import importlib.util
import traceback


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path.resolve()))
    mod = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(mod)
    return mod


def main():
    cfg_path = Path("data/smart_plant_config.json")
    backup = cfg_path.with_suffix(".json.bak")

    try:
        if cfg_path.exists():
            shutil.copy(cfg_path, backup)
            print("Backup created:", backup)

        # Remove config to test default creation
        if cfg_path.exists():
            cfg_path.unlink()
            print("Removed existing config to test creation")

        dash_mod = load_module(Path("pages") / "smart_plant_dashboard.py")
        cfg = dash_mod.load_config()
        print("load_config created keys:", list(cfg.keys()))
        print("Config file exists after load_config():", cfg_path.exists())

        # Test rendering helpers (will call streamlit components but should not raise)
        try:
            print("Calling render_plant() (2D)...")
            dash_mod.render_plant(cfg)
            print("render_plant OK")
        except Exception:
            traceback.print_exc()

        # Test 3D component
        three_path = Path("components") / "threejs_plant.py"
        if three_path.exists():
            three_mod = load_module(three_path)
            try:
                print("Calling render_3d_plant() (may require CDN)...")
                three_mod.render_3d_plant(cfg.get("hotspots", []))
                print("render_3d_plant invoked OK")
            except Exception:
                traceback.print_exc()

        # Test config page save/load
        cfg_mod = load_module(Path("pages") / "smart_plant_config.py")
        original = cfg_mod.load_config()
        temp = dict(original)
        temp["overview_text"] = "__TEST_SAVE__"
        cfg_mod.save_config(temp)
        reloaded = cfg_mod.load_config()
        print("Saved overview_text ->", reloaded.get("overview_text"))

        # Restore original via save_config
        cfg_mod.save_config(original)
        print("Restored original config via save_config()")

    except Exception:
        traceback.print_exc()
    finally:
        # Restore backup file if exists
        if backup.exists():
            shutil.copy(backup, cfg_path)
            backup.unlink()
            print("Restored config from backup")


if __name__ == "__main__":
    main()
