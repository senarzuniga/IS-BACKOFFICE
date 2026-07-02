"""PDF / document extractor (lightweight, no external deps).

This file provides a tiny, dependency-free extractor for development and
tests. It does not call external binaries and returns placeholders for
binary PDF files. For production, replace with `pymupdf` or `pdfminer`.
"""

import os
from typing import Optional


def extract_text_from_pdf(path: str) -> str:
    """Return text extracted from `path`.

    Behavior:
    - If `path` exists and ends with `.txt`, return its contents (useful
      for tests using text fixtures).
    - Otherwise return a placeholder string indicating PDF content.
    """
    if os.path.exists(path) and path.lower().endswith('.txt'):
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            return fh.read()
    return "[PDF_TEXT_PLACEHOLDER]"
