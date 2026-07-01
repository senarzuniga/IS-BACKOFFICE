#!/usr/bin/env python3
"""Quick test for ERP foundation: suppliers, projects, purchase orders, documents."""
from erp_facturacion import erp
from pathlib import Path

erp.init_db()

s_id = erp.add_supplier("Proveedor Test", nif="PT123")
print("Supplier created:", s_id)

p_id = erp.add_project("Proyecto Test", code="PRJ001", description="Prueba", budget=10000)
print("Project created:", p_id)

po = erp.create_purchase_order(po_number="PO-2026-001", po_date="2026-07-01", supplier_id=s_id, project_id=p_id, subtotal=5000, iva=1050, total=6050)
print("PO created:", po)

# add a document
from pathlib import Path
p = Path(__file__).resolve()
doc_id = erp.add_document("policy", "test_doc", str(p), source="local", tags="test")
print("Doc added:", doc_id)
