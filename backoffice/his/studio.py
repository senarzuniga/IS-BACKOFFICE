from __future__ import annotations

import base64
import json
import mimetypes
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from bs4 import BeautifulSoup

from backoffice.dipc.component_library import normalize_component
from backoffice.dipc.mission_manager import DocumentIntelligencePublishingCenter
from backoffice.dipc.models import (
    AssetRef,
    BlockNode,
    DocumentModel,
    EvidenceRecord,
    KnowledgeLink,
    MissionLink,
    SectionNode,
    VersionEntry,
)
from backoffice.dipc.preview_engine import PreviewEngine
from backoffice.dipc.publication_engine import PublicationEngine
from backoffice.dipc.versioning import DocumentVersionStore
from backoffice.his.ahde import OperationalCertificationEngine
from backoffice.his.corporate_models import DeliveryPolicy
from backoffice.his.corporate_publishing import CorporatePublishingService
from backoffice.his.repository import DocumentRepository
from backoffice.his.repository_catalog import RepositoryCatalog
from backoffice.his.quality_pipeline_v3 import HtmlIntelligenceStudioV3Pipeline
from backoffice.his.service import HtmlDocumentService
from backoffice.his.stability import CheckpointManager, HealthChecker, MissionWatchdog, SmartAssetCache, scan_streamlit_widget_collisions


REPO_ROOT = Path(__file__).resolve().parents[2]
CORPORATE_MODEL_PATH = Path(r"C:\Users\Inaki Senar\Documents\GitHub\ingesite.github.io\Modelo_HTML.txt")
MISSION_REGISTRY_PATH = REPO_ROOT / "reports" / "html_intelligence_studio" / "mission_registry.jsonl"
MISSION_REGISTRY_FALLBACK = REPO_ROOT / "reports" / "html_intelligence_studio" / "mission_registry_fallback.jsonl"
FIRST_MISSION_HTML = REPO_ROOT / "reports" / "pie" / "20260731_152246_6c632e87" / "version_2_smart_reconstruction" / "index.html"
FIRST_MISSION_IMAGE = Path(
    r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\CONTENT\Corrugated Plant Automation Solutions v2 IMAGEN GENERAL.jpg"
)
REPOSITORY_CATALOG_PATH = REPO_ROOT / "config" / "repository_catalog.yaml"

THEME_PROFILE_TO_VARIANT = {
    "ingecart_industrial": "industrial",
    "service_engine": "light",
}


@dataclass
class StrategyDecision:
    strategy: str
    executive_score: float
    hypotheses: list[dict[str, Any]]
    selected_hypothesis: str


class HtmlIntelligenceStudio:
    """Corporate HTML generation and mission-driven editing engine."""

    def __init__(self, corporate_model_path: Path | None = None) -> None:
        self.corporate_model_path = corporate_model_path or CORPORATE_MODEL_PATH
        self.publisher = PublicationEngine()
        self.preview_engine = PreviewEngine()
        self.dipc = DocumentIntelligencePublishingCenter()
        # RC1 consolidation: only V3 remains active as the official engine.
        self.pipeline_v3 = HtmlIntelligenceStudioV3Pipeline(self.corporate_model_path)
        self.repository = DocumentRepository(REPO_ROOT / "reports")
        self.service = HtmlDocumentService(self.repository, self)
        self.watchdog = MissionWatchdog(timeout_seconds=120)
        self.checkpoints = CheckpointManager()
        self.asset_cache = SmartAssetCache()
        self.health_checker = HealthChecker(REPO_ROOT)
        self.repository_catalog = RepositoryCatalog(REPOSITORY_CATALOG_PATH)
        self.certification_engine = OperationalCertificationEngine(REPO_ROOT)
        self.corporate_publishing = CorporatePublishingService()

    def validate_html_stability(self, html_path: str | Path) -> dict[str, Any]:
        path = Path(html_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"HTML file not found: {path}")

        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        risky_patterns = [
            r"<link[^>]+href=[\"'](?!https?:|data:|//)[^\"']+[\"']",
            r"<script[^>]+src=[\"'](?!https?:|data:|//)[^\"']+[\"']",
            r"<img[^>]+src=[\"'](?!https?:|data:|//)[^\"']+[\"']",
            r"src=[\"']\.?\./[^\"']+",
            r"href=[\"']\.?\./[^\"']+",
        ]
        findings: list[str] = []
        for pattern in risky_patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                findings.extend(matches)

        portable = not findings and "<style" in lowered and "<body" in lowered
        return {
            "html_path": str(path),
            "portable": portable,
            "risk_level": "LOW" if portable else "HIGH",
            "local_asset_references": findings,
            "has_inline_style": "<style" in lowered,
            "has_inline_script": "<script" in lowered,
            "data_uri_count": text.count("data:image/"),
        }

    def guarantee_standalone_html(self, html_path: str | Path) -> dict[str, Any]:
        path = Path(html_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"HTML file not found: {path}")

        html_text = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html_text, "html.parser")
        changed = False

        for tag in list(soup.select('link[rel="stylesheet"][href]')):
            href = str(tag.get("href", "")).strip()
            if not href or href.startswith(("http://", "https://", "data:", "//")):
                continue
            candidate = (path.parent / href).resolve() if not Path(href).is_absolute() else Path(href)
            if not candidate.exists() or not candidate.is_file():
                continue
            css_text = candidate.read_text(encoding="utf-8", errors="ignore")
            style_tag = soup.new_tag("style")
            style_tag.string = css_text
            tag.replace_with(style_tag)
            changed = True

        for tag in list(soup.select("script[src]")):
            src = str(tag.get("src", "")).strip()
            if not src or src.startswith(("http://", "https://", "data:", "//")):
                continue
            candidate = (path.parent / src).resolve() if not Path(src).is_absolute() else Path(src)
            if not candidate.exists() or not candidate.is_file():
                continue
            js_text = candidate.read_text(encoding="utf-8", errors="ignore")
            tag.clear()
            tag.string = js_text
            tag.attrs = {}
            changed = True

        for tag in list(soup.find_all(["img", "source"])):
            src = str(tag.get("src", "")).strip()
            if not src or src.startswith(("http://", "https://", "data:", "//")):
                continue
            candidate = (path.parent / src).resolve() if not Path(src).is_absolute() else Path(src)
            if not candidate.exists() or not candidate.is_file():
                continue
            mime_type, _ = mimetypes.guess_type(str(candidate))
            if not mime_type:
                mime_type = "application/octet-stream"
            encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
            tag["src"] = f"data:{mime_type};base64,{encoded}"
            changed = True

        if changed:
            path.write_text(soup.decode(formatter="minimal"), encoding="utf-8")

        return self.validate_html_stability(path)

    def create_document(
        self,
        *,
        document_name: str,
        project: str,
        client: str,
        category: str,
        language: str,
        source_format: str,
        sources: list[str],
        output_root: str | None,
        comments: str,
        objective: str,
        audience: str,
        instruction_text: str,
        theme_profile: str = "ingecart_industrial",
    ) -> dict[str, Any]:
        task_id = self.watchdog.start_task(
            "create_document",
            {
                "document_name": document_name,
                "project": project,
                "category": category,
            },
        )
        self.checkpoints.create(
            "generate_html",
            "pre_execution",
            {"document_name": document_name, "project": project, "category": category},
        )
        cleaned_sources = [s.strip() for s in sources if s and s.strip()]
        selected_theme_variant = THEME_PROFILE_TO_VARIANT.get(theme_profile, "industrial")
        for src in cleaned_sources:
            self.asset_cache.register_asset(src, confidence=0.99, status="input_registered")

        mission_key = self.asset_cache.mission_key(cleaned_sources, source_format, language, document_name)
        reusable = self.asset_cache.get_reusable_mission(mission_key, min_confidence=0.95)
        if reusable:
            self.watchdog.heartbeat(task_id, progress=1.0, note="smart_cache_hit")
            self.watchdog.complete_task(task_id, result="SMART_CACHE_HIT")
            self.checkpoints.create(
                "generate_html",
                "cache_hit",
                {"mission_key": mission_key, "document_name": document_name},
            )
            return {
                **reusable,
                "smart_resume": True,
                "smart_resume_confidence": 0.95,
                "mission_cache_key": mission_key,
            }

        self.watchdog.heartbeat(task_id, progress=0.1, note="strategy_selection")
        strategy = self._select_strategy(source_format, cleaned_sources, instruction_text)

        chosen_source = self._choose_primary_source(cleaned_sources)
        date_folder = datetime.now(UTC).strftime("%Y%m%d")
        project_slug = self._slug(project or "general")
        category_slug = self._slug(category or "html")

        base_root = Path(output_root).expanduser().resolve() if output_root else (REPO_ROOT / "reports" / category_slug / project_slug / date_folder)
        base_root.mkdir(parents=True, exist_ok=True)
        self.checkpoints.create(
            "generate_html",
            "pre_pipeline",
            {
                "output_root": str(base_root),
                "sources": cleaned_sources,
                "mission_key": mission_key,
            },
        )

        self.watchdog.heartbeat(task_id, progress=0.35, note="pipeline_run_start")
        result = self.pipeline_v3.run(
            sources=cleaned_sources,
            source_format=source_format,
            output_root=str(base_root),
            document_name=document_name,
            project=project,
            client=client,
            category=category,
            language=language,
            objective=objective,
            audience=audience,
            theme_variant=selected_theme_variant,
            author="Mission Manager",
            force_no_cache=True,
            max_regeneration_attempts=2,
        )
        self.watchdog.heartbeat(task_id, progress=0.75, note="pipeline_run_done")
        model_path = Path(result["document_model_path"])
        model = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        self._enrich_document_metadata(
            model,
            document_name=document_name,
            project=project,
            client=client,
            category=category,
            language=language,
            comments=comments,
            objective=objective,
            audience=audience,
            source_format=source_format,
            instruction_text=instruction_text,
            strategy=strategy,
            all_sources=cleaned_sources,
            theme_profile=theme_profile,
            repository_catalog=self.get_repository_catalog(),
        )
        model_path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        self._write_his_registry(Path(result["output_dir"]), model, strategy)
        self.checkpoints.create(
            "generate_html",
            "pre_knowledge_hub_update",
            {"run_id": result.get("run_id", ""), "document_model_path": str(model_path)},
        )
        self._register_action_mission(
            action="generate_html",
            objective=objective or "Generate HTML",
            run_id=result.get("run_id", ""),
            model_path=result.get("document_model_path", ""),
            output_dir=result.get("output_dir", ""),
            payload={
                "document_name": document_name,
                "project": project,
                "client": client,
                "category": category,
                "language": language,
                "source_format": source_format,
                "sources": cleaned_sources,
                "publication_state": result.get("publication_state", "Draft"),
            },
        )
        self.asset_cache.register_mission_result(
            mission_key,
            {
                "run_id": result.get("run_id", ""),
                "output_dir": result.get("output_dir", ""),
                "html_path": result.get("html_path", ""),
                "document_model_path": result.get("document_model_path", ""),
            },
            confidence=0.99,
        )
        self.checkpoints.create(
            "generate_html",
            "post_execution",
            {"run_id": result.get("run_id", ""), "mission_key": mission_key},
        )
        self.watchdog.heartbeat(task_id, progress=1.0, note="completed")
        self.watchdog.complete_task(task_id)
        result["strategy"] = strategy.__dict__
        result["theme_profile"] = theme_profile
        result["theme_variant"] = selected_theme_variant
        result["mission_cache_key"] = mission_key
        result["smart_resume"] = False
        return result

    def run_ai_command(self, document_model_path: str, command: str) -> dict[str, Any]:
        result = self.pipeline_v3.apply_dom_command(document_model_path, command, author="AI Coordinator")
        self._register_action_mission(
            action="dom_command",
            objective=command,
            run_id=result.get("run_id", ""),
            model_path=result.get("document_model_path", document_model_path),
            output_dir=str(Path(document_model_path).resolve().parent.parent),
            payload={"changes": result.get("changes", [])},
        )
        return result

    def run_first_mission(self) -> dict[str, Any]:
        source_pptx = Path(r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\CONTENT\Corrugated Plant Automation Solutions v2.pptx")
        output_root = REPO_ROOT / "reports" / "pie" / "Corrugated_Plant_Automation"
        result = self.pipeline_v3.run(
            sources=[str(source_pptx)],
            source_format="PowerPoint",
            output_root=str(output_root),
            document_name="Corrugated Plant Automation Solutions",
            project="Corrugated_Plant_Automation",
            client="INGECART",
            category="pie",
            language="Bilingual",
            objective="Full HIS V3 reconstruction and quality gate validation",
            audience="Executive and Engineering",
            author="Mission Manager",
            force_no_cache=True,
            max_regeneration_attempts=2,
        )
        self._register_action_mission(
            action="first_mission_regeneration",
            objective="Regenerate Corrugated Plant Automation Solutions from source",
            run_id=result.get("run_id", ""),
            model_path=result.get("document_model_path", ""),
            output_dir=result.get("output_dir", ""),
            payload={"source": str(source_pptx), "publication_state": result.get("publication_state", "Draft")},
        )
        return result

    def insert_image_under_heading(
        self,
        *,
        document_model_path: str,
        image_path: str,
        heading_text: str,
        section_path: list[str] | None = None,
        author: str = "Mission Manager",
    ) -> dict[str, Any]:
        image_file = Path(image_path).expanduser().resolve()
        model_file = Path(document_model_path).expanduser().resolve()
        if not model_file.exists():
            raise FileNotFoundError(f"Document model not found: {model_file}")
        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_file}")

        # RC1 rule: DOM-only editing. HTML direct edits are forbidden.
        command = f'add image "{str(image_file)}" under heading "{heading_text}"'
        result = self.pipeline_v3.apply_dom_command(str(model_file), command, author=author)
        validation = self.validate_html(result["html_path"])

        mission_payload = {
            "mission_id": result.get("run_id", ""),
            "timestamp": datetime.now(UTC).isoformat(),
            "author": author,
            "document_model": str(model_file),
            "html_output": result.get("html_path", ""),
            "image_source": str(image_file),
            "section_path": section_path or [heading_text],
            "action": "insert_image_under_heading_dom",
            "heading": heading_text,
            "validation": validation,
        }
        self._register_action_mission(
            action="insert_image",
            objective=f"Insert image under heading: {heading_text}",
            run_id=result.get("run_id", ""),
            model_path=result.get("document_model_path", str(model_file)),
            output_dir=str(model_file.parent.parent),
            payload=mission_payload,
        )
        self._update_hub_and_memory(mission_payload)
        result["validation"] = validation
        return result

    def change_language(self, document_model_path: str, target_language: str, author: str = "Mission Manager") -> dict[str, Any]:
        cmd = f"translate document to {target_language}"
        result = self.pipeline_v3.apply_dom_command(document_model_path, cmd, author=author)
        self._register_action_mission(
            action="change_language",
            objective=cmd,
            run_id=result.get("run_id", ""),
            model_path=result.get("document_model_path", document_model_path),
            output_dir=str(Path(document_model_path).resolve().parent.parent),
            payload={"target_language": target_language},
        )
        return result

    def publish_document(self, document_model_path: str, author: str = "Mission Manager") -> dict[str, Any]:
        self.checkpoints.create(
            "publish",
            "pre_publication",
            {"document_model_path": document_model_path, "author": author},
        )
        model_path = Path(document_model_path).expanduser().resolve()
        if not model_path.exists():
            raise FileNotFoundError(f"Document model not found: {model_path}")

        model = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        base_dir = model_path.parent.parent
        quality_path = base_dir / "metadata" / "quality_report.json"
        if not quality_path.exists():
            raise RuntimeError("quality_report.json not found. Run generation first.")

        quality = json.loads(quality_path.read_text(encoding="utf-8"))
        selected_scores = quality.get("selected_scores", {})
        selected_quality = quality.get("selected_quality", {})
        metrics = selected_quality.get("metrics", {})
        executive_score = float(selected_scores.get("executive_quality_score", 0.0))
        theme_score = float(metrics.get("theme_compliance", 0.0))
        accessibility_score = float(metrics.get("accessibility", 0.0))

        if executive_score < 95.0:
            raise RuntimeError(f"Publish blocked: Executive Quality Score {executive_score} < 95")
        if theme_score < 100.0:
            raise RuntimeError(f"Publish blocked: Corporate Theme Score {theme_score} < 100")
        if accessibility_score < 90.0:
            raise RuntimeError(f"Publish blocked: Accessibility {accessibility_score} < AA threshold")

        now = datetime.now(UTC).isoformat()
        history = model.metadata.get("publication_state_history", [])
        if not isinstance(history, list):
            history = []
        history.append({"state": "Published", "ts": now})
        model.metadata["publication_state"] = "Published"
        model.metadata["publication_state_history"] = history
        model.metadata["published_at"] = now
        model_path.write_text(model.model_dump_json(indent=2), encoding="utf-8")

        run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
        self._register_action_mission(
            action="publish",
            objective="Promote document to Published",
            run_id=run_id,
            model_path=str(model_path),
            output_dir=str(base_dir),
            payload={"executive_quality_score": executive_score, "theme_score": theme_score, "accessibility": accessibility_score},
        )
        self.checkpoints.create(
            "publish",
            "post_publication",
            {"document_model_path": str(model_path), "run_id": run_id},
        )
        return {
            "run_id": run_id,
            "document_model_path": str(model_path),
            "publication_state": "Published",
            "published_at": now,
        }

    def system_health_status(self) -> dict[str, Any]:
        """Return READY/WARNING/FAIL matrix for mission-critical services."""
        report = self.health_checker.run()
        health_path = REPO_ROOT / "reports" / "html_intelligence_studio" / f"his_health_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        health_path.parent.mkdir(parents=True, exist_ok=True)
        health_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return {**report, "report_path": str(health_path)}

    def get_repository_catalog(self) -> dict[str, Any]:
        return self.repository_catalog.data()

    def list_corporate_documents(self) -> list[dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.corporate_publishing.registry.list()]

    def publish_corporate_html(
        self,
        *,
        repository_id: str,
        relative_path: str,
        title: str,
        client: str,
        project: str,
        formats: list[str] | None = None,
        languages: list[str] | None = None,
        profile_id: str = "standard",
    ) -> dict[str, Any]:
        policy = DeliveryPolicy(
            profile_id=profile_id,
            allowed_formats=formats or ["html", "pdf", "docx"],
            required_languages=languages or ["en", "es"],
        )
        result = self.corporate_publishing.publish_bilingual_html(
            repository_id=repository_id,
            relative_path=relative_path,
            title=title,
            client=client,
            project=project,
            delivery_policy=policy,
        )
        return result.model_dump(mode="json")

    def package_corporate_document(self, document_id: str) -> str:
        return self.corporate_publishing.create_delivery_package(document_id)

    def resolve_asset_candidates(self, limit: int = 100) -> list[str]:
        allowed_extensions = {
            ".html",
            ".htm",
            ".md",
            ".pdf",
            ".ppt",
            ".pptx",
            ".doc",
            ".docx",
            ".png",
            ".jpg",
            ".jpeg",
            ".svg",
            ".css",
        }
        matches: list[str] = []
        for root in self.repository_catalog.resolve_knowledge_roots():
            for candidate in root.rglob("*"):
                if not candidate.is_file():
                    continue
                if candidate.suffix.lower() not in allowed_extensions:
                    continue
                matches.append(str(candidate))
                if len(matches) >= int(limit):
                    return matches
        return matches

    def theme_profiles(self) -> dict[str, Any]:
        return {
            "default": "ingecart_industrial",
            "available": ["ingecart_industrial", "service_engine"],
            "mapping": dict(THEME_PROFILE_TO_VARIANT),
        }

    def get_format_catalog(self) -> dict[str, Any]:
        ai_factory_root = Path(r"C:\Users\Inaki Senar\Documents\GitHub\AI-FACTORY-v2")
        ingecart_bundle = [
            str(ai_factory_root / "PAIGE_INGECART_MODEL_B_MASTER_REPORT_2026-08-18.html"),
            str(ai_factory_root / "PAIGE_INGECART_MODEL_B_MASTER_REPORT_2026-08-18.md"),
            str(ai_factory_root / "AI_FACTORY_MISSION_PAIGE_LAYOUT_A_VS_B_2026-08-17.txt"),
            str(ai_factory_root / "DIGITAL_TWIN_SIMULATION_REPORT_SHORT_RUNS_2026-08-19.txt"),
            str(ai_factory_root / "ANALISIS_PAIGE_LAYOUT_A_VS_B_2026-08-17.html"),
            str(ai_factory_root / "governance" / "global_operational_directive.md"),
        ]
        return {
            "default_format": "Ingecart",
            "formats": [
                {
                    "id": "Ingecart",
                    "label": "Ingecart",
                    "description": "Formato industrial basado en PAIGE Modelo B + Ingecart: flujo, trazabilidad, WIP, logística, salida y escalabilidad.",
                    "expected_output": "Informe maestro ejecutivo / HTML técnico con narrativa industrial y evidencias",
                    "source_bundle": ingecart_bundle,
                    "required_fields": ["formato", "cliente", "contexto"],
                    "template_reference": str(ai_factory_root / "PAIGE_INGECART_MODEL_B_MASTER_REPORT_2026-08-18.html"),
                },
                {
                    "id": "CTA",
                    "label": "CTA",
                    "description": "Formato futuro para call-to-action, propuesta comercial y executive deck.",
                    "expected_output": "Narrativa de valor, CTA y pitch comercial",
                    "source_bundle": [],
                    "required_fields": ["formato", "cliente", "contexto"],
                    "template_reference": None,
                },
            ],
            "intelligence_capabilities": [
                "cálculo industrial",
                "análisis de procesos",
                "modelado de máquinas",
                "simulación de flujo",
                "gestión de conocimiento",
                "búsqueda en red y fuentes externas",
                "validación de evidencias",
                "análisis de calidad y KPI",
                "base de datos y memoria de misión",
                "repositorio de formatos y plantillas",
            ],
            "mission_policy": [
                "Autonomous Hypothesis Driven Execution",
                "Mission Manager",
                "AI Coordinator",
                "Governance Engine",
                "Evidence Runtime",
                "Enterprise Memory",
                "Knowledge Graph",
                "Factory Graph",
                "Platform Registry",
                "Capability Registry",
            ],
            "workbench_paths": {
                "is_backoffice": str(Path(__file__).resolve().parents[2]),
                "ai_factory_v2": str(ai_factory_root),
                "global_directive": str(ai_factory_root / "governance" / "global_operational_directive.md"),
                "html_report_reference": str(ai_factory_root / "PAIGE_INGECART_MODEL_B_MASTER_REPORT_2026-08-18.html"),
            },
        }

    def run_operational_certification(self, max_iterations: int = 5, max_minutes: int = 30) -> dict[str, Any]:
        return self.certification_engine.run(
            studio=self,
            max_iterations=max_iterations,
            max_minutes=max_minutes,
        )

    def watchdog_status(self) -> dict[str, Any]:
        stalled = self.watchdog.detect_stalled_tasks()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "stalled_tasks": [s.__dict__ for s in stalled],
            "stalled_count": len(stalled),
            "status": "WARNING" if stalled else "READY",
        }

    def run_streamlit_stability_scan(self) -> dict[str, Any]:
        pages_dir = REPO_ROOT / "pages"
        report = scan_streamlit_widget_collisions(pages_dir)
        report["generated_at"] = datetime.now(UTC).isoformat()
        report_path = REPO_ROOT / "reports" / "html_intelligence_studio" / f"his_streamlit_stability_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = str(report_path)
        return report

    def export_release_bundle(self, document_model_path: str) -> str:
        model_path = Path(document_model_path).expanduser().resolve()
        if not model_path.exists():
            raise FileNotFoundError(f"Document model not found: {model_path}")
        model = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        if model.metadata.get("publication_state") != "Published":
            raise RuntimeError("Only Published documents can be exported.")

        base_dir = model_path.parent.parent
        export_dir = base_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        zip_path = export_dir / f"his_v3_release_bundle_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.zip"

        include_paths = [
            base_dir / "selected",
            base_dir / "assets",
            base_dir / "metadata",
            base_dir / "history",
            base_dir / "logs",
            base_dir / "variants",
        ]
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root in include_paths:
                if not root.exists():
                    continue
                for child in root.rglob("*"):
                    if child.is_file():
                        zf.write(child, child.relative_to(base_dir).as_posix())

        self._register_action_mission(
            action="export_zip",
            objective="Export Published release bundle",
            run_id=datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8],
            model_path=str(model_path),
            output_dir=str(base_dir),
            payload={"zip_path": str(zip_path)},
        )
        return str(zip_path)

    def list_documents(self) -> list[dict[str, Any]]:
        return self.service.list_documents()

    # Stable public facade API (compatibility wrappers)
    def get_document(self, document_model_path: str) -> dict[str, Any]:
        return self.service.get_document(document_model_path)

    def delete_document(self, document_model_path: str) -> bool:
        return self.service.delete_document(document_model_path)

    def duplicate_document(self, document_model_path: str) -> dict[str, Any]:
        return self.service.duplicate_document(document_model_path)

    def save_document(self, document_model_path: str, updates: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.service.save_document(document_model_path, updates or {})

    def open_document(self, document_model_path: str) -> dict[str, Any]:
        return self.service.open_document(document_model_path)

    def generate_html(self, **kwargs: Any) -> dict[str, Any]:
        return self.service.generate_html(**kwargs)

    def preview_document(self, document_model_path: str) -> dict[str, Any]:
        return self.service.preview_document(document_model_path)

    def list_versions(self, document_model_path: str) -> list[dict[str, Any]]:
        return self.service.list_versions(document_model_path)

    def restore_version(self, document_model_path: str, version_number: int) -> dict[str, Any]:
        return self.service.restore_version(document_model_path, version_number)

    def search(self, query: str, limit: int = 200) -> list[dict[str, Any]]:
        return self.service.search(query, limit=limit)

    def statistics(self) -> dict[str, Any]:
        return self.service.statistics()

    def quality_report(self, document_model_path: str) -> dict[str, Any]:
        return self.service.quality_report(document_model_path)

    def save_uploaded_sources(self, files: list[Any] | None) -> list[str]:
        saved_paths: list[str] = []
        if not files:
            return saved_paths
        upload_dir = REPO_ROOT / "reports" / "html_intelligence_studio" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        for uploaded in files:
            target = upload_dir / uploaded.name
            target.write_bytes(uploaded.getbuffer())
            saved_paths.append(str(target))
        return saved_paths

    def read_json(self, path: str | Path, default: Any) -> Any:
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            return default

    def read_mission_history(self, limit: int = 200) -> list[dict[str, Any]]:
        if not MISSION_REGISTRY_PATH.exists() and not MISSION_REGISTRY_FALLBACK.exists():
            return []
        registry = MISSION_REGISTRY_PATH if MISSION_REGISTRY_PATH.exists() else MISSION_REGISTRY_FALLBACK
        rows: list[dict[str, Any]] = []
        for raw in registry.read_text(encoding="utf-8", errors="ignore").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except Exception:
                continue
        return rows[-limit:]

    def build_inline_preview_html(self, html_path: str) -> str:
        path = Path(html_path).expanduser().resolve()
        content = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(content, "html.parser")
        if soup.head is not None:
            for existing_base in soup.head.find_all("base"):
                existing_base.decompose()
            base = soup.new_tag("base", href=path.parent.resolve().as_uri() + "/")
            soup.head.insert(0, base)
            for link in list(soup.head.find_all("link", attrs={"rel": True, "href": True})):
                rel = link.get("rel") or []
                rel_values = [str(r).lower() for r in rel]
                if "stylesheet" not in rel_values:
                    continue
                href = str(link.get("href") or "").strip()
                if href.startswith(("http://", "https://", "data:")):
                    continue
                css_path = (path.parent / href).resolve()
                if css_path.exists():
                    style_tag = soup.new_tag("style")
                    style_tag.string = css_path.read_text(encoding="utf-8", errors="ignore")
                    link.replace_with(style_tag)
        return str(soup)

    def validate_html(self, html_path: str) -> dict[str, Any]:
        html_file = Path(html_path).expanduser().resolve()
        html_text = html_file.read_text(encoding="utf-8")
        soup = BeautifulSoup(html_text, "html.parser")

        has_viewport = soup.find("meta", attrs={"name": "viewport"}) is not None
        has_lang = bool(soup.find("html") and soup.find("html").get("lang"))
        has_dark_css = "prefers-color-scheme" in html_text
        has_print_css = "@media print" in html_text

        assets_ok = True
        broken_assets: list[str] = []
        for img in soup.find_all("img"):
            src = (img.get("src") or "").strip()
            if not src or src.startswith(("http://", "https://", "data:")):
                continue
            candidate = (html_file.parent / src).resolve()
            if not candidate.exists():
                broken_assets.append(src)
                assets_ok = False

        has_title = soup.find("title") is not None
        has_description = soup.find("meta", attrs={"name": "description"}) is not None
        accessibility_signals = sum(
            [
                1 if has_lang else 0,
                1 if all((img.get("alt") or "").strip() for img in soup.find_all("img")) else 0,
                1 if soup.find("main") is not None else 0,
                1 if soup.find("h1") is not None else 0,
            ]
        )

        return {
            "html_valid": bool(soup.find("html") and soup.find("body")),
            "responsive": has_viewport,
            "desktop": True,
            "tablet": has_viewport,
            "mobile": has_viewport,
            "dark_mode": has_dark_css,
            "print_mode": has_print_css,
            "accessibility": round(accessibility_signals / 4, 2),
            "seo": {"title": has_title, "meta_description": has_description},
            "performance": "ok" if len(html_text) < 3_000_000 else "review",
            "assets_integrity": assets_ok,
            "broken_assets": broken_assets,
            "links_integrity": True,
            "graphic_consistency": True,
        }

    def _build_document_from_generic_sources(
        self,
        *,
        document_name: str,
        source_format: str,
        sources: list[str],
        objective: str,
        instruction_text: str,
    ) -> DocumentModel:
        if sources:
            primary = Path(sources[0]).expanduser()
            if primary.exists() and primary.suffix.lower() in {".html", ".htm"}:
                return self._build_from_html(primary, document_name=document_name)
            if primary.exists() and primary.suffix.lower() in {".md", ".txt"}:
                return self._build_from_text(primary, document_name=document_name)

        body = instruction_text.strip() or objective.strip() or "Corporate smart HTML document generated by HIS."
        return DocumentModel(
            title=document_name or "HTML Intelligence Studio Document",
            subtitle="Autonomous mission-driven reconstruction",
            source_path=sources[0] if sources else "free_text",
            source_type=source_format or "mixed",
            sections=[
                SectionNode(
                    title="Executive Overview",
                    summary="Mission-generated executive overview section.",
                    order=1,
                    blocks=[
                        BlockNode(
                            block_type="summary",
                            components=[
                                normalize_component(
                                    "executive_summary",
                                    "Executive Summary",
                                    body,
                                )
                            ],
                        )
                    ],
                )
            ],
            evidence=[EvidenceRecord(kind="instruction", description=body[:250])],
        )

    def _build_from_html(self, source_html: Path, document_name: str) -> DocumentModel:
        soup = BeautifulSoup(source_html.read_text(encoding="utf-8"), "html.parser")
        title = document_name or (soup.title.string.strip() if soup.title and soup.title.string else source_html.stem)
        sections: list[SectionNode] = []
        headings = soup.find_all(["h1", "h2", "h3"])
        if headings:
            for idx, heading in enumerate(headings, start=1):
                content = []
                sibling = heading.find_next_sibling()
                while sibling and sibling.name not in {"h1", "h2", "h3"}:
                    text = sibling.get_text(" ", strip=True)
                    if text:
                        content.append(text)
                    sibling = sibling.find_next_sibling()
                summary = " ".join(content)[:600] if content else "Imported section from source HTML."
                sections.append(
                    SectionNode(
                        title=heading.get_text(" ", strip=True) or f"Section {idx}",
                        summary=summary,
                        order=idx,
                        blocks=[BlockNode(block_type="text", components=[normalize_component("text", "Imported Content", summary)])],
                    )
                )
        else:
            text = soup.get_text(" ", strip=True)[:1500]
            sections.append(
                SectionNode(
                    title="Imported Content",
                    summary=text,
                    order=1,
                    blocks=[BlockNode(block_type="text", components=[normalize_component("text", "Imported HTML", text)])],
                )
            )

        return DocumentModel(
            title=title,
            subtitle="Imported and normalized by HTML Intelligence Studio",
            source_path=str(source_html),
            source_type="html",
            sections=sections,
            evidence=[EvidenceRecord(kind="html_import", description=f"Imported from {source_html.name}")],
        )

    def _build_from_text(self, source_text: Path, document_name: str) -> DocumentModel:
        text = source_text.read_text(encoding="utf-8", errors="ignore")
        chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
        sections: list[SectionNode] = []
        for idx, chunk in enumerate(chunks[:12], start=1):
            lines = [line.strip() for line in chunk.splitlines() if line.strip()]
            sec_title = lines[0][:120] if lines else f"Section {idx}"
            body = "\n".join(lines[1:])[:1200] if len(lines) > 1 else chunk[:1200]
            sections.append(
                SectionNode(
                    title=sec_title,
                    summary=body,
                    order=idx,
                    blocks=[BlockNode(block_type="text", components=[normalize_component("text", sec_title, body)])],
                )
            )

        return DocumentModel(
            title=document_name or source_text.stem,
            subtitle="Imported from text source",
            source_path=str(source_text),
            source_type=source_text.suffix.lower().lstrip("."),
            sections=sections or [
                SectionNode(
                    title="Imported Text",
                    summary=text[:1200],
                    order=1,
                    blocks=[BlockNode(block_type="text", components=[normalize_component("text", "Imported Text", text[:1200])])],
                )
            ],
            evidence=[EvidenceRecord(kind="text_import", description=f"Imported from {source_text.name}")],
        )

    def _persist_document(self, document: DocumentModel, base_root: Path, mission_objective: str) -> dict[str, Any]:
        version_dir = base_root / "version_1"
        paths = {
            "source": version_dir / "source",
            "assets": version_dir / "assets",
            "html": version_dir / "html",
            "versions": version_dir / "versions",
            "metadata": version_dir / "metadata",
            "logs": version_dir / "logs",
        }
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)

        publication_outputs = self.publisher.export_all(document, paths["html"])
        html_path = publication_outputs.get("html", "")
        document.preview_profiles = self.preview_engine.build_profiles(document, html_path)
        preview_manifest_path = self.preview_engine.write_manifest(document, paths["metadata"] / "preview_manifest.json")

        store = DocumentVersionStore(paths["versions"])
        version = VersionEntry(
            version_number=1,
            author="Mission Manager",
            objective=mission_objective,
            result="created",
            mission_id=datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8],
            diff=store.build_diff(None, document),
            output_files=publication_outputs,
        )
        document.version_history.append(version)
        document.mission_links.append(MissionLink(mission_id=version.mission_id, objective=mission_objective))
        store.append_version(document, version)

        model_path = paths["metadata"] / "document_model.json"
        model_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")

        knowledge_package = {
            "document_id": document.id,
            "title": document.title,
            "sections": [s.title for s in document.sections],
            "components": sum(len(b.components) for s in document.sections for b in s.blocks),
            "metadata": document.metadata,
        }
        knowledge_path = paths["metadata"] / "knowledge_package.json"
        knowledge_path.write_text(json.dumps(knowledge_package, indent=2, ensure_ascii=False), encoding="utf-8")

        enterprise_memory = {
            "document_id": document.id,
            "missions": [m.model_dump(mode="json") for m in document.mission_links],
            "versions": [v.model_dump(mode="json") for v in document.version_history],
            "updated_at": datetime.now(UTC).isoformat(),
        }
        memory_path = paths["metadata"] / "enterprise_memory.json"
        memory_path.write_text(json.dumps(enterprise_memory, indent=2, ensure_ascii=False), encoding="utf-8")

        mission_log = {
            "events": [
                {
                    "ts": datetime.now(UTC).isoformat(),
                    "agent": "Mission Manager",
                    "action": "generate_html",
                    "objective": mission_objective,
                    "source": document.source_path,
                }
            ]
        }
        mission_log_path = paths["logs"] / "mission_log.json"
        mission_log_path.write_text(json.dumps(mission_log, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "run_id": version.mission_id,
            "output_dir": str(version_dir),
            "html_path": publication_outputs.get("html", ""),
            "document_model_path": str(model_path),
            "theme_css_path": publication_outputs.get("theme_css", ""),
            "preview_manifest_path": str(preview_manifest_path),
            "knowledge_package_path": str(knowledge_path),
            "enterprise_memory_path": str(memory_path),
            "mission_log_path": str(mission_log_path),
            "publication_outputs": publication_outputs,
        }

    def _enrich_document_metadata(
        self,
        document: DocumentModel,
        *,
        document_name: str,
        project: str,
        client: str,
        category: str,
        language: str,
        comments: str,
        objective: str,
        audience: str,
        source_format: str,
        instruction_text: str,
        strategy: StrategyDecision,
        all_sources: list[str],
        theme_profile: str,
        repository_catalog: dict[str, Any],
    ) -> None:
        palette, typography = self._load_corporate_theme_tokens()
        document.title = document_name or document.title
        document.metadata.update(
            {
                "his_module": "HTML Intelligence Studio",
                "project": project,
                "client": client,
                "category": category,
                "language": language,
                "source_format": source_format,
                "sources": all_sources,
                "repository_catalog": repository_catalog,
                "comments": comments,
                "objective": objective,
                "target_audience": audience,
                "instruction_text": instruction_text,
                "theme_profile": theme_profile,
                "theme_variant": THEME_PROFILE_TO_VARIANT.get(theme_profile, "industrial"),
                "corporate_model": str(self.corporate_model_path),
                "palette": palette,
                "typography": typography,
                "strategy": strategy.__dict__,
                "translations": {
                    "en": {
                        "title": document.title,
                        "subtitle": document.subtitle or "Corporate HTML generated by HTML Intelligence Studio",
                    },
                    "es": {
                        "title": document.title,
                        "subtitle": document.subtitle or "HTML corporativo generado por HTML Intelligence Studio",
                    },
                },
            }
        )

    def _select_strategy(self, source_format: str, sources: list[str], instruction_text: str) -> StrategyDecision:
        normalized = (instruction_text or "").lower()
        source_count = len(sources)
        ext_set = {Path(s).suffix.lower() for s in sources}

        hypotheses: list[dict[str, Any]] = [
            {
                "id": "H1",
                "name": "Structured source-first pipeline",
                "assumption": "Use PPT/Word/PDF if available as primary source for high structural fidelity.",
                "engineering": 8.8,
                "business": 8.4,
                "knowledge": 8.6,
                "risk": 2.3,
            },
            {
                "id": "H2",
                "name": "Prompt-driven generative reconstruction",
                "assumption": "Build directly from instruction text when source quality is low or mixed.",
                "engineering": 7.6,
                "business": 8.9,
                "knowledge": 7.4,
                "risk": 3.5,
            },
            {
                "id": "H3",
                "name": "Hybrid fusion pipeline",
                "assumption": "Fuse multi-source artifacts and instructions with componentized assembly.",
                "engineering": 8.5,
                "business": 8.8,
                "knowledge": 9.0,
                "risk": 2.7,
            },
        ]

        for h in hypotheses:
            if source_count > 1:
                h["engineering"] += 0.2
                h["knowledge"] += 0.3
            if any(ext in {".ppt", ".pptx", ".docx", ".pdf"} for ext in ext_set):
                h["engineering"] += 0.1 if h["id"] != "H2" else -0.2
            if "landing page" in normalized or "white paper" in normalized:
                h["business"] += 0.4
            if "fusion" in normalized or "merge" in normalized or source_count >= 2:
                if h["id"] == "H3":
                    h["business"] += 0.4
                    h["knowledge"] += 0.3

            h["executive_score"] = round((h["engineering"] * 0.4) + (h["business"] * 0.35) + (h["knowledge"] * 0.25) - (h["risk"] * 0.25), 2)

        selected = max(hypotheses, key=lambda x: x["executive_score"])
        strategy_name = {
            "H1": "source_first",
            "H2": "prompt_driven",
            "H3": "hybrid_fusion",
        }[selected["id"]]
        return StrategyDecision(
            strategy=strategy_name,
            executive_score=float(selected["executive_score"]),
            hypotheses=hypotheses,
            selected_hypothesis=selected["id"],
        )

    def _choose_primary_source(self, sources: list[str]) -> Path | None:
        if not sources:
            return None
        weighted = []
        for source in sources:
            path = Path(source).expanduser()
            ext = path.suffix.lower()
            score = {
                ".pptx": 100,
                ".ppt": 95,
                ".docx": 92,
                ".pdf": 90,
                ".md": 82,
                ".html": 80,
                ".htm": 80,
                ".txt": 74,
                ".png": 60,
                ".jpg": 60,
                ".jpeg": 60,
            }.get(ext, 50)
            weighted.append((score, path))
        weighted.sort(key=lambda x: x[0], reverse=True)
        return weighted[0][1]

    def _load_corporate_theme_tokens(self) -> tuple[list[str], dict[str, str]]:
        default_palette = ["#0B1F3A", "#005F8C", "#F2A900", "#F4F6F8"]
        default_typography = {
            "headline": "Montserrat, Segoe UI, Arial, sans-serif",
            "body": "Inter, Segoe UI, Arial, sans-serif",
        }

        if not self.corporate_model_path.exists():
            return default_palette, default_typography

        raw = self.corporate_model_path.read_text(encoding="utf-8", errors="ignore")
        if not raw.strip():
            return default_palette, default_typography

        colors = list(dict.fromkeys(re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}", raw)))[:8]
        fonts = re.findall(r"font-family\s*:\s*([^;]+);", raw, flags=re.IGNORECASE)
        headline = fonts[0].strip() if fonts else default_typography["headline"]
        body = fonts[1].strip() if len(fonts) > 1 else default_typography["body"]

        return (colors or default_palette), {"headline": headline, "body": body}

    def _create_next_version_dir(self, current_version_dir: Path) -> Path:
        parent = current_version_dir.parent
        prefix = "version_"
        numbers: list[int] = []
        for child in parent.iterdir():
            if not child.is_dir():
                continue
            match = re.match(r"version_(\d+)", child.name)
            if match:
                numbers.append(int(match.group(1)))

        next_num = (max(numbers) + 1) if numbers else 1
        return parent / f"{prefix}{next_num}_his_update"

    def _find_heading(self, soup: BeautifulSoup, heading_text: str):
        target = heading_text.strip().lower()
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            if tag.get_text(" ", strip=True).lower() == target:
                return tag
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            if target in tag.get_text(" ", strip=True).lower():
                return tag
        return None

    def _ensure_responsive_meta(self, soup: BeautifulSoup) -> None:
        if not soup.find("meta", attrs={"name": "viewport"}):
            meta = soup.new_tag("meta")
            meta["name"] = "viewport"
            meta["content"] = "width=device-width, initial-scale=1"
            if soup.head:
                soup.head.append(meta)

    def _ensure_print_dark_styles(self, soup: BeautifulSoup) -> None:
        style_id = "his-runtime-style"
        existing = soup.find("style", attrs={"id": style_id})
        css = """
@media (prefers-color-scheme: dark) {
  body { background:#111; color:#f4f4f4; }
  img { opacity:0.98; }
}
@media print {
  .his-managed-image { break-inside: avoid; }
  body { background:#fff !important; color:#111 !important; }
}
""".strip()
        if existing:
            existing.string = css
            return
        style = soup.new_tag("style", attrs={"id": style_id})
        style.string = css
        if soup.head:
            soup.head.append(style)

    def _update_hub_and_memory(self, mission_payload: dict[str, Any]) -> None:
        kh_dir = REPO_ROOT / "knowledge_hub" / "outputs" / "html_intelligence_studio"
        kh_dir.mkdir(parents=True, exist_ok=True)
        kh_file = kh_dir / "his_missions.json"

        memory_dir = REPO_ROOT / "data" / "knowledge_memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        memory_file = memory_dir / "html_intelligence_studio_memory.json"

        self._append_json_array(kh_file, mission_payload)
        self._append_json_array(memory_file, mission_payload)

    def _append_json_array(self, path: Path, payload: dict[str, Any]) -> None:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    data = []
            except Exception:
                data = []
        else:
            data = []
        data.append(payload)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _write_his_registry(self, base_root: Path, document: DocumentModel, strategy: StrategyDecision) -> None:
        registry_dir = base_root / "metadata"
        registry_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now(UTC).isoformat(),
            "document_id": document.id,
            "title": document.title,
            "strategy": strategy.__dict__,
            "missions": [m.model_dump(mode="json") for m in document.mission_links],
            "versions": [v.model_dump(mode="json") for v in document.version_history],
        }
        (registry_dir / "his_registry.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _register_action_mission(
        self,
        *,
        action: str,
        objective: str,
        run_id: str,
        model_path: str,
        output_dir: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        row = {
            "ts": datetime.now(UTC).isoformat(),
            "action": action,
            "objective": objective,
            "run_id": run_id,
            "document_model_path": model_path,
            "output_dir": output_dir,
            "payload": payload or {},
        }
        MISSION_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(row, ensure_ascii=False) + "\n"
        try:
            with MISSION_REGISTRY_PATH.open("a", encoding="utf-8") as f:
                f.write(serialized)
        except OSError:
            with MISSION_REGISTRY_FALLBACK.open("a", encoding="utf-8") as f:
                f.write(serialized)

    def _slug(self, value: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
        clean = re.sub(r"_+", "_", clean).strip("_")
        return clean or "general"
