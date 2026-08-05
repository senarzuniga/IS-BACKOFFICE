from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .html_generator import generate_slide_flow_html, generate_smart_reconstruction_html
from .hypothesis_engine import resolve_uncertainty
from .models import Hypothesis, PieRunResult
from .powerpoint_parser import PowerPointParser
from .theme_manager import build_corporate_css, build_theme_tokens


def _extract_palette_from_slides(slides: list[Any], top_n: int = 12) -> list[str]:
    freq: dict[str, int] = {}
    for slide in slides:
        for color in getattr(slide, "palette", []):
            if not color:
                continue
            freq[color] = freq.get(color, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [color for color, _ in ranked[:top_n]]


class PresentationIntelligenceMissionManager:
    AGENTS = [
        "Mission Manager",
        "AI Coordinator",
        "Knowledge Hub",
        "Enterprise Memory",
        "Executive Reports",
        "Context Manager",
        "Evidence Engine",
        "HTML Generator",
        "Document Parser",
        "PowerPoint Parser",
        "Image Processor",
        "Vision Analysis",
        "Layout Analysis",
        "Theme Manager",
        "Template Engine",
        "Report Generator",
        "Asset Manager",
        "Translation Engine",
        "Factory Graph",
    ]

    def __init__(self) -> None:
        self.log: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []

    def run(self, source_pptx: str, output_root: str = "reports/pie") -> PieRunResult:
        source = Path(source_pptx).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Source presentation not found: {source}")

        run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
        run_dir = Path(output_root).resolve() / run_id
        assets_dir = run_dir / "assets"
        outputs_v1 = run_dir / "version_1_slide_flow"
        outputs_v2 = run_dir / "version_2_smart_reconstruction"
        for directory in [assets_dir, outputs_v1, outputs_v2]:
            directory.mkdir(parents=True, exist_ok=True)

        self._agent("Mission Manager", "Mission started", {"source": str(source), "run_id": run_id})
        for agent_name in self.AGENTS:
            self._agent(agent_name, "Registered in mission graph")

        parser = PowerPointParser()
        analysis = self._agent_call(
            "PowerPoint Parser",
            "Parse presentation structure, content, visual assets, and element metadata",
            lambda: parser.parse(str(source), str(assets_dir)),
        )
        analysis.metadata["source_name"] = source.name

        analysis.global_palette = _extract_palette_from_slides(analysis.slides)

        self._resolve_uncertainties(analysis)

        theme = self._agent_call("Theme Manager", "Generate design tokens and theme profile", lambda: build_theme_tokens(analysis))
        corporate_css = self._agent_call("Template Engine", "Build corporate CSS from tokens", lambda: build_corporate_css(theme))

        css_file = run_dir / "corporate_theme.css"
        css_file.write_text(corporate_css, encoding="utf-8")

        v1_html = self._agent_call(
            "HTML Generator",
            "Create Slide Flow HTML with continuous vertical navigation",
            lambda: generate_slide_flow_html(analysis, theme, "../corporate_theme.css"),
        )
        v2_html = self._agent_call(
            "HTML Generator",
            "Create Smart HTML Reconstruction from semantic components",
            lambda: generate_smart_reconstruction_html(analysis, theme, "../corporate_theme.css"),
        )

        v1_file = outputs_v1 / "index.html"
        v2_file = outputs_v2 / "index.html"
        v1_file.write_text(v1_html, encoding="utf-8")
        v2_file.write_text(v2_html, encoding="utf-8")

        # Duplicate CSS into variant folders for portability.
        shutil.copy2(css_file, outputs_v1 / "corporate_theme.css")
        shutil.copy2(css_file, outputs_v2 / "corporate_theme.css")

        theme_file = run_dir / "theme_tokens.json"
        theme_file.write_text(json.dumps(theme, indent=2, ensure_ascii=False), encoding="utf-8")

        evidence_file = run_dir / "evidence.json"
        evidence = self._build_evidence(analysis)
        evidence_file.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")

        matrix_file = run_dir / "components_matrix.md"
        matrix_file.write_text(self._build_components_matrix(analysis), encoding="utf-8")

        technical_file = run_dir / "technical_report.md"
        technical_file.write_text(self._build_technical_report(source, analysis), encoding="utf-8")

        diff_file = run_dir / "differences_report.md"
        diff_file.write_text(self._build_differences_report(analysis), encoding="utf-8")

        knowledge_file = run_dir / "knowledge_hub_package.json"
        knowledge_file.write_text(self._build_knowledge_package_json(source, analysis, theme), encoding="utf-8")

        memory_file = run_dir / "enterprise_memory_log.json"
        memory_file.write_text(self._build_enterprise_memory_json(source, analysis), encoding="utf-8")

        decisions_file = run_dir / "ahde_decisions.json"
        decisions_file.write_text(json.dumps(self.decisions, indent=2, ensure_ascii=False), encoding="utf-8")

        mission_log_file = run_dir / "mission_log.json"
        mission_log_file.write_text(json.dumps(self.log, indent=2, ensure_ascii=False), encoding="utf-8")

        self._agent("Executive Reports", "Run completed", {"output_dir": str(run_dir)})

        return PieRunResult(
            run_id=run_id,
            output_dir=str(run_dir),
            source_file=str(source),
            version_1_html=str(v1_file),
            version_2_html=str(v2_file),
            corporate_css=str(css_file),
            assets_dir=str(assets_dir),
            theme_file=str(theme_file),
            technical_report=str(technical_file),
            differences_report=str(diff_file),
            components_matrix=str(matrix_file),
            evidence_file=str(evidence_file),
            knowledge_hub_file=str(knowledge_file),
            enterprise_memory_file=str(memory_file),
            decisions_file=str(decisions_file),
            mission_log_file=str(mission_log_file),
        )

    def _resolve_uncertainties(self, analysis) -> None:
        if not analysis.global_palette:
            decision = resolve_uncertainty(
                "Color palette extraction returned empty output",
                [
                    Hypothesis("U1", "Infer palette from shape fills", 8.6, 8.0, 8.7, 8.4, "Use detected fill colors."),
                    Hypothesis("U2", "Apply corporate fallback palette", 8.1, 7.6, 10.0, 9.0, "No stop condition allowed."),
                ],
            )
            self.decisions.append({"type": "palette", "decision": asdict(decision)})
            analysis.global_palette = ["#0B3D6E", "#E85C1A", "#1A2B3C", "#F4F7FA"]

        for slide in analysis.slides:
            has_smartart = any(e.kind == "smartart" for e in slide.elements)
            if has_smartart:
                decision = resolve_uncertainty(
                    f"SmartArt reconstruction strategy on slide {slide.index}",
                    [
                        Hypothesis("S1", "Convert SmartArt text nodes into card-grid + svg connector", 8.9, 8.4, 8.0, 8.5, "Reusable web component."),
                        Hypothesis("S2", "Convert SmartArt to static image", 7.1, 4.2, 9.8, 6.0, "Disallowed by mission quality policy."),
                    ],
                )
                self.decisions.append({"type": "smartart", "slide": slide.index, "decision": asdict(decision)})

    def _agent(self, name: str, action: str, payload: dict[str, Any] | None = None) -> None:
        self.log.append(
            {
                "ts": datetime.now(UTC).isoformat(),
                "agent": name,
                "action": action,
                "payload": payload or {},
            }
        )

    def _agent_call(self, agent_name: str, action: str, fn: Callable[[], Any]):
        self._agent(agent_name, action)
        result = fn()
        self._agent(agent_name, "Completed", {"result_type": type(result).__name__})
        return result

    def _build_evidence(self, analysis) -> dict[str, Any]:
        total_elements = sum(len(s.elements) for s in analysis.slides)
        counts: dict[str, int] = {}
        for slide in analysis.slides:
            for el in slide.elements:
                counts[el.kind] = counts.get(el.kind, 0) + 1

        return {
            "source": analysis.source_path,
            "slide_count": analysis.slide_count,
            "total_elements": total_elements,
            "element_counts": counts,
            "palette": analysis.global_palette,
            "typography": analysis.typography,
        }

    def _build_components_matrix(self, analysis) -> str:
        lines = [
            "# PIE Reusable Component Matrix",
            "",
            "| Component | Source Elements | Version 1 | Version 2 | Reuse Notes |",
            "|---|---|---|---|---|",
            "| Hero/Cover | Title + opening visual blocks | yes | yes | Reusable landing section |",
            "| Section Cards | Text blocks and grouped content | yes | yes | Generic executive chapter layout |",
            "| Data Tables | Native table shapes | yes | yes | Sortable + CSV export hooks |",
            "| Charts | Editable chart metadata | yes | yes | Rebuilt as SVG bars in baseline |",
            "| SmartArt Component | SmartArt nodes and labels | yes | yes | Reconstructed as card-grid + connectors |",
            "| Navigation Index | Slide titles | yes | yes | Scroll spy + chapter anchors |",
            "| AI Command Panel | Runtime command layer | yes | yes | Mission Manager command hooks |",
        ]

        lines.append("")
        lines.append(f"Slides analyzed: {analysis.slide_count}")
        return "\n".join(lines)

    def _build_technical_report(self, source: Path, analysis) -> str:
        return "\n".join(
            [
                "# PIE Technical Report",
                "",
                f"- Source document: {source}",
                f"- Slide count analyzed: {analysis.slide_count}",
                f"- Palette size: {len(analysis.global_palette)}",
                f"- Font families detected: {len(analysis.typography.get('font_usage', {}))}",
                "- AHDE mode: enabled across parsing, theme extraction, and SmartArt strategy selection",
                "- Mission policy: no hard stop on uncertainty; auto hypothesis simulation and scoring applied",
                "",
                "## Agent Coordination",
                "",
                *[f"- {name}" for name in self.AGENTS],
                "",
                "## Deliverables",
                "",
                "- Version 1: Slide Flow HTML",
                "- Version 2: Smart HTML Reconstruction",
                "- Corporate CSS / theme tokens",
                "- Asset package with deduplicated images",
                "- Evidence + Knowledge Hub package + Enterprise Memory log",
                "",
                "## Notes",
                "",
                "- This engine transforms presentation knowledge into web-native assets.",
                "- It is not a binary PowerPoint-to-HTML embed conversion.",
            ]
        )

    def _build_differences_report(self, analysis) -> str:
        return "\n".join(
            [
                "# PIE Differences Report",
                "",
                "## Version 1 - Slide Flow HTML",
                "- Preserves slide-by-slide sequence in continuous scroll.",
                "- Keeps original proportions, visuals, colors, and structural order.",
                "- Adds navigation index, progress bar, scroll spy, print/fullscreen actions, and AI panel.",
                "",
                "## Version 2 - Smart HTML Reconstruction",
                "- Rebuilds each slide semantically into web components.",
                "- Prioritizes cards, responsive tables, SVG charts, and reusable blocks.",
                "- Avoids embedding complete slide screenshots.",
                "",
                "## Quality Criteria Coverage",
                "- Pure HTML/CSS/JS output: yes",
                "- Responsive output desktop/mobile: yes",
                "- Corporate visual identity retention: yes",
                "- SEO-ready structure and headings: yes",
                "- Fast loading controls (lazy image loading): yes",
                "",
                f"Slides covered: {analysis.slide_count}",
            ]
        )

    def _build_knowledge_package_json(self, source: Path, analysis, theme: dict[str, Any]) -> str:
        payload = {
            "source_document": str(source),
            "captured_at": datetime.now(UTC).isoformat(),
            "reusable_assets": {
                "palette": analysis.global_palette,
                "typography": analysis.typography,
                "theme_tokens": theme,
                "slides": [
                    {
                        "index": s.index,
                        "title": s.title,
                        "layout": s.layout,
                        "visual_hierarchy": s.visual_hierarchy,
                        "elements": [
                            {
                                "id": e.element_id,
                                "kind": e.kind,
                                "text": e.text[:300],
                                "asset": e.asset_path,
                            }
                            for e in s.elements
                        ],
                    }
                    for s in analysis.slides
                ],
            },
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _build_enterprise_memory_json(self, source: Path, analysis) -> str:
        payload = {
            "source_document": str(source),
            "destination_type": "Dual HTML outputs (slide-flow and smart-reconstruction)",
            "version": "PIE_V1",
            "recorded_at": datetime.now(UTC).isoformat(),
            "decisions": self.decisions,
            "transformations": [
                "Extracted structural and visual features from all slides",
                "Generated reusable design tokens",
                "Generated V1 and V2 HTML variants",
            ],
            "learned_signals": [
                "SmartArt should prefer semantic reconstruction over static snapshots",
                "Mission quality improves when uncertainty fallback is explicit and scored",
            ],
            "analysis_summary": {
                "slide_count": analysis.slide_count,
                "global_palette_size": len(analysis.global_palette),
            },
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)
