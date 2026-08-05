from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


ComponentKind = Literal[
    "executive_header",
    "hero",
    "section_header",
    "executive_summary",
    "feature_cards",
    "comparison_table",
    "industrial_kpi",
    "timeline",
    "gantt",
    "mission_cards",
    "digital_twin_panel",
    "factory_layout",
    "architecture_diagram",
    "technology_comparison",
    "risk_matrix",
    "executive_dashboard",
    "technical_specification",
    "engineering_drawing_viewer",
    "amr_fleet_panel",
    "ingetrans_panel",
    "maintenance_report",
    "business_case",
    "roi_summary",
    "project_roadmap",
    "contact_block",
    "footer",
    "process_flow",
    "sipoc",
    "bpmn_simplified",
    "swimlane",
    "pyramid",
    "cycle",
    "matrix",
    "relationship",
    "chevron",
    "hierarchy",
    "org_chart",
    "tree",
    "venn",
    "circular_diagram",
    "industrial_blocks",
    "plant_layout",
    "electrical_diagram",
    "mechanical_diagram",
    "material_flow_diagram",
    "infographic",
    "table",
    "text",
    "image_gallery",
]


ThemeVariant = Literal["industrial", "light", "dark", "high_contrast"]
PreviewDevice = Literal["desktop", "tablet", "mobile", "ultrawide", "print", "pdf"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return uuid4().hex


class AssetRef(BaseModel):
    id: str = Field(default_factory=_uuid)
    kind: str
    path: str
    title: str | None = None
    checksum: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StyleTokenRef(BaseModel):
    token: str
    value: str
    group: str


class EvidenceRecord(BaseModel):
    id: str = Field(default_factory=_uuid)
    kind: str
    description: str
    source_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeLink(BaseModel):
    key: str
    value: str
    category: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MissionLink(BaseModel):
    mission_id: str
    objective: str
    command: str | None = None
    status: str = "completed"
    agent: str = "Mission Manager"
    confidence: float = 1.0


class ComponentNode(BaseModel):
    id: str = Field(default_factory=_uuid)
    component_kind: ComponentKind
    title: str | None = None
    body: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    props: dict[str, Any] = Field(default_factory=dict)
    asset_ids: list[str] = Field(default_factory=list)
    style_tokens: list[StyleTokenRef] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    knowledge_keys: list[str] = Field(default_factory=list)
    semantic_labels: list[str] = Field(default_factory=list)
    confidence: float = 1.0


class BlockNode(BaseModel):
    id: str = Field(default_factory=_uuid)
    block_type: str
    title: str | None = None
    components: list[ComponentNode] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SectionNode(BaseModel):
    id: str = Field(default_factory=_uuid)
    title: str
    summary: str | None = None
    order: int
    blocks: list[BlockNode] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentDiff(BaseModel):
    structural_diff: dict[str, Any] = Field(default_factory=dict)
    visual_diff: dict[str, Any] = Field(default_factory=dict)
    semantic_diff: dict[str, Any] = Field(default_factory=dict)
    html_diff: list[str] = Field(default_factory=list)
    component_diff: dict[str, Any] = Field(default_factory=dict)
    change_log: list[dict[str, Any]] = Field(default_factory=list)


class VersionEntry(BaseModel):
    version_id: str = Field(default_factory=_uuid)
    version_number: int
    author: str
    objective: str
    result: str
    mission_id: str
    created_at: datetime = Field(default_factory=_now)
    diff: DocumentDiff = Field(default_factory=DocumentDiff)
    output_files: dict[str, str] = Field(default_factory=dict)


class PreviewProfile(BaseModel):
    device: PreviewDevice
    width_px: int
    height_px: int
    theme: ThemeVariant
    html_path: str | None = None


class AnalyzerReport(BaseModel):
    accessibility_score: float = 0.0
    performance_score: float = 0.0
    seo_score: float = 0.0
    responsive_score: float = 0.0
    notes: list[str] = Field(default_factory=list)


class KnowledgeGraphNode(BaseModel):
    id: str = Field(default_factory=_uuid)
    node_type: str
    label: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityScore(BaseModel):
    visual_fidelity: float = 0.0
    structural_fidelity: float = 0.0
    semantic_fidelity: float = 0.0
    accessibility: float = 0.0
    responsive: float = 0.0
    load_time: float = 0.0
    complexity: float = 0.0
    reusability: float = 0.0
    maintainability: float = 0.0
    graphical_consistency: float = 0.0
    typography_quality: float = 0.0
    alignment_quality: float = 0.0
    component_usage: float = 0.0
    executive_quality_score: float = 0.0


class LiveDocumentState(BaseModel):
    toc_generated: bool = False
    navigation_generated: bool = False
    preview_regenerated: bool = False
    styles_regenerated: bool = False
    cross_refs_updated: bool = False
    knowledge_graph_updated: bool = False
    metadata_updated: bool = False
    affected_component_ids: list[str] = Field(default_factory=list)


class DocumentModel(BaseModel):
    id: str = Field(default_factory=_uuid)
    title: str
    subtitle: str | None = None
    source_path: str
    source_type: str
    document_type: str = "smart_html_v2"
    theme_variant: ThemeVariant = "industrial"
    metadata: dict[str, Any] = Field(default_factory=dict)
    sections: list[SectionNode] = Field(default_factory=list)
    assets: list[AssetRef] = Field(default_factory=list)
    styles: list[StyleTokenRef] = Field(default_factory=list)
    knowledge_links: list[KnowledgeLink] = Field(default_factory=list)
    mission_links: list[MissionLink] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    version_history: list[VersionEntry] = Field(default_factory=list)
    preview_profiles: list[PreviewProfile] = Field(default_factory=list)
    analyzer_report: AnalyzerReport = Field(default_factory=AnalyzerReport)
    knowledge_graph_nodes: list[KnowledgeGraphNode] = Field(default_factory=list)
    knowledge_graph_edges: list[KnowledgeGraphEdge] = Field(default_factory=list)
    quality_score: QualityScore = Field(default_factory=QualityScore)
    live_state: LiveDocumentState = Field(default_factory=LiveDocumentState)


class DipcRunResult(BaseModel):
    run_id: str
    output_dir: str
    document_model_path: str
    theme_css_path: str
    preview_manifest_path: str
    mission_log_path: str
    knowledge_package_path: str
    enterprise_memory_path: str
    publication_outputs: dict[str, str]
