from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict

from .models import OfferInput, OfferQualityReport


def persist_offer_record(
    offer: OfferInput,
    bom: Dict[str, int],
    generated_docs: Dict[str, str],
    quality: OfferQualityReport,
    reuse_score: float,
) -> str:
    output_path = Path("knowledge_hub/spoe/offers_history.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "created_at": datetime.now(UTC).isoformat(),
        "customer": offer.customer,
        "configuration": {
            "plant": offer.plant,
            "country": offer.country,
            "language": offer.language,
            "project_name": offer.project_name,
            "line_length_m": offer.total_main_line_length_m,
            "turns_90": offer.turns_90,
            "ramps_count": offer.ramps_count,
            "ramp_lengths_m": offer.ramp_lengths_m,
        },
        "engineering_parameters": bom,
        "commercial_parameters": {
            "offer_number": offer.offer_number,
            "offer_date": offer.offer_date.isoformat(),
            "commercial_notes": offer.commercial_notes,
            "technical_notes": offer.technical_notes,
        },
        "generated_bom": bom,
        "generated_scope": {
            "scope_of_supply": "Generated in DOCX package.",
            "excluded_scope": "Generated in DOCX package.",
        },
        "generated_documents": generated_docs,
        "lessons_learned": quality.suggestions,
        "future_reuse_score": reuse_score,
        "coordinator_quality_score": quality.quality_score,
    }
    with output_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return str(output_path)
