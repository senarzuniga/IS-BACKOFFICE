"""HTML / document parser utilities (minimal, dependency-free).

These helpers are intentionally simple: tag-stripping and metadata
extraction placeholders suitable for unit testing and architectural
validation.
"""

import re
from typing import Dict


def extract_text_from_html(html: str) -> str:
    """Very small HTML -> text extractor (not a full parser).

    Use proper HTML parsers (BeautifulSoup/lxml) in production.
    """
    # remove script/style blocks
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    # remove tags
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_metadata_from_html(html: str) -> Dict[str, str]:
    """Return a tiny metadata dict (title, description) if present.

    This is a heuristic placeholder.
    """
    meta = {}
    m = re.search(r'<title>(.*?)</title>', html, flags=re.I | re.S)
    if m:
        meta['title'] = m.group(1).strip()
    m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html, flags=re.I)
    if m:
        meta['description'] = m.group(1).strip()
    return meta
