"""Capa 7: Orquestador multiagente con parser de lenguaje natural."""
from __future__ import annotations
import re
import shlex
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

from utils.doc_memory import CorporateMemory, KnowledgeGraph
from utils.doc_agents import (AnalistaDocumentalAgent, InvestigadorWebAgent,
                                AuditorAgent, AgentTask)
from utils.doc_intelligence import MultiLLMConsensusEngine


class MultiAgentOrchestrator:
    EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".csv", ".md", ".eml", ".msg"}

    def __init__(self) -> None:
        self.memory = CorporateMemory()
        self.graph = KnowledgeGraph()
        self.analista = AnalistaDocumentalAgent(self.memory, self.graph)
        self.investigador = InvestigadorWebAgent(self.memory, self.graph)
        self.auditor = AuditorAgent(self.memory, self.graph)
        self.consensus = MultiLLMConsensusEngine()

    async def execute(self, command: str, progress: Callable[[str], None] = None) -> Dict:
        parsed = self._parse(command)
        if progress: progress(f"🎯 Intent: **{parsed['intent']}**")
        if progress: progress(f"📂 Path: `{parsed.get('path') or '—'}` · Entidad: `{parsed.get('entity') or '—'}`")

        documents: List[Path] = []
        if parsed.get("path"):
            documents = self._discover(parsed["path"])
            if progress: progress(f"📁 Documentos: {len(documents)}")

        results: Dict = {}
        if documents:
            results["analista"] = await self.analista.run(AgentTask(documents=documents), progress)
        if parsed.get("entity"):
            results["investigador"] = await self.investigador.run(
                AgentTask(documents=[], entity=parsed["entity"]), progress)
        if results.get("analista"):
            facts_blob = ". ".join(results["analista"].get("facts_sample", []))
            web_results = results.get("investigador", {}).get("results", [])
            results["auditor"] = await self.auditor.run(
                AgentTask(documents=[], entity=facts_blob), progress)

        if progress: progress("🧠 Generando consenso multi-LLM…")
        consensus = await self.consensus.analyze(
            content=str(results)[:8000], task_type=parsed["intent"])

        return {
            "command": command, "parsed": parsed, "results": results,
            "consensus": consensus,
            "memory_stats": self.memory.stats(),
            "graph_stats": self.graph.stats(),
            "report": self._report(parsed, results, consensus),
        }

    def _parse(self, command: str) -> Dict:
        p = {"original": command, "intent": "analyze", "path": None, "entity": None,
             "output_format": "executive_report"}
        # Detectar path Windows (entrecomillado o sin comillas)
        m = re.search(r'"([A-Z]:\\[^\"]+)"', command) or re.search(r"'([A-Z]:\\[^']+)'", command) \
            or re.search(r'\b([A-Z]:\\[\w\-\.\\ ]+)', command)
        if m: p["path"] = m.group(1).strip().rstrip('"\'')
        low = command.lower()
        for kw, intent in [("benchmark", "benchmark"), ("due diligence", "due_diligence"),
                           ("comparativ", "benchmark"), ("informe", "analyze")]:
            if kw in low: p["intent"] = intent; break
        for ent in ["PCM", "Cascades", "WestRock", "Smurfit Kappa", "Ingercart", "INGECART",
                    "Saica", "Monterrey", "México", "Tetra Pak", "PSC Visalia"]:
            if ent.lower() in low: p["entity"] = ent; break
        if "powerpoint" in low or " ppt" in low: p["output_format"] = "powerpoint"
        elif "word" in low or ".docx" in low: p["output_format"] = "word"
        return p

    def _discover(self, path_str: str) -> List[Path]:
        root = Path(path_str)
        if not root.exists(): return []
        return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in self.EXTENSIONS]

    def _report(self, parsed: Dict, results: Dict, consensus: Dict) -> str:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        analista = results.get("analista", {})
        investigador = results.get("investigador", {})
        auditor = results.get("auditor", {})
        ents = analista.get("entities", [])
        by_type: Dict[str, List[str]] = {}
        for e in ents:
            by_type.setdefault(e["type"], []).append(e["value"])
        ent_lines = [f"### {t}\n" + "\n".join(f"- `{v}`" for v in vs[:15])
                     for t, vs in by_type.items()] or ["_Ninguna_"]
        return f"""# 📊 Informe Ejecutivo
**Generado:** {ts}  
**Comando:** `{parsed['original']}`  
**Intent:** {parsed['intent']}

## 📈 Resumen
- Documentos procesados: **{analista.get('documents_processed', 0)}**
- Entidades detectadas: **{len(ents)}**
- Hechos extraídos: **{analista.get('facts_extracted', 0)}**
- Verificación: **{auditor.get('verification_rate', 0)*100:.0f}%**
- Memoria: **{results and self.memory.stats()['total_facts']} hechos**
- Grafo: **{self.graph.stats()['total_entities']} entidades**

## 🧠 Consenso Multi-LLM
{consensus.get('consensus', 'N/A')}

## 🏷️ Entidades Detectadas
{chr(10).join(ent_lines)}

## ✅ Hechos Verificados
{chr(10).join(f"- {v['statement'][:200]}" for v in auditor.get('verified', [])[:10]) or "_Ninguno_"}

## ⚠️ Inconsistencias
{chr(10).join(f"- {v['statement'][:200]}" for v in auditor.get('inconsistencies', [])[:10]) or "✅ Ninguna"}

## 🌐 Fuentes Web Consultadas
{chr(10).join(f"- [{r['title']}]({r['url']})" for r in investigador.get('results', [])[:5]) or "_Ninguna_"}
"""
