from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backoffice.his.corporate_models import DeliveryPolicy
from backoffice.his.corporate_publishing import CorporatePublishingService


def main() -> int:
    service = CorporatePublishingService()
    source = "PCG_MIDDLETOWN_CONVERTING_AUDIT_2026-08-17.html"
    adapter = service.adapters["ai_factory"]
    source_hash_before = adapter.snapshot(source).sha256

    pcg = service.publish_bilingual_html(
        repository_id="ai_factory",
        relative_path=source,
        title="PCG Middletown Converting Audit",
        client="President Container Group",
        project="Middletown Converting Audit",
        delivery_policy=DeliveryPolicy(
            profile_id="standard",
            allowed_formats=["html", "pdf", "docx"],
            required_languages=["en", "es"],
        ),
    )
    cascades = service.publish_bilingual_html(
        repository_id="ai_factory",
        relative_path=source,
        title="Cascades Corporate Audit Delivery",
        client="Cascades",
        project="Corporate Audit",
        delivery_policy=DeliveryPolicy(
            profile_id="cascades_pdf_only",
            allowed_formats=["pdf"],
            required_languages=["en", "es"],
        ),
    )
    package = Path(service.create_delivery_package(cascades.document_id))
    with zipfile.ZipFile(package) as archive:
        package_entries = archive.namelist()

    source_hash_after = adapter.snapshot(source).sha256
    result = {
        "pcg_id": pcg.document_id,
        "pcg_status": pcg.status,
        "pcg_artifacts": [
            {
                "language": artifact.language,
                "format": artifact.format,
                "size": artifact.size_bytes,
                "path": artifact.path,
            }
            for artifact in pcg.artifacts
        ],
        "cascades_id": cascades.document_id,
        "cascades_status": cascades.status,
        "cascades_package": str(package),
        "cascades_package_entries": package_entries,
        "source_unchanged": source_hash_before == source_hash_after,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    expected_formats = {"html", "pdf", "docx"}
    actual_pairs = {(artifact.language, artifact.format) for artifact in pcg.artifacts}
    expected_pairs = {(language, format_name) for language in ("en", "es") for format_name in expected_formats}
    package_is_pdf_only = not any(name.endswith((".html", ".docx", ".xlsx", ".pptx")) for name in package_entries)
    accepted = (
        pcg.status == "ready"
        and cascades.status == "ready"
        and actual_pairs == expected_pairs
        and package_is_pdf_only
        and result["source_unchanged"]
    )
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
