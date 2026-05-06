"""Unit normaliser – converts speed and width to SI base units."""
from __future__ import annotations


class UnitNormalizer:
    def normalize_speed(self, value: float | None, unit: str | None) -> tuple[float | None, str]:
        """Normalise speed to m/min."""
        if value is None:
            return None, "m/min"
        src = (unit or "m/min").lower()
        if src in {"m/h", "mph", "metres/hour"}:
            return round(value / 60, 3), "m/min"
        if src in {"ft/min", "fpm"}:
            return round(value * 0.3048, 3), "m/min"
        return value, "m/min"

    def normalize_width(self, value: float | None, unit: str | None) -> tuple[float | None, str]:
        """Normalise width to mm."""
        if value is None:
            return None, "mm"
        src = (unit or "mm").lower()
        if src == "cm":
            return round(value * 10, 1), "mm"
        if src in {"m", "metres", "meters"}:
            return round(value * 1000, 1), "mm"
        if src in {"in", "inch", "inches"}:
            return round(value * 25.4, 1), "mm"
        return value, "mm"
