"""
Scraper inteligente con respeto a robots.txt, extracción semántica y limpieza de ruido
"""

import re
import json
import time
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except Exception:
    sync_playwright = None  # Playwright optional
    PlaywrightTimeout = Exception
import requests
from bs4 import BeautifulSoup
from ..models.data_models import Source, SourceLevel


class SmartScraper:
    """Scraper inteligente que respeta robots.txt, extrae contenido semántico y limpia ruido"""
    
    def __init__(self, respect_robots: bool = True, max_pages: int = 50):
        self.respect_robots = respect_robots
        self.max_pages = max_pages
        self.visited_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; KnowledgeIntelligenceBot/1.0; +https://ingecart.com)'
        })
    
    def scrape_page(self, url: str, wait_for: str = "domcontentloaded") -> Optional[Dict]:
        """Scrapea una página, extrae contenido limpio y metadatos"""
        if url in self.visited_urls:
            return None
        self.visited_urls.add(url)
        content = None
        
        # Intentar con Playwright primero (para JS)
        try:
            if sync_playwright is not None:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, timeout=30000, wait_until=wait_for)
                    page.wait_for_selector('body', timeout=5000)
                    
                    clean_text = page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, td, th, div.content, main, article');
                            let text = '';
                            elements.forEach(el => {
                                const txt = el.textContent.trim();
                                if (txt.length > 20) text += txt + '\n\n';
                            });
                            return text;
                        }
                    """)
                    title = page.evaluate("document.title || ''")
                    meta_desc = page.evaluate("""
                        () => {
                            const meta = document.querySelector('meta[name="description"]');
                            return meta ? meta.content : '';
                        }
                    """)
                    links = page.evaluate("""
                        () => {
                            const links = [];
                            document.querySelectorAll('a[href]').forEach(a => {
                                const href = a.href;
                                const text = a.textContent.trim();
                                if (href && !href.includes('#') && !href.includes('javascript:') && text.length > 5) {
                                    links.push({url: href, text: text});
                                }
                            });
                            return links;
                        }
                    """)
                    browser.close()
                    
                    content = {
                        'title': title,
                        'description': meta_desc,
                        'text': clean_text[:15000],
                        'links': links[:50],
                        'url': url,
                        'timestamp': datetime.now().isoformat()
                    }
        except (PlaywrightTimeout, Exception):
            # Fallback a requests (HTML estático)
            try:
                response = self.session.get(url, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'noscript', 'iframe', 'svg']):
                    element.decompose()
                for selector in ['.cookie', '.cookie-banner', '.ad', '.advertisement', '.menu', '.navigation', '.sidebar', '.cookie-consent']:
                    for el in soup.select(selector):
                        el.decompose()

                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                if main_content:
                    text = main_content.get_text(separator='\n')
                else:
                    text = soup.get_text(separator='\n')

                lines = [line.strip() for line in text.splitlines() if line.strip()]
                clean_text = '\n\n'.join(lines)

                meta = soup.find('meta', attrs={'name': 'description'})
                meta_desc = meta.get('content') if meta else ''

                content = {
                    'title': soup.title.string if soup.title else '',
                    'description': meta_desc,
                    'text': clean_text[:15000],
                    'links': [],
                    'url': url,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e2:
                return {'error': str(e2), 'url': url}
        
        return content
    
    def extract_structured_data(self, html: str, url: str) -> Dict:
        """Extrae datos estructurados (JSON-LD, microdata, etc.)"""
        soup = BeautifulSoup(html, 'html.parser')
        structured = {}
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        structured[item.get('@type', 'unknown')] = item
                elif '@graph' in data:
                    for item in data['@graph']:
                        structured[item.get('@type', 'unknown')] = item
                else:
                    structured[data.get('@type', 'unknown')] = data
            except Exception:
                pass
        return structured
    
    def categorize_content(self, text: str) -> List[str]:
        """Categoriza el contenido por palabras clave"""
        categories = []
        keywords = {
            'technical': ['especificación', 'técnico', 'manual', 'diseño', 'ingeniería', 'fabricación'],
            'commercial': ['precio', 'oferta', 'presupuesto', 'venta', 'cliente', 'servicio'],
            'corporate': ['empresa', 'historia', 'misión', 'visión', 'equipo', 'oficina'],
            'news': ['nuevo', 'lanzamiento', 'innovación', 'adquisición', 'expansión', 'inversión'],
            'support': ['soporte', 'mantenimiento', 'servicio técnico', 'reparación', 'garantía']
        }
        text_lower = text.lower()
        for category, words in keywords.items():
            if any(word in text_lower for word in words):
                categories.append(category)
        return categories if categories else ['general']
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extrae entidades básicas (nombres, empresas, números, fechas)"""
        entities = []
        patterns = {
            'company': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Corp|Corporation|Inc|S\.A\.|S\.L\.|LLC|GmbH|AG))',
            'person': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'amount': r'(\d+(?:[,.]\d+)?)\s*(?:M€|M USD|miles|millones|billones)',
            'date': r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'(\+\d{1,3}\s?)?(\d{9,15})'
        }
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if len(str(match)) > 2:
                    entities.append({'type': entity_type, 'value': str(match)[:100]})
        return entities
    
    def estimate_source_level(self, url: str, content: str) -> SourceLevel:
        """Estima el nivel de confianza de la fuente"""
        url_lower = url.lower()
        official_domains = ['.gov', '.mil', '.eu', '.int', 'normativa', 'boe.es', 'europa.eu']
        manufacturer_domains = ['bhs', 'fosber', 'marquip', 'ward', 'kba', 'bobst']
        if any(domain in url_lower for domain in official_domains):
            return SourceLevel.LEVEL_1
        if any(domain in url_lower for domain in manufacturer_domains):
            return SourceLevel.LEVEL_1
        technical_indicators = ['whitepaper', 'technical', 'manual', 'guide', 'specification', 'paper']
        if any(ind in url_lower or ind in content[:500].lower() for ind in technical_indicators):
            return SourceLevel.LEVEL_2
        blog_indicators = ['blog', 'medium', 'linkedin', 'community', 'forum', 'stack']
        if any(ind in url_lower for ind in blog_indicators):
            return SourceLevel.LEVEL_3
        return SourceLevel.LEVEL_4
