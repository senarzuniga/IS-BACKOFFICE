"""Canonical, traceable access to INGETRANS engineering parameters."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REFERENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "knowledge_hub"
    / "INGETRANS_ENGINEERING_REFERENCE"
    / "canonical_data"
    / "INGETRANS_ENGINEERING_REFERENCE.v1.json"
)

REQUIRED_TRACEABILITY_FIELDS = {
    "source_document",
    "source_page",
    "source_table",
    "source_condition",
    "confidence",
    "validation_status",
    "effective_version",
    "created_at",
    "updated_at",
}


class ReferenceValidationError(ValueError):
    """Raised when canonical engineering data violates governance rules."""


def load_reference(path: Path | str = REFERENCE_PATH) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as reference_file:
        reference = json.load(reference_file)
    validate_reference(reference)
    return reference


def validate_reference(reference: dict[str, Any]) -> None:
    if reference.get("dataset") != "INGETRANS_ENGINEERING_REFERENCE":
        raise ReferenceValidationError("Unexpected canonical dataset name")

    for parameter in reference.get("parameters", []):
        missing = REQUIRED_TRACEABILITY_FIELDS.difference(parameter)
        if missing:
            raise ReferenceValidationError(
                f"{parameter.get('variable', '<unknown>')} missing traceability: {sorted(missing)}"
            )
        if parameter.get("governance_level") == 1:
            empty_source = [
                field
                for field in ("source_document", "source_page", "source_table")
                if parameter.get(field) in (None, "")
            ]
            if empty_source:
                raise ReferenceValidationError(
                    f"LEVEL 1 {parameter.get('variable')} has no primary-source traceability: {empty_source}"
                )


def get_parameter(
    variable: str,
    *,
    project: str | None = None,
    condition: str | None = None,
    path: Path | str = REFERENCE_PATH,
) -> dict[str, Any]:
    reference = load_reference(path)
    candidates = [item for item in reference["parameters"] if item.get("variable") == variable]
    applicable = [
        item
        for item in candidates
        if item.get("applicability") in {"GLOBAL", "BENCHMARK"}
        or (item.get("applicability") == "PROJECT-SPECIFIC" and item.get("project") == project)
        or (
            item.get("applicability") == "CONDITION-SPECIFIC"
            and item.get("project") == project
            and item.get("condition_id") == condition
        )
    ]
    if not applicable:
        raise KeyError(f"No applicable canonical value for {variable!r}")
    return min(applicable, key=lambda item: int(item["governance_level"]))