from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ElementStyle:
    font_name: str | None = None
    font_size_pt: float | None = None
    bold: bool | None = None
    italic: bool | None = None
    color: str | None = None
    align: str | None = None


@dataclass
class SlideElement:
    element_id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    text: str = ""
    style: ElementStyle = field(default_factory=ElementStyle)
    asset_path: str | None = None
    table_rows: list[list[str]] = field(default_factory=list)
    chart: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SlideAnalysis:
    index: int
    title: str
    width: float
    height: float
    background: str | None
    layout: str
    palette: list[str]
    elements: list[SlideElement] = field(default_factory=list)
    visual_hierarchy: list[str] = field(default_factory=list)


@dataclass
class PresentationAnalysis:
    source_path: str
    slide_count: int
    global_palette: list[str]
    typography: dict[str, Any]
    slides: list[SlideAnalysis] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hypothesis:
    key: str
    strategy: str
    confidence: float
    impact: float
    effort: float
    risk_inverse: float
    notes: str


@dataclass
class DecisionRecord:
    uncertainty: str
    selected_hypothesis: Hypothesis
    score: float


@dataclass
class PieRunResult:
    run_id: str
    output_dir: str
    source_file: str
    version_1_html: str
    version_2_html: str
    corporate_css: str
    assets_dir: str
    theme_file: str
    technical_report: str
    differences_report: str
    components_matrix: str
    evidence_file: str
    knowledge_hub_file: str
    enterprise_memory_file: str
    decisions_file: str
    mission_log_file: str
