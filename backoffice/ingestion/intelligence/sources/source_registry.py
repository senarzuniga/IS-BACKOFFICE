"""Source registry – loads SourceConfig list from sources.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
    _YAML_OK = True
except ImportError:
    _YAML_OK = False

from backoffice.ingestion.intelligence.models.source_config import SourceConfig


class SourceRegistry:
    def __init__(self, config_path: str | Path = "config/sources.yaml") -> None:
        self.config_path = Path(config_path)
        self.sources: list[SourceConfig] = []

    def load(self) -> list[SourceConfig]:
        if not _YAML_OK:
            import logging
            logging.getLogger(__name__).warning("pyyaml not installed – source registry empty")
            return []
        raw: dict[str, Any] = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        self.sources = [SourceConfig.from_dict(item) for item in raw.get("sources", [])]
        return self.sources

    def get_by_id(self, source_id: str) -> SourceConfig | None:
        return next((s for s in self.sources if s.id == source_id), None)

    def list_active(self) -> list[SourceConfig]:
        return [s for s in self.sources if s.is_active]
