from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from backoffice.pie.hypothesis_engine import resolve_uncertainty
from backoffice.pie.models import Hypothesis
from backoffice.pie.powerpoint_parser import PowerPointParser
from tools.report_publication_guard import get_isolated_workspace

from .component_library import infer_component_kind, normalize_component
from .models import AssetRef, BlockNode, DipcRunResult, DocumentModel, EvidenceRecord, KnowledgeLink, MissionLink, SectionNode, StyleTokenRef, VersionEntry
from .preview_engine import PreviewEngine
from .publication_engine import PublicationEngine
from .theme_engine import build_css
from .versioning import DocumentVersionStore


class DocumentIntelligencePublishingCenter:
    def __init__(self) -> None:
        self.log: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.publisher = PublicationEngine()
        self.preview = PreviewEngine()

    def build_from_powerpoint(self, source_pptx: str, output_root: str = "reports/dipc", author: str = "Mission Manager") -> DipcRunResult:
        source = Path(source_pptx).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)

        run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
        run_dir = Path(output_root).resolve() / run_id
        assets_dir = run_dir / "assets"
        model_dir = run_dir / "model"
        publish_dir = run_dir / "published"
        for path in [assets_dir, model_dir, publish_dir]:
            path.mkdir(parents=True, exist_ok=True)

        self._log("Mission Manager", "DIPC build mission started", {"source": str(source), "run_id": run_id})
        parser = PowerPointParser()
        analysis = parser.parse(str(source), str(assets_dir))
        palette = analysis.global_palette or ["#FF6A00", "#0D0F13", "#F2F3F5"]

        workspace_dir = get_isolated_workspace(Path.cwd(), "dipc", "document_intelligence_publishing_center")
        self._log("Publication Engine", "Using isolated workspace", {"workspace": str(workspace_dir)})

        document = self._build_document_model(analysis, source)
        document.metadata["palette"] = palette
        document.metadata["workspace_dir"] = str(workspace_dir)
        document.styles = [StyleTokenRef(token=f"palette.{idx}", value=color, group="palette") for idx, color in enumerate(palette)]

        theme_css = build_css(document.theme_variant, palette)
        theme_css_path = run_dir / "dipc_theme.css"
        theme_css_path.write_text(theme_css, encoding="utf-8")

        publication_outputs = self.publisher.export_all(document, publish_dir)
        document.preview_profiles = self.preview.build_profiles(document, publication_outputs["html"])
        preview_manifest_path = self.preview.write_manifest(document, run_dir / "preview_manifest.json")

        store = DocumentVersionStore(run_dir / "history")
        version = VersionEntry(
            version_number=1,
            author=author,
            objective="Initial DIPC reconstruction from PowerPoint",
            result="created",
            mission_id=run_id,
            diff=store.build_diff(None, document),
            output_files=publication_outputs,
        )
        document.version_history.append(version)
        document.mission_links.append(MissionLink(mission_id=run_id, objective=version.objective))
        store.append_version(document, version)

        document_model_path = model_dir / "document_model.json"
        document_model_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")

        knowledge_path = run_dir / "knowledge_package.json"
        knowledge_path.write_text(self._build_knowledge_package(document), encoding="utf-8")
        memory_path = run_dir / "enterprise_memory.json"
        memory_path.write_text(self._build_enterprise_memory(document), encoding="utf-8")
        mission_log_path = run_dir / "mission_log.json"
        mission_log_path.write_text(json.dumps(self.log, indent=2, ensure_ascii=False), encoding="utf-8")

        return DipcRunResult(
            run_id=run_id,
            output_dir=str(run_dir),
            document_model_path=str(document_model_path),
            theme_css_path=str(theme_css_path),
            preview_manifest_path=str(preview_manifest_path),
            mission_log_path=str(mission_log_path),
            knowledge_package_path=str(knowledge_path),
            enterprise_memory_path=str(memory_path),
            publication_outputs=publication_outputs,
        )

    def apply_mission(self, document_model_path: str, command: str, output_root: str | None = None, author: str = "AI Coordinator") -> DipcRunResult:
        model_path = Path(document_model_path).resolve()
        document = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        base_dir = model_path.parents[1] if output_root is None else Path(output_root).resolve()
        mission_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]

        previous_document = copy.deepcopy(document)
        previous_html_path = Path(document.version_history[-1].output_files.get("html", "")) if document.version_history else None
        previous_html = previous_html_path.read_text(encoding="utf-8") if previous_html_path and previous_html_path.exists() else ""

        self._log("Mission Manager", "Command mission started", {"mission_id": mission_id, "command": command})
        document = self._transform_document(document, command, mission_id)

        publish_dir = base_dir / "published" / mission_id
        publication_outputs = self.publisher.export_all(document, publish_dir)
        current_html = Path(publication_outputs["html"]).read_text(encoding="utf-8")
        document.preview_profiles = self.preview.build_profiles(document, publication_outputs["html"])
        preview_manifest_path = self.preview.write_manifest(document, base_dir / f"preview_manifest_{mission_id}.json")

        store = DocumentVersionStore(base_dir / "history")
        version_number = len(document.version_history) + 1
        version = VersionEntry(
            version_number=version_number,
            author=author,
            objective=command,
            result="updated",
            mission_id=mission_id,
            diff=store.build_diff(previous_document, document, previous_html, current_html),
            output_files=publication_outputs,
        )
        document.version_history.append(version)
        document.mission_links.append(MissionLink(mission_id=mission_id, objective=command, command=command))
        store.append_version(document, version)

        model_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")
        knowledge_path = base_dir / f"knowledge_package_{mission_id}.json"
        knowledge_path.write_text(self._build_knowledge_package(document), encoding="utf-8")
        memory_path = base_dir / f"enterprise_memory_{mission_id}.json"
        memory_path.write_text(self._build_enterprise_memory(document), encoding="utf-8")
        mission_log_path = base_dir / f"mission_log_{mission_id}.json"
        mission_log_path.write_text(json.dumps(self.log, indent=2, ensure_ascii=False), encoding="utf-8")

        return DipcRunResult(
            run_id=mission_id,
            output_dir=str(base_dir),
            document_model_path=str(model_path),
            theme_css_path=publication_outputs["theme_css"],
            preview_manifest_path=str(preview_manifest_path),
            mission_log_path=str(mission_log_path),
            knowledge_package_path=str(knowledge_path),
            enterprise_memory_path=str(memory_path),
            publication_outputs=publication_outputs,
        )

    def _build_document_model(self, analysis: Any, source: Path) -> DocumentModel:
        title = analysis.slides[0].title if analysis.slides else source.stem
        subtitle = f"DIPC Smart HTML V2 reconstruction from {source.name}"
        sections: list[SectionNode] = []
        assets: list[AssetRef] = []
        evidence: list[EvidenceRecord] = []
        knowledge_links: list[KnowledgeLink] = []

        for slide in analysis.slides:
            items: list[dict[str, Any]] = []
            kpis: list[dict[str, Any]] = []
            tables: list[list[str]] | None = None
            for element in slide.elements:
                body = (element.text or "").strip()
                if body:
                    items.append({"title": element.kind.title(), "body": body})
                    evidence.append(EvidenceRecord(kind="slide_text", description=body[:240], metadata={"slide": slide.index, "element": element.element_id}))
                if element.asset_path:
                    assets.append(AssetRef(kind="image", path=element.asset_path, title=slide.title))
                if element.table_rows:
                    tables = element.table_rows
                if element.kind in {"heading", "title"} and body:
                    kpis.append({"label": body[:40], "value": slide.index, "detail": slide.layout})

            section_title = slide.title or f"Slide {slide.index}"
            section_kind = infer_component_kind(section_title, " ".join(item["body"] for item in items), fallback="text")
            blocks = [
                BlockNode(
                    block_type="primary",
                    title=section_title,
                    components=[normalize_component("hero" if slide.index == 1 else section_kind, section_title, slide.title, items=items, props={"layout": slide.layout})],
                )
            ]
            if tables:
                blocks.append(BlockNode(block_type="table", title="Data", components=[normalize_component("comparison_table", "Data Table", None, props={"rows": tables})]))
            if kpis:
                blocks.append(BlockNode(block_type="kpi", title="KPIs", components=[normalize_component("industrial_kpi", "Industrial KPI", None, items=kpis[:4])]))

            sections.append(SectionNode(title=section_title, summary=f"Layout: {slide.layout}", order=slide.index, blocks=blocks, metadata={"visual_hierarchy": slide.visual_hierarchy}))
            knowledge_links.append(KnowledgeLink(key=f"slide:{slide.index}", value=section_title, category="layout", metadata={"layout": slide.layout}))

        sections.append(
            SectionNode(
                title="Conclusions",
                summary="Generated by DIPC as a reusable executive closure.",
                order=len(sections) + 1,
                blocks=[
                    BlockNode(block_type="conclusion", components=[normalize_component("executive_summary", "Corporate Conclusion", "This reconstructed document is ready for reuse across publishing targets.")]),
                    BlockNode(block_type="contact", components=[normalize_component("contact_block", "INGECART Contact", "Document Intelligence & Publishing Center · IS_BACKOFFICE")]),
                    BlockNode(block_type="footer", components=[normalize_component("footer", "Footer", "Generated by DIPC mission pipeline.")]),
                ],
            )
        )

        return DocumentModel(
            title=title,
            subtitle=subtitle,
            source_path=str(source),
            source_type="pptx",
            metadata={"slide_count": analysis.slide_count, "palette": analysis.global_palette, "typography": analysis.typography},
            sections=sections,
            assets=assets,
            evidence=evidence,
            knowledge_links=knowledge_links,
        )

    def _transform_document(self, document: DocumentModel, command: str, mission_id: str) -> DocumentModel:
        normalized = command.lower().strip()
        decision = resolve_uncertainty(
            f"How to apply command: {command}",
            [
                Hypothesis("H1", "Apply conservative executive rewrite preserving structure", 8.9, 8.5, 8.6, 8.4, "Balanced transformation."),
                Hypothesis("H2", "Aggressive restructure and shorten narrative", 7.8, 8.8, 7.2, 7.0, "Higher impact, more risk."),
                Hypothesis("H3", "Add component overlays while keeping original text", 8.3, 8.1, 8.0, 8.6, "Improves visualization."),
            ],
        )
        self.decisions.append({"mission_id": mission_id, "command": command, "decision": decision.selected_hypothesis.key, "score": decision.score})

        if "resume" in normalized or "reduce" in normalized:
            for section in document.sections:
                if section.summary and len(section.summary) > 120:
                    section.summary = section.summary[:117] + "..."
                for block in section.blocks:
                    for component in block.components:
                        if component.body and len(component.body) > 260:
                            component.body = component.body[:257] + "..."
                        for item in component.items:
                            body = str(item.get("body", ""))
                            if len(body) > 140:
                                item["body"] = body[:137] + "..."

        if "ejecutivo" in normalized or "executive" in normalized:
            document.document_type = "executive_report"
            summary = SectionNode(
                title="Executive Summary",
                summary="Generated from a mission-driven executive reframing.",
                order=1,
                blocks=[BlockNode(block_type="summary", components=[normalize_component("executive_summary", "Executive Summary", "This version prioritizes decisions, impact, and measurable business value.")])],
            )
            document.sections = [summary] + [self._reorder_section(section, idx + 2) for idx, section in enumerate(document.sections)]

        if "más técnico" in normalized or "more technical" in normalized or "manual" in normalized:
            document.document_type = "technical_manual"
            for section in document.sections:
                section.blocks.append(BlockNode(block_type="specification", components=[normalize_component("technical_specification", "Technical Specification", None, items=[{"title": section.title, "body": section.summary or "Technical section summary"}])]))

        if "añade gráficos" in normalized or "add charts" in normalized or "dashboard" in normalized:
            dashboard = SectionNode(
                title="Executive Dashboard",
                summary="Auto-generated KPI dashboard from mission command.",
                order=len(document.sections) + 1,
                blocks=[BlockNode(block_type="dashboard", components=[normalize_component("executive_dashboard", "Executive Dashboard", None, items=[{"label": "Sections", "value": len(document.sections), "detail": "Structured chapters"}, {"label": "Components", "value": sum(len(b.components) for s in document.sections for b in s.blocks), "detail": "Reusable blocks"}, {"label": "Assets", "value": len(document.assets), "detail": "Managed visual assets"}, {"label": "Missions", "value": len(document.mission_links) + 1, "detail": "Tracked mission executions"}])])],
            )
            document.sections.append(dashboard)
            self._reindex_sections(document)

        if "índice" in normalized or "index" in normalized:
            document.metadata["index_generated"] = True

        if "landing page" in normalized or "white paper" in normalized or "propuesta" in normalized or "proposal" in normalized:
            document.document_type = "landing_page" if "landing" in normalized else "white_paper"
            document.theme_variant = "light" if "landing" in normalized else document.theme_variant
            document.subtitle = f"Mission-transformed as {document.document_type.replace('_', ' ')}"

        if "conclusiones" in normalized or "conclusions" in normalized:
            document.sections.append(SectionNode(title="Mission Conclusions", summary="Added automatically by mission command.", order=len(document.sections) + 1, blocks=[BlockNode(block_type="conclusion", components=[normalize_component("executive_summary", "Mission Conclusion", "The document now includes a dedicated conclusion section aligned to the requested transformation.")])]))
            self._reindex_sections(document)

        document.metadata["last_command"] = command
        return document

    def _reorder_section(self, section: SectionNode, order: int) -> SectionNode:
        section.order = order
        return section

    def _reindex_sections(self, document: DocumentModel) -> None:
        for idx, section in enumerate(document.sections, start=1):
            section.order = idx

    def _build_knowledge_package(self, document: DocumentModel) -> str:
        payload = {
            "document_id": document.id,
            "title": document.title,
            "components": [component.model_dump(mode="json") for section in document.sections for block in section.blocks for component in block.components],
            "layouts": [link.model_dump(mode="json") for link in document.knowledge_links],
            "palette": document.metadata.get("palette", []),
            "patterns": sorted({component.component_kind for section in document.sections for block in section.blocks for component in block.components}),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _build_enterprise_memory(self, document: DocumentModel) -> str:
        payload = {
            "document_id": document.id,
            "source_path": document.source_path,
            "document_type": document.document_type,
            "missions": [mission.model_dump(mode="json") for mission in document.mission_links],
            "versions": [version.model_dump(mode="json") for version in document.version_history],
            "evidence_count": len(document.evidence),
            "knowledge_link_count": len(document.knowledge_links),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _log(self, agent: str, action: str, payload: dict[str, Any] | None = None) -> None:
        self.log.append({"ts": datetime.now(UTC).isoformat(), "agent": agent, "action": action, "payload": payload or {}})
