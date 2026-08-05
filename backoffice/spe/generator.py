"""Service Proposal Engine — HTML adapter based exclusively on HIS V3."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backoffice.his.studio import HtmlIntelligenceStudio

from .models import Proposal


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CORPORATE_TEMPLATE = Path(r"C:/Users/Inaki Senar/Documents/GitHub/ingesite.github.io/Modelo_HTML.txt")


class ProposalHTMLGenerator:
    """Generates proposal documents via HIS V3 as the single corporate HTML engine."""

    def __init__(self) -> None:
        self.corporate_model_path = DEFAULT_CORPORATE_TEMPLATE
        self.his = HtmlIntelligenceStudio(corporate_model_path=self.corporate_model_path)

    def generate(self, proposal: Proposal, preview: bool = False) -> str:
        payload = self._proposal_to_markdown(proposal)
        output_root = REPO_ROOT / "reports" / "spe" / "runs"
        source_dir = REPO_ROOT / "reports" / "spe" / "sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        slug = (proposal.number or proposal.id or "proposal").replace("/", "-").replace(" ", "_")
        source_file = source_dir / f"{slug}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.md"
        source_file.write_text(payload, encoding="utf-8")
        result = self.his.create_document(
            document_name=proposal.title or "Service Proposal",
            project=proposal.project or "Service_Proposal_Engine",
            client=proposal.customer or "INGECART Client",
            category="spe",
            language=proposal.language or "en",
            source_format="Markdown",
            sources=[str(source_file)],
            output_root=str(output_root),
            comments="Service Proposal Engine generation via HIS V3",
            objective="Generate corporate service proposal with validated publication structure",
            audience="Commercial and Executive",
            instruction_text="Use official corporate template and remove KPI summary block.",
        )

        html_path = Path(result["html_path"])
        html = html_path.read_text(encoding="utf-8", errors="ignore") if html_path.exists() else ""
        model_path = Path(result["document_model_path"])

        proposal.report_id = result.get("run_id", "")
        proposal.docx_path = str(result.get("quality_report_path", ""))
        proposal.pdf_path = str(result.get("technical_report_path", ""))

        quality_path = Path(result.get("quality_report_path", ""))
        metadata = {
            "generator": "HIS_V3",
            "preview": preview,
            "run_id": result.get("run_id", ""),
            "output_dir": result.get("output_dir", ""),
            "document_model_path": str(model_path),
            "html_path": str(html_path),
            "quality_report_path": str(quality_path),
            "generated_at": datetime.now(UTC).isoformat(),
        }

        meta_file = model_path.parent / "spe_generation_metadata.json"
        meta_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        if not preview:
            proposal.html_output = html
        return html

    def get_model_path(self, proposal: Proposal) -> str:
        if not proposal.report_id:
            return ""
        search_root = REPO_ROOT / "reports" / "spe" / "runs"
        candidates = sorted(search_root.glob(f"**/{proposal.report_id}/metadata/document_model.json"), reverse=True)
        if candidates:
            return str(candidates[0])

        # Fallback: inspect latest metadata file with matching report_id.
        for meta in sorted(search_root.glob("**/metadata/spe_generation_metadata.json"), reverse=True):
            try:
                payload = json.loads(meta.read_text(encoding="utf-8"))
            except Exception:
                continue
            if payload.get("run_id") == proposal.report_id:
                model_path = payload.get("document_model_path", "")
                if model_path and Path(model_path).exists():
                    return model_path
        return ""

    def _proposal_to_markdown(self, proposal: Proposal) -> str:
        lines: list[str] = []
        lines.append(f"# {proposal.title or 'Service Proposal'}")
        lines.append("")
        lines.append("## Proposal Metadata")
        lines.append(f"- Number: {proposal.number or 'pending'}")
        lines.append(f"- Customer: {proposal.customer or '-'}")
        lines.append(f"- Plant: {proposal.plant or '-'}")
        lines.append(f"- Country: {proposal.customer_country or '-'}")
        lines.append(f"- Language: {proposal.language or 'en'}")
        lines.append(f"- Currency: {proposal.currency or 'EUR'}")
        lines.append(f"- Duration: {proposal.duration or '-'}")
        lines.append(f"- Validity Days: {proposal.validity_days}")
        lines.append(f"- Payment Terms: {proposal.payment_terms or '-'}")
        lines.append("")

        lines.append("## Executive Summary")
        lines.append(proposal.executive_summary or "Corporate service proposal generated under AHDE governance.")
        lines.append("")

        lines.append("## Services")
        if proposal.services:
            for s in proposal.services:
                if not s.enabled:
                    continue
                lines.append(f"### {s.name}")
                lines.append(s.description or "")
                lines.append(f"- Service ID: {s.service_id}")
                lines.append(f"- Frequency: {s.frequency or s.unit}")
                lines.append(f"- Quantity: {s.quantity}")
                lines.append(f"- Unit Price: {s.price:.2f} {proposal.currency}")
                lines.append(f"- Total: {s.total_price:.2f} {proposal.currency}")
                lines.append(f"- Optional: {'Yes' if s.optional else 'No'}")
                if s.coverage:
                    lines.append(f"- Coverage: {s.coverage}")
                if s.deliverables:
                    lines.append(f"- Deliverables: {s.deliverables}")
                lines.append("")
        else:
            lines.append("No services configured.")
            lines.append("")

        sections = [
            ("About INGECART", proposal.about_ingecart),
            ("Understanding Installation", proposal.understanding_installation),
            ("Objectives", proposal.objectives),
            ("Scope Of Services", proposal.scope_of_services),
            ("Maintenance Programme", proposal.maintenance_programme),
            ("Visit Methodology", proposal.visit_methodology),
            ("Deliverables", proposal.deliverables),
            ("IngPRO Section", proposal.ingpro_section),
            ("Optional Services", proposal.optional_services),
            ("Customer Responsibilities", proposal.customer_responsibilities),
            ("Commercial Conditions", proposal.commercial_conditions),
            ("Pricing Summary", proposal.pricing_summary),
            ("Why INGECART", proposal.why_ingecart),
            ("Acceptance", proposal.acceptance),
            ("Annexes", proposal.annexes),
        ]
        for title, content in sections:
            lines.append(f"## {title}")
            lines.append(content or "")
            lines.append("")

        return "\n".join(lines)
