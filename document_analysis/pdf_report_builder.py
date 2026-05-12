"""PDFReportBuilder — render plain text / code reports into modern PDF documents."""

from __future__ import annotations

import re
from datetime import datetime


class PDFReportBuilder:
    """Build polished PDF reports from TXT/markdown/code-like content."""

    _PAGE_WIDTH = 595.0  # A4 portrait points
    _PAGE_HEIGHT = 842.0
    _MARGIN_X = 42.0
    _BODY_BOTTOM = 790.0
    _BRAND_COLOR = (0.07, 0.14, 0.33)
    _ACCENT_COLOR = (0.0, 0.64, 0.82)
    _TEXT_COLOR = (0.12, 0.12, 0.12)
    _SUBTLE_TEXT = (0.45, 0.45, 0.45)
    _CODE_BG = (0.96, 0.97, 0.99)

    def build_pdf(
        self,
        content: str,
        *,
        title: str,
        created_at: datetime | None = None,
        header_image_bytes: bytes | None = None,
        source_type: str = "TXT",
    ) -> bytes:
        """Generate a styled PDF document as bytes."""
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:  # pragma: no cover - handled by caller/tests
            raise RuntimeError("PyMuPDF is required to generate PDF output.") from exc

        created_at = created_at or datetime.now()
        safe_title = self._sanitize(title or "Informe")
        safe_content = self._sanitize(content or "")
        safe_source_type = self._sanitize(source_type or "TXT").upper()

        doc = fitz.open()
        page = doc.new_page(width=self._PAGE_WIDTH, height=self._PAGE_HEIGHT)
        y = self._draw_header(
            page,
            title=safe_title,
            created_at=created_at,
            source_type=safe_source_type,
            header_image_bytes=header_image_bytes,
            first_page=True,
        )

        in_code_block = False
        for raw_line in safe_content.splitlines():
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code_block = not in_code_block
                y += 6
                continue

            if not stripped:
                y += 8
                if y > self._BODY_BOTTOM:
                    page = doc.new_page(width=self._PAGE_WIDTH, height=self._PAGE_HEIGHT)
                    y = self._draw_header(
                        page,
                        title=safe_title,
                        created_at=created_at,
                        source_type=safe_source_type,
                        header_image_bytes=header_image_bytes,
                        first_page=False,
                    )
                continue

            style = self._line_style(stripped, in_code_block)
            text_for_line = style["text"]
            x = float(style["x"])
            max_width = self._PAGE_WIDTH - self._MARGIN_X - x
            wrapped = self._wrap_text(
                text_for_line,
                max_width=max_width,
                fontname=style["fontname"],
                fontsize=float(style["fontsize"]),
                preserve_spaces=bool(style["preserve_spaces"]),
            )

            for wline in wrapped:
                if y + float(style["line_height"]) > self._BODY_BOTTOM:
                    page = doc.new_page(width=self._PAGE_WIDTH, height=self._PAGE_HEIGHT)
                    y = self._draw_header(
                        page,
                        title=safe_title,
                        created_at=created_at,
                        source_type=safe_source_type,
                        header_image_bytes=header_image_bytes,
                        first_page=False,
                    )

                if bool(style["code"]):
                    bg = fitz.Rect(
                        x - 5,
                        y - float(style["fontsize"]) + 3,
                        self._PAGE_WIDTH - self._MARGIN_X,
                        y + 5,
                    )
                    page.draw_rect(bg, fill=self._CODE_BG, color=self._CODE_BG, width=0)

                page.insert_text(
                    (x, y),
                    wline,
                    fontsize=float(style["fontsize"]),
                    fontname=str(style["fontname"]),
                    color=style["color"],
                )
                y += float(style["line_height"])

            y += float(style["after"])

        doc.set_metadata(
            {
                "title": safe_title,
                "author": "IS-BACKOFFICE",
                "subject": f"Informe {safe_source_type}",
                "creator": "IS-BACKOFFICE Document Analysis",
                "producer": "PyMuPDF",
                "keywords": "report, executive, ai, pdf, backoffice",
            }
        )
        self._draw_page_numbers(doc)
        pdf_bytes = doc.tobytes(deflate=True, garbage=3)
        doc.close()
        return pdf_bytes

    def _draw_header(
        self,
        page: "fitz.Page",
        *,
        title: str,
        created_at: datetime,
        source_type: str,
        header_image_bytes: bytes | None,
        first_page: bool,
    ) -> float:
        import fitz  # PyMuPDF

        date_text = created_at.strftime("%d/%m/%Y %H:%M")
        page.draw_rect(
            fitz.Rect(0, 0, self._PAGE_WIDTH, 18),
            fill=self._ACCENT_COLOR,
            color=self._ACCENT_COLOR,
            width=0,
        )

        if first_page:
            image_y = 26
            image_h = 52
            title_y = 145
            subtitle_y = 167
            body_start = 196
            title_size = 23
            subtitle_size = 11
        else:
            image_y = 22
            image_h = 34
            title_y = 48
            subtitle_y = 64
            body_start = 90
            title_size = 12
            subtitle_size = 9

        image_rect = fitz.Rect(self._MARGIN_X, image_y, self._MARGIN_X + 126, image_y + image_h)
        if header_image_bytes:
            try:
                page.insert_image(image_rect, stream=header_image_bytes, keep_proportion=True)
            except Exception:
                page.insert_text(
                    (self._MARGIN_X, image_y + 25),
                    "LOGO",
                    fontsize=10,
                    fontname="helv",
                    color=self._BRAND_COLOR,
                )
        else:
            page.insert_text(
                (self._MARGIN_X, image_y + 25),
                "IS-BACKOFFICE",
                fontsize=10,
                fontname="helv",
                color=self._BRAND_COLOR,
            )

        title_width = fitz.get_text_length(title, fontname="helv", fontsize=title_size)
        page.insert_text(
            ((self._PAGE_WIDTH - title_width) / 2, title_y),
            title,
            fontsize=title_size,
            fontname="helv",
            color=self._BRAND_COLOR,
        )

        subtitle = f"Fecha de creación: {date_text} · Fuente: {source_type}"
        subtitle_width = fitz.get_text_length(subtitle, fontname="helv", fontsize=subtitle_size)
        page.insert_text(
            ((self._PAGE_WIDTH - subtitle_width) / 2, subtitle_y),
            subtitle,
            fontsize=subtitle_size,
            fontname="helv",
            color=self._SUBTLE_TEXT,
        )

        line_y = body_start - 16
        page.draw_line(
            (self._MARGIN_X, line_y),
            (self._PAGE_WIDTH - self._MARGIN_X, line_y),
            color=self._ACCENT_COLOR,
            width=1.2,
        )
        return body_start

    def _draw_page_numbers(self, doc: "fitz.Document") -> None:
        import fitz  # PyMuPDF

        total = doc.page_count
        for idx, page in enumerate(doc, start=1):
            footer = f"Página {idx} de {total}"
            footer_width = fitz.get_text_length(footer, fontname="helv", fontsize=9)
            x = (self._PAGE_WIDTH - footer_width) / 2
            page.insert_text(
                (x, 820),
                footer,
                fontsize=9,
                fontname="helv",
                color=self._SUBTLE_TEXT,
            )

    def _line_style(self, stripped: str, in_code_block: bool) -> dict[str, object]:
        if in_code_block:
            return {
                "text": stripped,
                "fontname": "cour",
                "fontsize": 9.8,
                "line_height": 14.0,
                "color": self._TEXT_COLOR,
                "x": self._MARGIN_X + 8,
                "after": 1.0,
                "code": True,
                "preserve_spaces": True,
            }

        if stripped.startswith("# "):
            return {
                "text": stripped[2:].strip(),
                "fontname": "helv",
                "fontsize": 17.0,
                "line_height": 24.0,
                "color": self._BRAND_COLOR,
                "x": self._MARGIN_X,
                "after": 4.0,
                "code": False,
                "preserve_spaces": False,
            }

        if stripped.startswith("## "):
            return {
                "text": stripped[3:].strip(),
                "fontname": "helv",
                "fontsize": 13.0,
                "line_height": 18.0,
                "color": self._BRAND_COLOR,
                "x": self._MARGIN_X,
                "after": 2.5,
                "code": False,
                "preserve_spaces": False,
            }

        if stripped.startswith("### "):
            return {
                "text": stripped[4:].strip(),
                "fontname": "helv",
                "fontsize": 11.5,
                "line_height": 16.0,
                "color": self._BRAND_COLOR,
                "x": self._MARGIN_X,
                "after": 2.0,
                "code": False,
                "preserve_spaces": False,
            }

        if re.match(r"^(\-|\*|\d+\.)\s+", stripped):
            plain = re.sub(r"^(\-|\*|\d+\.)\s+", "", stripped)
            return {
                "text": f"• {plain}",
                "fontname": "helv",
                "fontsize": 10.7,
                "line_height": 15.5,
                "color": self._TEXT_COLOR,
                "x": self._MARGIN_X + 12,
                "after": 1.5,
                "code": False,
                "preserve_spaces": False,
            }

        return {
            "text": stripped,
            "fontname": "helv",
            "fontsize": 10.9,
            "line_height": 16.0,
            "color": self._TEXT_COLOR,
            "x": self._MARGIN_X,
            "after": 2.0,
            "code": False,
            "preserve_spaces": False,
        }

    def _wrap_text(
        self,
        text: str,
        *,
        max_width: float,
        fontname: str,
        fontsize: float,
        preserve_spaces: bool,
    ) -> list[str]:
        import fitz  # PyMuPDF

        if not text:
            return [""]

        if preserve_spaces:
            lines: list[str] = []
            current = ""
            for char in text:
                candidate = current + char
                if fitz.get_text_length(candidate, fontname=fontname, fontsize=fontsize) <= max_width:
                    current = candidate
                else:
                    if current:
                        lines.append(current)
                    current = char
            if current:
                lines.append(current)
            return lines or [""]

        words = text.split()
        if not words:
            return [""]

        lines = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if fitz.get_text_length(candidate, fontname=fontname, fontsize=fontsize) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    @staticmethod
    def _sanitize(text: str) -> str:
        if not text:
            return ""
        return "".join(ch for ch in text.replace("\x00", "") if ch == "\n" or ord(ch) >= 32).strip()
