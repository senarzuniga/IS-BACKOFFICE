"""
Agente 10: Report Architect
- Diseña la estructura del informe
"""

from typing import Dict, Any


class ReportArchitect:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        plan = context.get('research_plan', {})
        structure = {
            "sections": [
                {"title": "Executive Summary", "level": 1},
                {"title": "Objectives", "level": 1},
                {"title": "Metodología", "level": 1},
                {"title": f"Perfil de {plan.get('target_company', 'el competidor')}", "level": 1},
                {"title": "Análisis de Mercado y Tendencias", "level": 1},
                {"title": "Benchmarking vs INGECART", "level": 1},
                {"title": "Riesgos y Amenazas", "level": 1},
                {"title": "Oportunidades Estratégicas", "level": 1},
                {"title": "Conclusiones y Recomendaciones", "level": 1},
                {"title": "Fuentes y Anexos", "level": 1}
            ]
        }
        context['report_structure'] = structure
        return structure
