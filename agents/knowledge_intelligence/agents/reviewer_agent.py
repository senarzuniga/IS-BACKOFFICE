"""
Agente 12: Reviewer Agent
- Actúa como auditor
- Comprueba coherencia, contradicciones, claridad, trazabilidad
"""

from typing import Dict, Any


class ReviewerAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        draft = context.get('draft_report', '')
        knowledge = context.get('knowledge_built', [])
        
        if not draft:
            return {'review': 'No hay borrador para revisar.'}
        prompt = f"""
Eres un revisor senior de informes de estrategia. Revisa críticamente el siguiente borrador de informe.

BORRADOR:
{draft}

CRITERIOS DE REVISIÓN:
1. Coherencia interna
2. Claridad y estructura
3. Trazabilidad
4. Gramática y estilo profesional
5. Uso de datos

Genera un informe de revisión con:
- Puntuación general (1-10)
- Aspectos mejorables (lista)
- Aspectos positivos (lista)
- Recomendaciones concretas para mejorar

RESPONDE EN FORMATO JSON
"""
        review = self.llm.generate_json(prompt)
        context['review'] = review
        return review
