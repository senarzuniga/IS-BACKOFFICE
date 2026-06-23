"""
Agente 8: Gap Analysis Agent
- Detecta lagunas de información
- Si hay lagunas críticas, activa más investigaciones
- NO permite redactar informe hasta que la base esté completa
"""

from typing import Dict, Any, List


class GapAnalysisAgent:
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.MAX_ITERATIONS = 3
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        plan = context.get('research_plan', {})
        knowledge = context.get('knowledge_built', [])
        
        gaps = self._identify_gaps(plan, knowledge)
        critical_gaps = [g for g in gaps if g.get('critical', False)]
        
        context['gaps'] = gaps
        context['critical_gaps'] = critical_gaps
        
        if critical_gaps and context.get('iteration', 0) < self.MAX_ITERATIONS:
            context['iteration'] = context.get('iteration', 0) + 1
            context['needs_more_research'] = True
            context['research_queries'] = [g['query'] for g in critical_gaps]
        else:
            context['needs_more_research'] = False
        
        return {
            'total_gaps': len(gaps),
            'critical_gaps': len(critical_gaps),
            'needs_more_research': len(critical_gaps) > 0,
            'gaps': gaps
        }
    
    def _identify_gaps(self, plan: Dict, knowledge: List) -> List[Dict]:
        required = plan.get('required_information', [])
        areas = plan.get('areas', [])
        existing_text = ' '.join([k.content[:1000] for k in knowledge]) if knowledge else ''
        gaps = []
        for req in required:
            if req.lower() not in existing_text.lower():
                gaps.append({
                    'area': req,
                    'critical': 'finanzas' in req.lower() or 'estrategia' in req.lower(),
                    'query': f"información sobre {req} {plan.get('target_company', '')}"
                })
        if not gaps and not knowledge:
            gaps.append({
                'area': 'Información general del competidor',
                'critical': True,
                'query': f"perfil corporativo {plan.get('target_company', '')}"
            })
        return gaps
