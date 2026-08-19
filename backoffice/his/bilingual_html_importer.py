from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from backoffice.dipc.component_library import normalize_component
from backoffice.dipc.models import BlockNode, DocumentModel, EvidenceRecord, SectionNode


class BilingualHtmlImporter:
    """Convert paired `.lang-en`/`.lang-es` HTML branches into DIPC models."""

    def import_file(self, source: str | Path, *, title: str | None = None) -> dict[str, DocumentModel]:
        path = Path(source).expanduser().resolve()
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        models: dict[str, DocumentModel] = {}
        for language in ("en", "es"):
            model = self._build_model(soup, path, language, title)
            if model.sections:
                models[language] = model
        if not models:
            raise ValueError("No `.lang-en` or `.lang-es` document branches were found")
        return models

    def _build_model(
        self,
        soup: BeautifulSoup,
        path: Path,
        language: str,
        title_override: str | None,
    ) -> DocumentModel:
        hero = soup.select_one(f".hero .lang-{language}")
        title_node = hero.find("h1") if isinstance(hero, Tag) else None
        subtitle_node = hero.find("p") if isinstance(hero, Tag) else None
        title = title_override or (title_node.get_text(" ", strip=True) if title_node else path.stem)
        subtitle = subtitle_node.get_text(" ", strip=True) if subtitle_node else None
        sections: list[SectionNode] = []
        evidence: list[EvidenceRecord] = []
        for order, section in enumerate(soup.find_all("section"), start=1):
            branch = section.select_one(f".lang-{language}")
            if not isinstance(branch, Tag):
                continue
            heading = branch.find(["h2", "h1"])
            section_title = heading.get_text(" ", strip=True) if heading else f"Section {order}"
            components = []
            for child in branch.find_all(["h3", "p", "table", "div"], recursive=True):
                if child.find_parent("table") and child.name != "table":
                    continue
                classes = set(child.get("class", []))
                if child.name == "table":
                    rows = [
                        [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
                        for row in child.find_all("tr")
                    ]
                    if rows:
                        components.append(normalize_component("table", None, None, props={"rows": rows}))
                elif child.name == "div" and classes.intersection({"decision", "formula"}):
                    kind = "technical_specification" if "formula" in classes else "executive_summary"
                    components.append(normalize_component(kind, None, child.get_text(" ", strip=True)))
                elif child.name == "h3":
                    body = child.find_next_sibling("p")
                    components.append(
                        normalize_component(
                            "text",
                            child.get_text(" ", strip=True),
                            body.get_text(" ", strip=True) if isinstance(body, Tag) else None,
                        )
                    )
                elif child.name == "p" and child.find_previous_sibling("h3") is None:
                    text = child.get_text(" ", strip=True)
                    if text:
                        components.append(normalize_component("text", None, text))
            seen: set[tuple[str | None, str | None]] = set()
            unique = []
            for component in components:
                key = (component.title, component.body)
                if key in seen:
                    continue
                seen.add(key)
                unique.append(component)
            sections.append(
                SectionNode(
                    title=section_title,
                    order=order,
                    blocks=[BlockNode(block_type="corporate_section", components=unique)],
                    metadata={"source_section_id": section.get("id", f"section-{order}")},
                )
            )
        for badge in soup.select(f".lang-{language} .evidence"):
            classes = set(badge.get("class", []))
            kind = next((item.removeprefix("e-") for item in classes if item.startswith("e-")), "source")
            evidence.append(EvidenceRecord(kind=kind, description=badge.get_text(" ", strip=True)))
        return DocumentModel(
            title=title,
            subtitle=subtitle,
            source_path=str(path),
            source_type="html",
            document_type="corporate_report",
            theme_variant="light",
            metadata={"language": language, "visual_profile": "pcg_corporate"},
            sections=sections,
            evidence=evidence,
        )
