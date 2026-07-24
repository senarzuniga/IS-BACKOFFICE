from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List


@dataclass
class OfferInput:
    customer: str
    plant: str
    country: str
    language: str
    offer_number: str
    offer_date: date
    project_name: str
    total_main_line_length_m: float
    turns_90: int
    ramps_count: int
    ramp_lengths_m: List[float]
    additional_notes: str = ""
    commercial_notes: str = ""
    technical_notes: str = ""
    layout_image_path: str = ""
    optional_attachment_paths: List[str] = field(default_factory=list)

    @property
    def total_ramp_length_m(self) -> float:
        return float(sum(self.ramp_lengths_m or []))


@dataclass
class ProductTemplate:
    key: str
    display_name: str
    status: str
    description: str


@dataclass
class ArchitectureAlternative:
    name: str
    description: str
    metrics_0_10: Dict[str, float]


@dataclass
class OfferQualityReport:
    quality_score: float
    iteration_count: int
    missing_fields: List[str]
    suggestions: List[str]
    accepted: bool
