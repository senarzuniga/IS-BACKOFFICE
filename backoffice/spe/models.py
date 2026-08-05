"""Service Proposal Engine — Data Models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class ProposalLanguage(str, Enum):
    ES = "es"
    EN = "en"


class ProposalCurrency(str, Enum):
    EUR = "EUR"
    USD = "USD"


@dataclass
class ServiceItem:
    service_id: str
    name: str
    description: str
    price: float = 0.0
    unit: str = "year"          # year, month, visit, hour, lumpsum
    quantity: float = 1.0
    frequency: str = ""         # e.g. "4 visits/year"
    hours_per_event: float = 0.0
    persons: int = 1
    coverage: str = ""
    objectives: str = ""
    deliverables: str = ""
    spare_parts: str = ""
    emergency_response: str = ""
    optional: bool = False
    enabled: bool = True
    notes: str = ""

    @property
    def total_price(self) -> float:
        return self.price * self.quantity


@dataclass
class ProposalVersion:
    version: int
    created_at: str
    author: str
    changes: str
    html_snapshot: str = ""


@dataclass
class MissionEntry:
    mission_id: str
    name: str
    status: str
    agents: List[str] = field(default_factory=list)
    prompts: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    kpis: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    completed_at: str = ""


@dataclass
class Proposal:
    # Identity
    id: str = ""
    number: str = ""                # OFF-AAAA-SXXX
    title: str = ""
    status: str = ProposalStatus.DRAFT.value
    version: int = 1

    # Customer
    customer: str = ""
    customer_contact: str = ""
    customer_email: str = ""
    customer_phone: str = ""
    customer_address: str = ""
    customer_country: str = ""
    plant: str = ""

    # Commercial
    language: str = ProposalLanguage.EN.value
    currency: str = ProposalCurrency.EUR.value
    responsible: str = "INGECART"
    commercial: str = ""
    project: str = ""
    duration: str = ""
    validity_days: int = 30
    incoterm: str = ""
    payment_terms: str = ""
    observations: str = ""

    # Dates
    date_created: str = ""
    date_sent: str = ""
    date_accepted: str = ""
    date_expiry: str = ""

    # Services
    services: List[ServiceItem] = field(default_factory=list)

    # Document sections (editable text)
    executive_summary: str = ""
    about_ingecart: str = ""
    understanding_installation: str = ""
    objectives: str = ""
    scope_of_services: str = ""
    maintenance_programme: str = ""
    visit_methodology: str = ""
    deliverables: str = ""
    ingpro_section: str = ""
    optional_services: str = ""
    customer_responsibilities: str = ""
    commercial_conditions: str = ""
    pricing_summary: str = ""
    why_ingecart: str = ""
    acceptance: str = ""
    annexes: str = ""

    # IA
    ai_comments: List[str] = field(default_factory=list)
    prompt_history: List[Dict[str, str]] = field(default_factory=list)

    # Mission
    missions: List[MissionEntry] = field(default_factory=list)

    # Metadata
    authors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    template_id: str = ""
    parent_id: str = ""          # If duplicated/versioned from another

    # Generated docs
    html_output: str = ""
    pdf_path: str = ""
    docx_path: str = ""
    report_id: str = ""

    # Version history
    versions: List[ProposalVersion] = field(default_factory=list)
    change_log: List[str] = field(default_factory=list)

    @property
    def total_price(self) -> float:
        return sum(s.total_price for s in self.services if s.enabled and not s.optional)

    @property
    def optional_price(self) -> float:
        return sum(s.total_price for s in self.services if s.enabled and s.optional)

    @property
    def display_number(self) -> str:
        return self.number or f"DRAFT-{self.id[:6]}"


# ─────────────────────────────────────────────────────────────────
# Service Catalog Definition
# ─────────────────────────────────────────────────────────────────
SERVICE_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "preventive_maintenance",
        "name": "Preventive Maintenance Programme",
        "category": "Maintenance",
        "default_price": 0.0,
        "unit": "year",
        "description": (
            "Scheduled preventive maintenance visits to ensure optimal performance, "
            "reduce unplanned downtime and extend the lifecycle of your equipment. "
            "Each visit includes systematic inspection, lubrication, calibration, "
            "functional testing and a detailed technical report."
        ),
        "icon": "🔧",
    },
    {
        "id": "ingpro",
        "name": "IngPRO Digital Monitoring",
        "category": "Digital",
        "default_price": 15000.0,
        "unit": "year",
        "description": (
            "Continuous cloud-based condition monitoring platform capturing vibration, "
            "temperature, current consumption and PLC tags. AI-powered analytics detect "
            "bearing defects, gear faults, misalignment and process anomalies. "
            "Periodic automated reports and real-time alerts included."
        ),
        "icon": "📡",
    },
    {
        "id": "emergency_support",
        "name": "Emergency On-site Support",
        "category": "Support",
        "default_price": 0.0,
        "unit": "event",
        "description": (
            "Priority emergency response with guaranteed on-site arrival within agreed "
            "response time. Includes diagnostic, root cause analysis, repair, and "
            "corrective action report."
        ),
        "icon": "🚨",
    },
    {
        "id": "remote_assistance",
        "name": "Remote Technical Assistance",
        "category": "Support",
        "default_price": 0.0,
        "unit": "hour",
        "description": (
            "Remote diagnostics and troubleshooting via secure VPN connection. "
            "Access to INGECART specialist engineers for real-time problem resolution, "
            "parameter adjustment and operational guidance."
        ),
        "icon": "💻",
    },
    {
        "id": "spare_parts_review",
        "name": "Spare Parts Review & Optimisation",
        "category": "Engineering",
        "default_price": 0.0,
        "unit": "lumpsum",
        "description": (
            "Complete review of existing spare parts inventory. Identification of "
            "critical, fast-moving and slow-moving parts. Recommended stock levels "
            "and supplier qualification. Delivers a certified spare parts list."
        ),
        "icon": "🗄️",
    },
    {
        "id": "engineering_audit",
        "name": "Engineering Audit",
        "category": "Engineering",
        "default_price": 0.0,
        "unit": "lumpsum",
        "description": (
            "Comprehensive technical audit covering mechanical, electrical, automation "
            "and process performance. Benchmarking against industry standards and "
            "manufacturer specifications. Delivers a prioritised improvement roadmap."
        ),
        "icon": "📊",
    },
    {
        "id": "electrical_inspection",
        "name": "Electrical Inspection",
        "category": "Inspection",
        "default_price": 0.0,
        "unit": "visit",
        "description": (
            "Detailed electrical inspection including switchgear, drives, motors, "
            "wiring condition, earthing, insulation resistance and thermal imaging. "
            "Full inspection report with corrective action list."
        ),
        "icon": "⚡",
    },
    {
        "id": "mechanical_inspection",
        "name": "Mechanical Inspection",
        "category": "Inspection",
        "default_price": 0.0,
        "unit": "visit",
        "description": (
            "In-depth mechanical inspection of rotating equipment, structural components, "
            "bearings, couplings, chains, belts and guarding. Vibration measurements "
            "and alignment checks included."
        ),
        "icon": "⚙️",
    },
    {
        "id": "automation_review",
        "name": "Automation & Control Review",
        "category": "Engineering",
        "default_price": 0.0,
        "unit": "lumpsum",
        "description": (
            "Review of PLC programming, HMI configurations, SCADA architecture and "
            "control loops. Identifies obsolescence risks, cyber vulnerabilities "
            "and optimisation opportunities."
        ),
        "icon": "🖥️",
    },
    {
        "id": "plc_backup",
        "name": "PLC Programme Backup & Archive",
        "category": "Engineering",
        "default_price": 0.0,
        "unit": "lumpsum",
        "description": (
            "Complete backup and secure archiving of all PLC, HMI and drive programmes "
            "and parameters. Version-controlled repository with change documentation "
            "and disaster recovery procedure."
        ),
        "icon": "💾",
    },
    {
        "id": "safety_audit",
        "name": "Safety & Compliance Audit",
        "category": "Safety",
        "default_price": 0.0,
        "unit": "lumpsum",
        "description": (
            "Systematic safety audit against applicable machinery directives (2006/42/EC), "
            "OSHA standards and customer EHS requirements. Risk assessment update, "
            "CE marking review and corrective action plan."
        ),
        "icon": "🛡️",
    },
    {
        "id": "software_update",
        "name": "Software & Firmware Updates",
        "category": "Engineering",
        "default_price": 0.0,
        "unit": "event",
        "description": (
            "Planned software and firmware update service including pre-update testing, "
            "backup, implementation, functional validation and rollback procedure. "
            "Covers PLC, HMI, drives and embedded controllers."
        ),
        "icon": "🔄",
    },
    {
        "id": "training",
        "name": "Technical Training Programme",
        "category": "Training",
        "default_price": 0.0,
        "unit": "day",
        "description": (
            "Customised training programme for maintenance and operations personnel. "
            "Covers equipment operation, maintenance procedures, fault diagnosis "
            "and safety practices. On-site or remote delivery available."
        ),
        "icon": "🎓",
    },
    {
        "id": "modernisation",
        "name": "Modernisation & Upgrade",
        "category": "Projects",
        "default_price": 0.0,
        "unit": "lumpsum",
        "description": (
            "Turnkey modernisation projects including obsolescence management, "
            "retrofitting of mechanical and electrical components, automation upgrades "
            "and performance improvement. Full project management and commissioning."
        ),
        "icon": "🏗️",
    },
    {
        "id": "lifecycle_consulting",
        "name": "Lifecycle & Asset Management Consulting",
        "category": "Consulting",
        "default_price": 0.0,
        "unit": "lumpsum",
        "description": (
            "Strategic consulting on asset lifecycle management including end-of-life "
            "planning, total cost of ownership analysis, investment prioritisation "
            "and long-term maintenance strategy."
        ),
        "icon": "📈",
    },
    {
        "id": "predictive_maintenance",
        "name": "Predictive Maintenance (Advanced)",
        "category": "Digital",
        "default_price": 0.0,
        "unit": "year",
        "description": (
            "Machine-learning based predictive maintenance using on-site sensor network, "
            "historical data correlation and failure pattern recognition. "
            "Predictive alerts with recommended maintenance actions."
        ),
        "icon": "🔮",
    },
]
