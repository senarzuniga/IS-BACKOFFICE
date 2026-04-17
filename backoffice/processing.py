from __future__ import annotations

from .models import ProcessingResult, RawRecord


class DataProcessingCleaningLayer:
    CURRENCY_MAP = {"usd": "USD", "$": "USD", "eur": "EUR", "€": "EUR"}

    def process(self, records: list[RawRecord]) -> ProcessingResult:
        seen = set()
        cleaned: list[RawRecord] = []
        dropped = 0
        missing_fields: list[str] = []
        validation_errors: list[str] = []

        for record in records:
            key = (record.source_id, record.content.lower())
            if key in seen:
                dropped += 1
                continue
            seen.add(key)

            if not record.content:
                missing_fields.append(f"empty_content:{record.source_id}")
                continue

            normalized = " ".join(record.content.split())
            normalized = normalized.replace("US$", "USD ").replace("usd", "USD")
            normalized = normalized.replace("eur", "EUR")
            for k, v in self.CURRENCY_MAP.items():
                normalized = normalized.replace(f" {k} ", f" {v} ")

            if "value=" in normalized.lower():
                frag = normalized.lower().split("value=", 1)[1].split()[0].rstrip(",.;")
                try:
                    float(frag)
                except ValueError:
                    validation_errors.append(f"invalid_value:{record.source_id}:{frag}")

            record.content = normalized
            cleaned.append(record)

        return ProcessingResult(
            cleaned_records=cleaned,
            dropped_duplicates=dropped,
            missing_fields=missing_fields,
            validation_errors=validation_errors,
        )
