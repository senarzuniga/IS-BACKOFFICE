"""
Agente 6: Knowledge Builder
Agente 7: Enrichment Agent
- Construye base de conocimiento del proyecto
- Enriquece con entidades, categorías, relaciones
"""

import hashlib
from typing import Dict, Any, List
from datetime import datetime
from ..models.data_models import KnowledgeItem, Source
from ..models.data_models import SourceLevel


class KnowledgeBuilder:
    def __init__(self, memory, llm_client):
        self.memory = memory
        self.llm = llm_client
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        validated = context.get('validated_data', [])
        plan = context.get('research_plan', {})
        project = f"{plan.get('target_company', 'unknown')}_analysis"
        
        knowledge_items = []
        for item in validated:
            if item.get('is_valid', False):
                ki = self._build_knowledge_item(item, project)
                knowledge_items.append(ki)
                try:
                    self.memory.save_knowledge(ki)
                except Exception as e:
                    print(f"Error saving knowledge: {e}")
        
        context['knowledge_built'] = knowledge_items
        return {'items_created': len(knowledge_items)}
    
    def _build_knowledge_item(self, validated_item: Dict, project: str) -> KnowledgeItem:
        url = validated_item.get('url', '')
        text = validated_item.get('text_preview', '')
        content_hash = hashlib.md5(f"{url}_{text[:100]}".encode()).hexdigest()[:12]
        level_val = int(validated_item.get('level', 3))
        try:
            level = SourceLevel(level_val)
        except Exception:
            level = SourceLevel.LEVEL_3
        source = Source(
            url=url,
            title=f"Scraped content from {url}",
            level=level,
            confidence=validated_item.get('confidence', 0.5)
        )
        enrichment = self._enrich(text, url)
        return KnowledgeItem(
            id=f"ki_{content_hash}",
            title=enrichment.get('title', 'Sin título'),
            category=enrichment.get('category', 'general'),
            subcategory=enrichment.get('subcategory', ''),
            summary=enrichment.get('summary', text[:200]),
            content=text,
            sources=[source],
            tags=enrichment.get('tags', []),
            entities=enrichment.get('entities', []),
            relationships=[],
            confidence=validated_item.get('confidence', 0.5),
            validated=validated_item.get('confidence', 0.5) > 0.7,
            project=project
        )
    
    def _enrich(self, text: str, url: str) -> Dict[str, Any]:
        prompt = f"""
Analiza el siguiente contenido web y extrae información estructurada.

URL: {url}
TEXTO (primeros 2000 caracteres):
{text[:2000]}

Genera un JSON con:
{
  "title": "Título extraído o inferido",
  "category": "Categoría principal (corrugado, automatización, empresa, finanzas, tecnología, mercado, soporte)",
  "subcategory": "Subcategoría específica",
  "summary": "Resumen del contenido en 1-2 frases",
  "tags": ["tag1", "tag2", ...],
  "entities": [{"type": "company|person|technology|product|amount|date", "value": "..."}]
}
"""
        try:
            return self.llm.generate_json(prompt)
        except Exception:
            return {
                'title': 'Sin título extraído',
                'category': 'general',
                'subcategory': '',
                'summary': text[:200],
                'tags': ['desconocido'],
                'entities': []
            }
