"""Simple file-based processing cache for DocumentInfo objects."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


_CACHE_DIR = Path(os.environ.get("DA_CACHE_DIR", Path.home() / ".cache" / "is_backoffice" / "doc_analysis"))


class ProcessingCache:
    """Persist parsed DocumentInfo JSON to disk keyed by file hash."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._dir = Path(cache_dir) if cache_dir else _CACHE_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def get(self, file_path: str | Path) -> dict | None:
        key = self._key(file_path)
        cache_file = self._dir / f"{key}.json"
        if not cache_file.exists():
            return None
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None

    def set(self, file_path: str | Path, data: dict) -> None:
        key = self._key(file_path)
        cache_file = self._dir / f"{key}.json"
        try:
            cache_file.write_text(json.dumps(data, default=str, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass  # Cache writes are best-effort

    def invalidate(self, file_path: str | Path) -> None:
        key = self._key(file_path)
        cache_file = self._dir / f"{key}.json"
        cache_file.unlink(missing_ok=True)

    def clear(self) -> int:
        count = 0
        for f in self._dir.glob("*.json"):
            f.unlink(missing_ok=True)
            count += 1
        return count

    def _key(self, file_path: str | Path) -> str:
        path = Path(file_path).expanduser().resolve()
        try:
            stat = path.stat()
            signature = f"{path}:{stat.st_size}:{stat.st_mtime}"
        except OSError:
            signature = str(path)
        return hashlib.sha256(signature.encode()).hexdigest()[:16]
