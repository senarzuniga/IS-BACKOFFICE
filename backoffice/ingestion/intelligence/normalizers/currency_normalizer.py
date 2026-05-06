"""Currency normaliser – converts any known currency to EUR."""
from __future__ import annotations


class CurrencyNormalizer:
    # Static FX rates (EUR base). Update as needed or inject a live feed.
    FX_TO_EUR: dict[str, float] = {
        "EUR": 1.0,
        "USD": 0.92,
        "GBP": 1.15,
        "CHF": 1.04,
        "JPY": 0.0062,
        "CNY": 0.128,
    }

    def normalize(self, value: float | None, currency: str | None) -> tuple[float | None, str]:
        if value is None:
            return None, "EUR"
        src = (currency or "EUR").upper()
        rate = self.FX_TO_EUR.get(src, 1.0)
        return round(value * rate, 2), "EUR"
