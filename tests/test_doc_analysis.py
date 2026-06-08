"""Tests independientes por capa (capa 12). Ejecutar con: pytest tests/test_doc_analysis.py -v"""
from __future__ import annotations
import asyncio, json
from pathlib import Path
import pytest

from utils.doc_memory import CorporateMemory, KnowledgeGraph, Fact
from utils.doc_agents import AnalistaDocumentalAgent, InvestigadorWebAgent, AuditorAgent, AgentTask
from utils.doc_intelligence import MultiLLMConsensusEngine
from utils.doc_orchestrator import MultiAgentOrchestrator


def test_capa3_memory_persistence(tmp_path):
    """Capa 3: memoria guarda, recupera y persiste."""
    m = CorporateMemory()
    fid = m.save_fact(Fact(id="t1", statement="Cliente ACME facturó 5M€ en Q1",
                            confidence=0.9, sources=[]))
    assert fid in m.facts
    related = m.find_related("ACME facturación")
    assert any(r["id"] == fid for r in related)
    assert m.stats()["total_facts"] >= 1


def test_capa4_graph_upsert_link():
    """Capa 4: grafo upsert + link + búsqueda."""
    g = KnowledgeGraph()
    a = g.upsert_entity("ACME", "cliente", {"sector": "industrial"})
    b = g.upsert_entity("Proyecto X", "proyecto")
    g.link(a, b, "owns")
    assert g.find("ACME") is not None
    assert g.stats()["total_entities"] >= 2
    assert g.stats()["total_relationships"] >= 1


def test_capa5_agents_run():
    """Capa 5: los 3 agentes ejecutan sin errores."""
    m = CorporateMemory(); g = KnowledgeGraph()
    a = AnalistaDocumentalAgent(m, g)
    i = InvestigadorWebAgent(m, g)
    u = AuditorAgent(m, g)
    r1 = asyncio.run(a.run(AgentTask(documents=[])))
    r2 = asyncio.run(i.run(AgentTask(documents=[], entity="ACME")))
    r3 = asyncio.run(u.run(AgentTask(documents=[], entity="")))
    assert r1["agent"] == "Analista Documental"
    assert r2["agent"] == "Investigador Web"
    assert r3["agent"] == "Auditor"


def test_capa6_consensus_parallel():
    """Capa 6: consensus engine con circuit breaker."""
    eng = MultiLLMConsensusEngine()
    r = asyncio.run(eng.analyze("contenido de prueba", "analyze"))
    assert "consensus" in r
    assert len(r["models_used"]) >= 3


def test_capa7_parser_natural_language():
    """Capa 7: parser NL detecta intent, path y entity."""
    o = MultiAgentOrchestrator()
    p = o._parse('Analiza "C:\\Clientes\\PCM_Mexico" benchmark PCM vs Cascades')
    assert p["intent"] == "benchmark"
    assert "PCM" in (p["entity"] or "")
    assert "Clientes" in (p["path"] or "")


def test_capa10_idempotent_reload():
    """Capa 10: sistema es idempotente (re-cargar no duplica grafo)."""
    MultiAgentOrchestrator()
    g1 = KnowledgeGraph().stats()["total_entities"]
    MultiAgentOrchestrator()
    g2 = KnowledgeGraph().stats()["total_entities"]
    assert g1 == g2
