from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class EDTObject:
    id: str
    type: str
    name: str
    description: Optional[str] = None
    capability: List[str] = field(default_factory=list)
    business_purpose: Optional[str] = None
    engineering_purpose: Optional[str] = None
    owner: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    status: str = "discovered"
    health: Optional[str] = None
    version: Optional[str] = None
    documentation: Optional[str] = None
    tests: Optional[Dict] = field(default_factory=dict)
    coverage: Optional[float] = None
    permissions: Optional[Dict] = field(default_factory=dict)
    knowledge_domains: List[str] = field(default_factory=list)
    execution_cost: Optional[float] = None
    complexity: Optional[str] = None
    reuse_score: Optional[float] = None
    business_value: Optional[float] = None
    engineering_value: Optional[float] = None
    architecture_maturity: Optional[str] = None
    technical_debt: Optional[float] = None
    risk: Optional[str] = None
    confidence: Optional[float] = None
    evidence: List[str] = field(default_factory=list)
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self):
        return asdict(self)
