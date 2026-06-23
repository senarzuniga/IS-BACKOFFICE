"""
Agente 9: Analyst Agent
- Genera patrones, tendencias, comparativas, riesgos, oportunidades
"""

from typing import Dict, Any, List


class AnalystAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        knowledge = context.get('knowledge_built', [])
        plan = context.get('research_plan', {})
        
        if not knowledge:
            return {'analysis': 'No hay suficiente información para analizar.'}
        
        knowledge_text = '\n\n'.join([f"Fuente {i+1}: {k.summary}\n{k.content[:500]}" for i, k in enumerate(knowledge[:15])])
        prompt = f"""
Eres un analista estratégico senior. Basándote en la siguiente información extraída sobre {plan.get('target_company', 'el competidor')}, genera un análisis profundo.

INFORMACIÓN DISPONIBLE:
{knowledge_text}

OBJETIVO:
1. Identifica patrones y tendencias claras
2. Compara con INGECART (si tienes información)
3. Identifica riesgos para INGECART
4. Identifica oportunidades de negocio concretas
5. Genera un resumen ejecutivo de las conclusiones

RESPONDE EN FORMATO JSON:
{
  "patterns": ["Patrón 1", "Patrón 2"],
  "trends": ["Tendencia 1", "Tendencia 2"],
  "risks": [{"description": "...", "impact": "alto"}],
  "opportunities": [{"description": "...", "potential": "alto"}],
  "comparative_advantages": {
    "ingecart": ["Ventaja 1"],
    "competitor": ["Ventaja 1"]
  },
  "executive_summary": "Resumen en 3-4 frases"
}
"""
        analysis = self.llm.generate_json(prompt)
        context['analysis'] = analysis
        return analysis
