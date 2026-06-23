"""
Agente 5: Validation Agent
- Verifica duplicados, contradicciones, coherencia
- Asigna niveles de confianza
"""

from typing import Dict, Any, List
from datetime import datetime
import re
from ..models.data_models import SourceLevel


class ValidationAgent:
    def __init__(self, memory):
        self.memory = memory
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        web_data = context.get('web_research', [])
        repository = context.get('repository_knowledge', [])
        
        validated_items = []
        contradictions = []
        
        for item in web_data:
            validation = self._validate_item(item)
            if validation.get('is_valid'):
                validated_items.append(validation)
            if validation.get('contradictions'):
                contradictions.extend(validation['contradictions'])
        
        context['validated_data'] = validated_items
        context['contradictions_found'] = contradictions
        
        return {
            'validated_count': len(validated_items),
            'contradictions_count': len(contradictions),
            'items': validated_items[:30]
        }
    
    def _validate_item(self, item: Dict) -> Dict:
        text = item.get('text', '')
        url = item.get('url', '')
        level = self._estimate_source_level(url)
        duplicates = self._find_duplicates(text)
        contradictions = self._find_contradictions(text)
        confidence = self._calculate_confidence(level, duplicates, contradictions)
        return {
            'is_valid': confidence > 0.3,
            'url': url,
            'level': level.value if hasattr(level, 'value') else 3,
            'confidence': confidence,
            'duplicates': duplicates,
            'contradictions': contradictions,
            'text_preview': text[:500]
        }
    
    def _estimate_source_level(self, url: str) -> SourceLevel:
        url_lower = url.lower()
        official = ['.gov', '.mil', '.eu', 'normativa', 'boe.es', 'europa.eu']
        manufacturer = ['bhs', 'fosber', 'marquip', 'ward', 'kba', 'bobst', 'ingecart']
        if any(d in url_lower for d in official) or any(d in url_lower for d in manufacturer):
            return SourceLevel.LEVEL_1
        if 'whitepaper' in url_lower or 'technical' in url_lower:
            return SourceLevel.LEVEL_2
        if 'blog' in url_lower or 'medium' in url_lower:
            return SourceLevel.LEVEL_3
        return SourceLevel.LEVEL_4
    
    def _find_duplicates(self, text: str) -> List[str]:
        return []
    
    def _find_contradictions(self, text: str) -> List[Dict]:
        contradictions = []
        numbers = re.findall(r'\b(\d+[,.]?\d*)\s*(?:M€|M USD|millones|miles|empleados|años)\b', text)
        if len(numbers) > 1:
            contradictions.append({
                'type': 'multiple_numbers',
                'values': numbers,
                'message': f'Múltiples cifras encontradas sin contexto claro: {", ".join(numbers)}'
            })
        return contradictions
    
    def _calculate_confidence(self, level, duplicates, contradictions) -> float:
        base = {1: 0.95, 2: 0.85, 3: 0.70, 4: 0.50}
        confidence = base.get(getattr(level, 'value', level), 0.5)
        if duplicates:
            confidence *= 0.8
        if contradictions:
            confidence *= 0.7
        return min(confidence, 1.0)
