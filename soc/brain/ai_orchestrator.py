from __future__ import annotations

from typing import Dict, List, Optional

from .context_router import ContextRouter
from .local_search import LocalSearch
from .llm_adapter import MockLLMAdapter
from .evidence import collect_evidence
from .fact_checker import assess_evidence


class AIOrchestrator:
    """High-level orchestrator that builds context and requests an LLM response.

    This implementation uses the MockLLMAdapter and local search layers to
    demonstrate the pipeline without external API calls.
    """

    def __init__(self, context_router: ContextRouter, local_search: LocalSearch, llm_adapter: Optional[MockLLMAdapter] = None) -> None:
        self.context_router = context_router
        self.local_search = local_search
        self.llm = llm_adapter or MockLLMAdapter()

    def run(self, company_name: str, question: str, k: int = 6) -> Dict:
        # Resolve context
        company = self.context_router.resolve(company_name)
        company_uuid = company.get('uuid') if company else None

        # Fetch local evidence
        local_results = self.local_search.search(company_uuid, question, limit=k)

        # For now memory_results are empty — placeholder for future memory queries
        memory_results: List[Dict] = []

        evidence = collect_evidence(memory_results, local_results, top_k=k)
        assessment = assess_evidence(evidence)

        prompt = f"Question: {question}\nContext Company: {company_name}"
        llm_response = self.llm.generate(prompt, evidence)

        result = {
            'company': company_name,
            'company_uuid': company_uuid,
            'question': question,
            'llm': llm_response,
            'evidence': evidence,
            'assessment': assessment,
        }
        return result
