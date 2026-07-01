from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Tuple

from soc.brain.memory_store import MemoryStore


def _exists(conn: sqlite3.Connection, table: str, where: str, params: Tuple = ()) -> bool:
    cur = conn.cursor()
    q = f"SELECT 1 FROM {table} WHERE {where} LIMIT 1"
    cur.execute(q, params)
    return cur.fetchone() is not None


def populate(db_path: Path | str = None) -> None:
    store = MemoryStore(db_path=db_path)
    conn = store._conn()

    def ensure_company(name: str) -> str:
        c = store.get_company_by_name(name)
        if c:
            print(f"Company exists: {name} -> {c['uuid']}")
            return c['uuid']
        uid = store.add_company(name, source_ref='demo', owner='demo')
        print(f"Added company: {name} -> {uid}")
        return uid

    inge_uuid = ensure_company('Ingecart')
    iar_uuid = ensure_company('Industrial Augmented Reality')

    # Documents for Ingecart
    inge_docs = [
        ('customer_acme.txt', 'ACME Corp — customer profile: manufacturing, needs high throughput', '/demo/inge/customer_acme.txt'),
        ('customer_beta.txt', 'BETA SL — customer profile: e-commerce packaging provider', '/demo/inge/customer_beta.txt'),
        ('project_reel_sim.txt', 'Project: Reel Load Simulator — simulate throughput and failure modes', '/demo/inge/project_reel_sim.txt'),
        ('project_integration.txt', 'Project: Integration Pilot — integrate inspection and folding lines', '/demo/inge/project_integration.txt'),
        ('spec_sheet.txt', 'Specification sheet for MegaFold Pro — capacity 500 m/min', '/demo/inge/spec_sheet.txt'),
        ('case_study.txt', 'Case study: 15% throughput improvement after integration.', '/demo/inge/case_study.txt'),
    ]

    for fname, content, fpath in inge_docs:
        if not _exists(conn, 'documents', 'company_uuid=? AND file_name=?', (inge_uuid, fname)):
            store.add_document(inge_uuid, fname, content, file_path=fpath, source_ref='demo')
            print(f'Added document {fname} for Ingecart')
        else:
            print(f'Document {fname} already present for Ingecart')

    # Documents for IAR
    iar_docs = [
        ('customer_gamma.txt', 'GAMMA Ltd — AR integration for maintenance workflows', '/demo/iar/customer_gamma.txt'),
        ('customer_delta.txt', 'DELTA Inc — AR-assisted training for operators', '/demo/iar/customer_delta.txt'),
        ('project_ar_pilot.txt', 'Project: AR Pilot — overlay instructions on machine', '/demo/iar/project_ar_pilot.txt'),
        ('project_iot_bridge.txt', 'Project: IoT Bridge — sensor telemetry into AR', '/demo/iar/project_iot_bridge.txt'),
        ('iar_spec.txt', 'IAR spec: latency targets and SDK requirements', '/demo/iar/iar_spec.txt'),
        ('iar_case.txt', 'Case: reduced MTTR with AR-guided repairs', '/demo/iar/iar_case.txt'),
    ]

    for fname, content, fpath in iar_docs:
        if not _exists(conn, 'documents', 'company_uuid=? AND file_name=?', (iar_uuid, fname)):
            store.add_document(iar_uuid, fname, content, file_path=fpath, source_ref='demo')
            print(f'Added document {fname} for IAR')
        else:
            print(f'Document {fname} already present for IAR')

    # Decisions and risks (idempotent checks)
    decisions = [
        (inge_uuid, 'Adopt pilot for Line 3', 'Approve budget to pilot new integration on Line 3'),
        (inge_uuid, 'Standardize KPI collection', 'Mandate KPI collection for OEE and scrap rates'),
        (iar_uuid, 'Run AR pilot Q3', 'Approve AR pilot for maintenance use-case'),
        (iar_uuid, 'Integrate telemetry', 'Capture sensor telemetry for AR overlays'),
    ]

    for comp_uuid, title, content in decisions:
        if not _exists(conn, 'decisions', 'company_uuid=? AND title=?', (comp_uuid, title)):
            store.add_decision(comp_uuid, title, content, source_ref='demo')
            print(f'Added decision {title}')
        else:
            print(f'Decision {title} already exists')

    risks = [
        (inge_uuid, 'Supply chain delay', 'Lead time for rollers may increase by 8 weeks', 0.7, 0.6),
        (inge_uuid, 'Operator training', 'Operator ramp-up may extend commissioning time', 0.5, 0.5),
        (iar_uuid, 'Connectivity reliability', 'Network reliability may impact AR overlays', 0.6, 0.5),
        (iar_uuid, 'Data privacy', 'Customer data in AR sessions must be managed', 0.4, 0.3),
    ]

    for comp_uuid, title, desc, sev, prob in risks:
        if not _exists(conn, 'risks', 'company_uuid=? AND title=?', (comp_uuid, title)):
            store.add_risk(comp_uuid, title, desc, severity=sev, probability=prob)
            print(f'Added risk {title}')
        else:
            print(f'Risk {title} already exists')

    conn.close()


if __name__ == '__main__':
    populate()
