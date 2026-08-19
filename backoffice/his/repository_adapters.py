from __future__ import annotations

import hashlib
import mimetypes
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from .corporate_models import SourceDependency


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_PARENT = REPO_ROOT.parent


class RepositoryAdapterError(ValueError):
    """Raised when a repository operation violates the configured boundary."""


@dataclass(frozen=True)
class CorporateRepositorySettings:
    ai_factory_root: Path
    adaptive_sales_engine_root: Path
    ingesite_root: Path
    ingesite_staging_root: Path
    output_root: Path
    registry_path: Path

    @classmethod
    def from_environment(cls) -> CorporateRepositorySettings:
        output_root = Path(os.getenv("HTML_INTELLIGENCE_OUTPUT_ROOT", REPO_ROOT / "reports" / "html_intelligence"))
        return cls(
            ai_factory_root=Path(os.getenv("HTML_INTELLIGENCE_AI_FACTORY_ROOT", WORKSPACE_PARENT / "AI-FACTORY-v2")),
            adaptive_sales_engine_root=Path(
                os.getenv("HTML_INTELLIGENCE_ASE_ROOT", WORKSPACE_PARENT / "adaptive-sales-engine")
            ),
            ingesite_root=Path(os.getenv("HTML_INTELLIGENCE_INGESITE_ROOT", WORKSPACE_PARENT / "ingesite.github.io")),
            ingesite_staging_root=Path(
                os.getenv("HTML_INTELLIGENCE_INGESITE_STAGING_ROOT", output_root / "ingesite_staging")
            ),
            output_root=output_root,
            registry_path=Path(
                os.getenv("HTML_INTELLIGENCE_REGISTRY_PATH", output_root / "document_registry.json")
            ),
        )


class RepositoryAdapter:
    repository_id: ClassVar[str]
    allowed_extensions: ClassVar[frozenset[str]] = frozenset()
    allowed_roots: ClassVar[tuple[str, ...]] = ()
    excluded_parts: ClassVar[frozenset[str]] = frozenset(
        {".git", ".venv", "venv", "node_modules", "__pycache__", ".env", ".netlify"}
    )

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def resolve_source(self, relative_path: str | Path) -> Path:
        candidate = (self.root / relative_path).resolve()
        if not self._is_relative_to(candidate, self.root):
            raise RepositoryAdapterError(f"Source path escapes repository root: {relative_path}")
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        relative = candidate.relative_to(self.root)
        if any(part.lower() in self.excluded_parts for part in relative.parts):
            raise RepositoryAdapterError(f"Source path is excluded: {relative_path}")
        if self.allowed_extensions and candidate.suffix.lower() not in self.allowed_extensions:
            raise RepositoryAdapterError(f"Source format is not allowed: {candidate.suffix}")
        if self.allowed_roots and relative.parts and relative.parts[0].lower() not in self.allowed_roots:
            raise RepositoryAdapterError(f"Source is outside allowed repository areas: {relative_path}")
        return candidate

    def snapshot(self, relative_path: str | Path) -> SourceDependency:
        source = self.resolve_source(relative_path)
        stat = source.stat()
        return SourceDependency(
            repository_id=self.repository_id,
            relative_path=source.relative_to(self.root).as_posix(),
            sha256=self.hash_file(source),
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            adapter=type(self).__name__,
            media_type=mimetypes.guess_type(source.name)[0],
        )

    def is_stale(self, dependency: SourceDependency) -> bool:
        if dependency.repository_id != self.repository_id:
            raise RepositoryAdapterError(
                f"Dependency belongs to {dependency.repository_id}, not {self.repository_id}"
            )
        try:
            source = self.resolve_source(dependency.relative_path)
        except FileNotFoundError:
            return True
        return self.hash_file(source) != dependency.sha256

    @staticmethod
    def hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _is_relative_to(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True


class AIFactoryRepositoryAdapter(RepositoryAdapter):
    repository_id = "ai_factory"
    allowed_extensions = frozenset({".json", ".yaml", ".yml", ".md", ".txt", ".html", ".css", ".png", ".jpg", ".jpeg", ".svg"})
    allowed_roots = ("data", "schemas", "ai-factory-v2", "scripts", "tests")

    def resolve_source(self, relative_path: str | Path) -> Path:
        relative = Path(relative_path)
        if len(relative.parts) == 1 and relative.suffix.lower() in {".html", ".css"}:
            candidate = (self.root / relative).resolve()
            if not candidate.is_file():
                raise FileNotFoundError(candidate)
            return candidate
        return super().resolve_source(relative_path)


class AdaptiveSalesEngineRepositoryAdapter(RepositoryAdapter):
    repository_id = "adaptive_sales_engine"
    allowed_extensions = frozenset(
        {".json", ".md", ".txt", ".html", ".css", ".ts", ".tsx", ".csv", ".xlsx", ".docx", ".pdf", ".tpl"}
    )
    allowed_roots = ("documents", "templates", "src", "tests")


class IngesiteRepositoryAdapter(RepositoryAdapter):
    repository_id = "ingesite"
    allowed_extensions = frozenset({".html", ".css", ".js", ".json", ".md", ".txt", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".pdf", ".pptx"})
    allowed_roots = ("solutions", "css", "assets", "docs", "public")

    def __init__(self, root: str | Path, staging_root: str | Path) -> None:
        super().__init__(root)
        self.staging_root = Path(staging_root).expanduser().resolve()
        if self._is_relative_to(self.staging_root, self.root):
            raise RepositoryAdapterError("INGESITE staging must be outside the source repository")

    def resolve_source(self, relative_path: str | Path) -> Path:
        relative = Path(relative_path)
        if len(relative.parts) == 1 and relative.suffix.lower() == ".html":
            candidate = (self.root / relative).resolve()
            if not candidate.is_file():
                raise FileNotFoundError(candidate)
            return candidate
        return super().resolve_source(relative_path)

    def validate_sync_destination(self, destination: str | Path) -> Path:
        candidate = Path(destination).expanduser().resolve()
        if not self._is_relative_to(candidate, self.staging_root):
            raise RepositoryAdapterError("INGESITE output must stay inside the configured staging root")
        if self._is_relative_to(candidate, self.root):
            raise RepositoryAdapterError("INGESITE originals are read-only")
        return candidate


def build_repository_adapters(
    settings: CorporateRepositorySettings | None = None,
) -> dict[str, RepositoryAdapter]:
    current = settings or CorporateRepositorySettings.from_environment()
    return {
        "ai_factory": AIFactoryRepositoryAdapter(current.ai_factory_root),
        "adaptive_sales_engine": AdaptiveSalesEngineRepositoryAdapter(current.adaptive_sales_engine_root),
        "ingesite": IngesiteRepositoryAdapter(current.ingesite_root, current.ingesite_staging_root),
    }
