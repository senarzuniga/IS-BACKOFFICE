from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RepositoryEntry:
    name: str
    path: str
    role: str
    priority: str = "normal"


class RepositoryCatalog:
    """Controlled repository registry used by HIS for asset and knowledge discovery."""

    DEFAULT_KNOWLEDGE_SOURCES = [
        "html_templates",
        "landing_pages",
        "presentations",
        "reports",
        "assets",
        "css",
    ]

    def __init__(self, catalog_path: Path) -> None:
        self.catalog_path = catalog_path
        self._catalog = self._load_or_bootstrap(catalog_path)

    def data(self) -> dict[str, Any]:
        return dict(self._catalog)

    def repositories(self) -> list[RepositoryEntry]:
        entries = self._catalog.get("repositories", [])
        out: list[RepositoryEntry] = []
        for row in entries:
            if not isinstance(row, dict):
                continue
            out.append(
                RepositoryEntry(
                    name=str(row.get("name", "unknown")),
                    path=str(row.get("path", "")),
                    role=str(row.get("role", "unspecified")),
                    priority=str(row.get("priority", "normal")),
                )
            )
        return out

    def knowledge_sources(self) -> list[str]:
        raw = self._catalog.get("knowledge_sources", [])
        if not isinstance(raw, list):
            return list(self.DEFAULT_KNOWLEDGE_SOURCES)
        values = [str(x).strip() for x in raw if str(x).strip()]
        return values or list(self.DEFAULT_KNOWLEDGE_SOURCES)

    def existing_repository_paths(self) -> list[Path]:
        paths: list[Path] = []
        for repo in self.repositories():
            path = Path(repo.path).expanduser()
            if path.exists() and path.is_dir():
                paths.append(path)
        return paths

    def resolve_knowledge_roots(self) -> list[Path]:
        """Resolve effective roots to scan, constrained by the repository catalog."""
        sources = set(self.knowledge_sources())
        resolved: list[Path] = []
        for repo_root in self.existing_repository_paths():
            resolved.append(repo_root)
            for candidate in repo_root.rglob("*"):
                if not candidate.is_dir():
                    continue
                name = candidate.name.lower()
                if name in sources:
                    resolved.append(candidate)
        unique: list[Path] = []
        seen: set[str] = set()
        for path in resolved:
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            unique.append(path)
        return unique

    def _load_or_bootstrap(self, path: Path) -> dict[str, Any]:
        if path.exists():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                data = None
            if isinstance(data, dict):
                return data

        path.parent.mkdir(parents=True, exist_ok=True)
        default_payload = {
            "repositories": [
                {
                    "name": "is_backoffice",
                    "path": str(Path(__file__).resolve().parents[2]),
                    "role": "Application Platform",
                    "priority": "high",
                }
            ],
            "knowledge_sources": list(self.DEFAULT_KNOWLEDGE_SOURCES),
        }
        path.write_text(yaml.safe_dump(default_payload, sort_keys=False, allow_unicode=False), encoding="utf-8")
        return default_payload