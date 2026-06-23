"""
Agente 13: Executive Summary Agent
- Genera únicamente el resumen ejecutivo, conclusiones y recomendaciones
"""

from typing import Dict, Any
import json


class ExecutiveSummaryAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        analysis = context.get('analysis', {})
        report = context.get('draft_report', '')
        prompt = f"""
Eres un consultor experto en resúmenes ejecutivos de nivel Consejo de Administración.

ANÁLISIS REALIZADO:
{json.dumps(analysis, indent=2)}

BORRADOR COMPLETO DEL INFORME:
{report[:3000]}...

Genera únicamente la sección de Executive Summary del informe, que debe contener:
1. Contexto y objetivo de la investigación
2. Principales hallazgos (3-5 puntos clave)
3. Conclusiones principales
4. Recomendaciones prioritarias (máximo 5)

EL RESULTADO DEBE SER CONCISO, IMPACTANTE Y EN MARKDOWN.
"""
        summary = self.llm.generate(prompt)
        context['executive_summary'] = summary
        return {'summary': summary}
