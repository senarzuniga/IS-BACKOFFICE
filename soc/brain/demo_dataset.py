from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from .memory_store import MemoryStore


def build_demo_store(db_path: Path | str = None) -> Tuple[MemoryStore, Dict[str, str]]:
    """Create a small synthetic dataset for two demo companies.

    Returns (MemoryStore, mapping_of_company_name_to_uuid)
    """
    db_path = Path(db_path) if db_path else None
    store = MemoryStore(db_path=db_path)

    mapping: Dict[str, str] = {}

    # Company A: Ingecart
    inge_uuid = store.add_company('Ingecart', source_ref='demo', owner='demo')
    mapping['Ingecart'] = inge_uuid

    # Company B: Industrial Augmented Reality (IAR)
    iar_uuid = store.add_company('Industrial Augmented Reality', source_ref='demo', owner='demo')
    mapping['Industrial Augmented Reality'] = iar_uuid

    # Populate Ingecart: 2 customers, 2 projects, 2 decisions, 2 risks, 2 documents
    store.add_document(inge_uuid, 'customer_acme.txt', 'ACME Corp — customer profile: manufacturing, needs high throughput', file_path='/demo/inge/customer_acme.txt', source_ref='demo')
    store.add_document(inge_uuid, 'customer_beta.txt', 'BETA SL — customer profile: e-commerce packaging provider', file_path='/demo/inge/customer_beta.txt', source_ref='demo')

    store.add_document(inge_uuid, 'project_reel_sim.txt', 'Project: Reel Load Simulator — simulate throughput and failure modes', file_path='/demo/inge/project_reel_sim.txt', source_ref='demo')
    store.add_document(inge_uuid, 'project_integration.txt', 'Project: Integration Pilot — integrate inspection and folding lines', file_path='/demo/inge/project_integration.txt', source_ref='demo')

    store.add_decision(inge_uuid, 'Adopt pilot for Line 3', 'Approve budget to pilot new integration on Line 3', source_ref='demo')
    store.add_decision(inge_uuid, 'Standardize KPI collection', 'Mandate KPI collection for OEE and scrap rates', source_ref='demo')

    # Risks: insert into risks table directly using optional convenience method if available
    try:
        # MemoryStore may implement add_risk
        add_risk = getattr(store, 'add_risk', None)
        if callable(add_risk):
            add_risk(inge_uuid, 'Supply chain delay', 'Lead time for rollers may increase by 8 weeks', severity=0.7, probability=0.6)
            add_risk(inge_uuid, 'Operator training', 'Operator ramp-up may extend commissioning time', severity=0.5, probability=0.5)
        else:
            # fallback: store as documents tagged as risk
            store.add_document(inge_uuid, 'risk_supply.txt', 'Risk: Supply chain delay — roller lead times', file_path='/demo/inge/risk_supply.txt', source_ref='demo', meta={'type': 'risk'})
            store.add_document(inge_uuid, 'risk_training.txt', 'Risk: Operator training — ramp-up issues', file_path='/demo/inge/risk_training.txt', source_ref='demo', meta={'type': 'risk'})
    except Exception:
        # keep demo creation resilient
        pass

    store.add_document(inge_uuid, 'spec_sheet.txt', 'Specification sheet for MegaFold Pro — capacity 500 m/min', file_path='/demo/inge/spec_sheet.txt', source_ref='demo')
    store.add_document(inge_uuid, 'case_study.txt', 'Case study: 15% throughput improvement after integration.', file_path='/demo/inge/case_study.txt', source_ref='demo')

    # Populate IAR similarly
    store.add_document(iar_uuid, 'customer_gamma.txt', 'GAMMA Ltd — AR integration for maintenance workflows', file_path='/demo/iar/customer_gamma.txt', source_ref='demo')
    store.add_document(iar_uuid, 'customer_delta.txt', 'DELTA Inc — AR-assisted training for operators', file_path='/demo/iar/customer_delta.txt', source_ref='demo')

    store.add_document(iar_uuid, 'project_ar_pilot.txt', 'Project: AR Pilot — overlay instructions on machine', file_path='/demo/iar/project_ar_pilot.txt', source_ref='demo')
    store.add_document(iar_uuid, 'project_iot_bridge.txt', 'Project: IoT Bridge — sensor telemetry into AR', file_path='/demo/iar/project_iot_bridge.txt', source_ref='demo')

    store.add_decision(iar_uuid, 'Run AR pilot Q3', 'Approve AR pilot for maintenance use-case', source_ref='demo')
    store.add_decision(iar_uuid, 'Integrate telemetry', 'Capture sensor telemetry for AR overlays', source_ref='demo')

    try:
        if callable(add_risk):
            add_risk(iar_uuid, 'Connectivity reliability', 'Network reliability may impact AR overlays', severity=0.6, probability=0.5)
            add_risk(iar_uuid, 'Data privacy', 'Customer data in AR sessions must be managed', severity=0.4, probability=0.3)
        else:
            store.add_document(iar_uuid, 'risk_connectivity.txt', 'Risk: Connectivity — AR overlays degrade with poor networks', file_path='/demo/iar/risk_connectivity.txt', source_ref='demo', meta={'type': 'risk'})
            store.add_document(iar_uuid, 'risk_privacy.txt', 'Risk: Privacy — session data retention concerns', file_path='/demo/iar/risk_privacy.txt', source_ref='demo', meta={'type': 'risk'})
    except Exception:
        pass

    store.add_document(iar_uuid, 'iar_spec.txt', 'IAR spec: latency targets and SDK requirements', file_path='/demo/iar/iar_spec.txt', source_ref='demo')
    store.add_document(iar_uuid, 'iar_case.txt', 'Case: reduced MTTR with AR-guided repairs', file_path='/demo/iar/iar_case.txt', source_ref='demo')

    return store, mapping
