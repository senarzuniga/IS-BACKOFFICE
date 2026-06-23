"""
Agente 11: Technical Writer
- Redacta el informe completo usando información validada
- Nunca inventa: cada afirmación debe tener fuente
"""

from typing import Dict, Any
import json
from datetime import datetime


class TechnicalWriter:
    def __init__(self, llm_client, memory):
        self.llm = llm_client
        self.memory = memory
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        analysis = context.get('analysis', {})
        structure = context.get('report_structure', {})
        plan = context.get('research_plan', {})
        knowledge = context.get('knowledge_built', [])
        gaps = context.get('gaps', [])
        
        knowledge_summary = '\n\n'.join([f"### Fuente: {k.title}\n{k.summary}" for k in knowledge[:10]])
        prompt = f"""
Eres un Technical Writer especializado en informes de inteligencia competitiva de nivel BCG/McKinsey.
Redacta un informe profesional basándote en los datos validados.

ESTRUCTURA DEL INFORME:
{json.dumps(structure, indent=2)}

DATOS DEL ANÁLISIS:
{json.dumps(analysis, indent=2)}

RESUMEN DEL CONOCIMIENTO VALIDADO:
{knowledge_summary}

LAGUNAS DE INFORMACIÓN (deben mencionarse explícitamente):
{json.dumps(gaps, indent=2)}

REGLAS ESTRICTAS:
1. NO inventes datos. Si falta información, di "No disponible en fuentes públicas".
2. Cada afirmación importante debe ir seguida de "(Fuente: [origen])".
3. El informe debe ser en Markdown, con formato profesional.
4. Incluye tablas comparativas donde sea posible.
5. Añade un resumen ejecutivo al inicio y conclusiones al final.
6. Sé objetivo y basado en evidencia.

GENERA EL INFORME COMPLETO EN MARKDOWN.
"""
        report = self.llm.generate(prompt)
        context['draft_report'] = report
        from pathlib import Path
        report_dir = Path('data/knowledge_intelligence/reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        filename = report_dir / f"report_{plan.get('target_company', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        context['report_file'] = str(filename)
        return {'report': report, 'file': str(filename)}
