"""
Modelos de datos para el sistema de inteligencia de conocimiento
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ConfidenceLevel(Enum):
    """Nivel de confianza basado en jerarquía de fuentes"""
    MAXIMUM = 1.0
    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5
    UNVERIFIED = 0.3


class SourceLevel(Enum):
    """Jerarquía de fuentes (Nivel 1 = máxima confianza)"""
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4


@dataclass
class Source:
    """Fuente de información con trazabilidad completa"""
    url: str
    title: str
    author: Optional[str] = None
    date: Optional[datetime] = None
    level: SourceLevel = SourceLevel.LEVEL_3
    confidence: float = 0.5
    extracted_at: datetime = field(default_factory=datetime.now)
    version: Optional[str] = None
    language: str = "es"
    category: Optional[str] = None
    raw_content: Optional[str] = None
    clean_content: Optional[str] = None


@dataclass
class KnowledgeItem:
    """Elemento de conocimiento estructurado"""
    id: str
    title: str
    category: str
    subcategory: Optional[str] = None
    summary: str = ""
    content: str = ""
    sources: List[Source] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    entities: List[Dict] = field(default_factory=list)
    relationships: List[Dict] = field(default_factory=list)
    confidence: float = 0.5
    validated: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: int = 1
    project: Optional[str] = None


@dataclass
class IndustrialKnowledgeObject:
    """Canonical reusable industrial knowledge object shared across engines."""

    object_id: str
    object_type: str
    name: str
    canonical_name: Optional[str] = None
    description: str = ""
    technical_data: Dict[str, Any] = field(default_factory=dict)
    operational_data: Dict[str, Any] = field(default_factory=dict)
    commercial_data: Dict[str, Any] = field(default_factory=dict)
    maintenance_data: Dict[str, Any] = field(default_factory=dict)
    lifecycle_data: Dict[str, Any] = field(default_factory=dict)
    kpis: Dict[str, Any] = field(default_factory=dict)
    digital_twin_params: Dict[str, Any] = field(default_factory=dict)
    simulation_params: Dict[str, Any] = field(default_factory=dict)
    benchmark_data: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    source_refs: List[Source] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.5
    validated: bool = False
    project: Optional[str] = None
    origin_engine: str = "unknown"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: int = 1


@dataclass
class ResearchPlan:
    """Plan de investigación generado por Research Manager"""
    objective: str
    target_company: str
    competitors: List[str]
    areas: List[str]
    key_questions: List[str]
    required_information: List[str]
    search_queries: List[str]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """Resultado de validación de información"""
    item_id: str
    is_valid: bool
    contradictions: List[Dict]
    duplicates: List[str]
    confidence_score: float
    validation_date: datetime = field(default_factory=datetime.now)
    notes: str = ""
