"""Data validation rules."""
from __future__ import annotations
import re
from typing import List, Tuple, Any

ValidationResult = Tuple[bool, List[str]]


class Validator:
    """Validates data fields and returns (is_valid, list_of_errors)."""

    def validate_number(self, value: Any, field_name: str = "value",
                        min_val: float = 0.0, max_val: float = 1e12) -> ValidationResult:
        errors = []
        if value is None:
            errors.append(f"{field_name} is missing")
            return False, errors
        try:
            num = float(value)
        except (ValueError, TypeError):
            errors.append(f"{field_name} is not a valid number: {value!r}")
            return False, errors
        if num < min_val:
            errors.append(f"{field_name}={num} is below minimum {min_val}")
        if num > max_val:
            errors.append(f"{field_name}={num} exceeds maximum {max_val}")
        return len(errors) == 0, errors

    def validate_email(self, email: str) -> ValidationResult:
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if re.match(pattern, email or ""):
            return True, []
        return False, [f"Invalid email: {email!r}"]

    def validate_required(self, data: dict, required_fields: List[str]) -> ValidationResult:
        errors = [f"Missing required field: {f}" for f in required_fields if not data.get(f)]
        return len(errors) == 0, errors

    def validate_currency(self, currency: str) -> ValidationResult:
        valid = {"EUR", "USD", "GBP", "JPY", "MAD", "CHF", "CAD", "AUD"}
        if (currency or "").upper() in valid:
            return True, []
        return False, [f"Unknown currency: {currency!r}"]
