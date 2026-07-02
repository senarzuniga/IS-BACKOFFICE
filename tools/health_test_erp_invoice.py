#!/usr/bin/env python3
"""Create a test client and invoice to verify ERP invoice generation."""
from erp_facturacion import erp
from pathlib import Path

erp.init_db()
client_id = erp.add_client(
    company_name="HealthCheck Co",
    nif="HC123456",
    address="Test address",
    city="TestCity",
)
print("Created client_id:", client_id)

res = erp.create_invoice(
    client_id=client_id,
    invoice_date="2026-07-01",
    due_date="2026-07-15",
    payment_method="Transferencia",
    lines=[{"description": "Health check service", "qty": 1, "unit_price": 123.45}],
    expenses=[],
    iva_rate=0.21,
    irpf_rate=0.0,
    notes="Health check invoice",
)
print("Invoice created:", res.get('invoice_number'))
print("PDF path:", res.get('pdf_path'))
pdf_path = Path(res.get('pdf_path'))
print("PDF exists:", pdf_path.exists())
