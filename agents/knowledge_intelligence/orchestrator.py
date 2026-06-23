"""
Orquestador del sistema de inteligencia de conocimiento
Gestiona el flujo completo de los 13 agentes con iteraciones para llenar gaps
"""

import time
from typing import Callable, Dict, Any
from .utils.llm_client import LLMClient
from .memory.knowledge_memory import KnowledgeMemory
from .agents.research_manager import ResearchManager
from .agents.repository_agent import RepositoryKnowledgeAgent
from .agents.web_research_agent import WebResearchAgent
from .agents.validation_agent import ValidationAgent
from .agents.knowledge_builder import KnowledgeBuilder
from .agents.gap_analysis_agent import GapAnalysisAgent
from .agents.analyst_agent import AnalystAgent
from .agents.report_architect import ReportArchitect
from .agents.technical_writer import TechnicalWriter
from .agents.reviewer_agent import ReviewerAgent
from .agents.executive_summary_agent import ExecutiveSummaryAgent


class KnowledgeOrchestrator:
    def __init__(self, llm_client: LLMClient, memory: KnowledgeMemory, search_paths: list, progress_callback: Callable = None):
        self.llm = llm_client
        self.memory = memory
        self.search_paths = search_paths
        self.progress_callback = progress_callback
        self.context = {}
        self.max_iterations = 3
    
    def run(self, request: str) -> Dict[str, Any]:
        self._log("🔄 Iniciando proceso de inteligencia de conocimiento", 0)
        self.context = {'request': request, 'iteration': 0, 'needs_more_research': True}
        self._log("🧠 Agente 1: Research Manager - Planificando investigación", 5)
        rm = ResearchManager(self.llm)
        self.context['research_plan'] = rm.run(request, self.context)
        while self.context.get('needs_more_research', False) and self.context.get('iteration', 0) < self.max_iterations:
            self._run_research_cycle()
        self._log("📊 Agente 9: Analyst Agent - Generando análisis", 75)
        analyst = AnalystAgent(self.llm)
        self.context['analysis'] = analyst.run(self.context)
        self._log("📐 Agente 10: Report Architect - Estructurando informe", 80)
        architect = ReportArchitect(self.llm)
        self.context['report_structure'] = architect.run(self.context)
        self._log("✍️ Agente 11: Technical Writer - Redactando informe", 85)
        writer = TechnicalWriter(self.llm, self.memory)
        self.context.update(writer.run(self.context))
        self._log("🔍 Agente 12: Reviewer Agent - Revisando informe", 92)
        reviewer = ReviewerAgent(self.llm)
        self.context['review'] = reviewer.run(self.context)
        self._log("📌 Agente 13: Executive Summary Agent - Generando resumen", 97)
        es = ExecutiveSummaryAgent(self.llm)
        self.context['executive_summary'] = es.run(self.context)
        self._log("✅ Proceso completado", 100)
        return self.context
    
    def _run_research_cycle(self):
        iteration = self.context.get('iteration', 0) + 1
        self.context['iteration'] = iteration
        self._log(f"🔄 Ciclo de investigación #{iteration}", 10 + (iteration * 10))
        self._log("📁 Agente 2: Buscando en repositorio local", 10 + (iteration * 10))
        repo_agent = RepositoryKnowledgeAgent(self.search_paths, self.memory)
        self.context.update(repo_agent.run(self.context))
        self._log("🌐 Agente 3+4: Investigando en web", 20 + (iteration * 10))
        web_agent = WebResearchAgent(self.llm)
        self.context.update(web_agent.run(self.context))
        self._log("✅ Agente 5: Validando información", 30 + (iteration * 10))
        val_agent = ValidationAgent(self.memory)
        self.context.update(val_agent.run(self.context))
        self._log("🧩 Agente 6+7: Construyendo y enriqueciendo conocimiento", 40 + (iteration * 10))
        kb_agent = KnowledgeBuilder(self.memory, self.llm)
        self.context.update(kb_agent.run(self.context))
        self._log("🔎 Agente 8: Analizando lagunas de información", 50 + (iteration * 10))
        gap_agent = GapAnalysisAgent(self.llm)
        gap_result = gap_agent.run(self.context)
        self.context['gaps'] = gap_result.get('gaps', [])
        self.context['critical_gaps'] = gap_result.get('critical_gaps', [])
        self.context['needs_more_research'] = gap_result.get('needs_more_research', False)
        if self.context['needs_more_research']:
            self._log(f"⚠️ Lagunas críticas detectadas. Continuando investigación...", 55 + (iteration * 10))
    
    def _log(self, message: str, progress: float):
        if self.progress_callback:
            self.progress_callback(message, progress)
        print(f"{message} ({progress:.0f}%)")
