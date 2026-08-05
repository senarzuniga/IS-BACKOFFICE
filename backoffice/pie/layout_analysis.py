from __future__ import annotations

from collections import Counter

from .models import SlideAnalysis


def detect_layout(slide_width: float, elements: list[dict]) -> str:
    if not elements:
        return "empty"

    centers = [e["x"] + (e["w"] / 2.0) for e in elements]
    left = sum(1 for c in centers if c < slide_width * 0.4)
    right = sum(1 for c in centers if c > slide_width * 0.6)

    if left > 0 and right > 0:
        return "two-column"
    if len(elements) >= 7:
        return "grid"
    return "single-column"


def build_visual_hierarchy(slide: SlideAnalysis) -> list[str]:
    ranked = []
    for element in slide.elements:
        priority = 0.0
        if element.kind == "title":
            priority += 100
        if element.kind in {"heading", "text"}:
            priority += 40
        if element.style.font_size_pt:
            priority += float(element.style.font_size_pt)
        priority += (element.w * element.h) / max(slide.width * slide.height, 1.0) * 80
        ranked.append((priority, element.element_id, element.kind))

    ranked.sort(reverse=True)
    return [f"{eid}:{kind}" for _, eid, kind in ranked]


def extract_palette(slides: list[SlideAnalysis], top_n: int = 12) -> list[str]:
    freq = Counter()
    for slide in slides:
        for color in slide.palette:
            if color:
                freq[color] += 1
    return [c for c, _ in freq.most_common(top_n)]
