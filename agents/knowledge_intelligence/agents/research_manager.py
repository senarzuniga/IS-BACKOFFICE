"""
Agente 1: Research Manager
- Entiende la solicitud del usuario
- Genera objetivos, preguntas clave, plan de investigación
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from ..models.data_models import ResearchPlan
from ..utils.llm_client import LLMClient


class ResearchManager:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def run(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
Eres un Research Manager experto en inteligencia competitiva del sector del cartón corrugado, automatización industrial y maquinaria.

SOLICITUD DEL USUARIO:
{request}

OBJETIVO: Generar un plan de investigación estructurado para abordar esta solicitud.

Debes identificar:
1. Empresa objetivo (si se menciona)
2. Competidores relevantes
3. Áreas clave a investigar (ej: tecnología, mercado, finanzas, soporte, presencia global)
4. Preguntas clave que deben responderse
5. Información específica que se necesita recopilar
6. Consultas de búsqueda sugeridas para web scraping

RESPONDE EXCLUSIVAMENTE EN FORMATO JSON con esta estructura:
{
  "objective": "Objetivo principal de la investigación",
  "target_company": "Nombre de la empresa objetivo o null",
  "competitors": ["Lista de competidores relevantes"],
  "areas": ["Área1", "Área2", ...],
  "key_questions": ["Pregunta1", "Pregunta2", ...],
  "required_information": ["Info1", "Info2", ...],
  "search_queries": ["Consulta de búsqueda 1", "Consulta 2", ...],
  "context": "Contexto adicional entendido de la solicitud"
}
"""
        response = self.llm.generate_json(prompt)
        context['research_plan'] = response
        return response
