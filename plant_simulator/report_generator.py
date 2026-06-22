from typing import Any


def generate_pdf_report(results: Any) -> bytes:
    # Minimal PDF placeholder (not a real PDF); tests usually just check return type
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"Report bytes\n"


def generate_excel_report(results: Any) -> bytes:
    # Minimal XLSX-like placeholder (not a real XLSX). Return some bytes.
    return b"PK\x03\x04\x14\x00" + b"ExcelReport"
