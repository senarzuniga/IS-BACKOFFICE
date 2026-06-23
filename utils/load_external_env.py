"""Load external .env file (AI-FACTORY-v2) into os.environ.

This loader is conservative: it will not overwrite existing environment
variables unless `override=True`. It tries several likely paths and is
safe to call multiple times.
"""

import os
from pathlib import Path
from typing import Dict


DEFAULT_CANDIDATES = [
    Path.home() / 'Documents' / 'GitHub' / 'AI-FACTORY-v2' / '.env',
    Path.cwd().parent / 'AI-FACTORY-v2' / '.env',
    Path('C:/Users/Inaki Senar/Documents/GitHub/AI-FACTORY-v2/.env')
]


def _parse_env_file(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    with path.open('r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                data[k] = v
    return data


def find_env_file(candidates: list = None) -> Path:
    candidates = candidates or DEFAULT_CANDIDATES
    for p in candidates:
        try:
            path = Path(p)
            if path.exists():
                return path
        except Exception:
            continue
    return None


def load_external_env(path: str = None, override: bool = False) -> Dict[str, str]:
    """Load KEY=VALUE pairs from `path` or from default AI-FACTORY locations.

    Returns the dictionary of loaded values (only those written to `os.environ`).
    """
    env_path = Path(path) if path else find_env_file()
    if not env_path:
        return {}

    try:
        parsed = _parse_env_file(env_path)
    except Exception as e:
        print(f"Warning: could not parse env file {env_path}: {e}")
        return {}

    written = {}
    for k, v in parsed.items():
        if not override and k in os.environ:
            continue
        # Only write non-empty values
        if v is None or v == "":
            continue
        os.environ[k] = v
        written[k] = v

    if written:
        # Print metadata only (no secret values)
        print(f"Loaded {len(written)} environment variables from {env_path}")

    return written


__all__ = ["load_external_env", "find_env_file"]
