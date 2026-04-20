"""Data normalization utilities."""
from __future__ import annotations
import re
import unicodedata
from typing import Optional

# Common currency symbols → ISO codes
_CURRENCY_MAP = {
    "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY",
    "usd": "USD", "eur": "EUR", "gbp": "GBP", "jpy": "JPY",
    "dh": "MAD", "mad": "MAD",
}

# Simple EUR conversion rates (static fallback)
_TO_EUR = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17, "JPY": 0.0062, "MAD": 0.092}


class Normalizer:
    """Normalizes strings, currencies, numbers, and dates."""

    # ── Text ─────────────────────────────────────────────────────────────────

    def normalize_name(self, name: str) -> str:
        """Lowercase, strip accents, collapse whitespace."""
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")
        name = name.lower().strip()
        name = re.sub(r"\s+", " ", name)
        return name

    def normalize_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r" +", " ", text)
        return text

    # ── Numbers ──────────────────────────────────────────────────────────────

    def parse_number(self, value: str) -> Optional[float]:
        """Parse a string like '1 234,56' or '1,234.56' into float."""
        if not value:
            return None
        value = value.strip()
        # Remove currency symbols and spaces
        value = re.sub(r"[€$£¥\s]", "", value)
        # Detect format: 1.234,56 → european; 1,234.56 → US
        if re.search(r"\d\.\d{3},", value):
            value = value.replace(".", "").replace(",", ".")
        elif re.search(r"\d,\d{3}\.", value):
            value = value.replace(",", "")
        else:
            value = value.replace(",", ".")
        try:
            return float(value)
        except ValueError:
            return None

    # ── Currency ─────────────────────────────────────────────────────────────

    def detect_currency(self, text: str) -> str:
        """Return ISO currency code detected in text."""
        for symbol, code in _CURRENCY_MAP.items():
            if symbol in text.lower():
                return code
        return "EUR"

    def normalize_currency(self, code: str) -> str:
        return _CURRENCY_MAP.get(code.lower(), code.upper())

    def convert_to_eur(self, amount: float, currency: str) -> float:
        rate = _TO_EUR.get(self.normalize_currency(currency), 1.0)
        return round(amount * rate, 2)
