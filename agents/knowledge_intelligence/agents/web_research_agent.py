"""
Agente 3 + 4: Web Research & Scraping Agent
- Realiza búsquedas en internet
- Scrapea páginas web
- Extrae información estructurada
- Nunca interpreta, solo recopila
"""

import time
from urllib.parse import quote_plus
from typing import List, Dict, Any
from datetime import datetime
from ..utils.smart_scraper import SmartScraper


class WebResearchAgent:
    def __init__(self, llm_client=None, use_serpapi: bool = False, serpapi_key: str = None):
        self.llm = llm_client
        self.scraper = SmartScraper()
        self.use_serpapi = use_serpapi
        self.serpapi_key = serpapi_key
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        research_plan = context.get('research_plan', {})
        queries = research_plan.get('search_queries', [])
        target = research_plan.get('target_company', '')
        
        if not queries and target:
            queries = [
                f"{target} corrugated cardboard automation",
                f"{target} corrugator converting",
                f"{target} company profile revenue",
                f"{target} technology patents innovation",
                f"{target} market position competitors",
            ]
        
        all_results = []
        for query in queries[:10]:
            print(f"🔍 Buscando: {query}")
            urls = self._search(query)
            for url in urls[:5]:
                content = self.scraper.scrape_page(url)
                if content and content.get('text') and len(content['text']) > 200:
                    content['query'] = query
                    all_results.append(content)
                time.sleep(0.5)
        context['web_research'] = all_results
        return {'pages_scraped': len(all_results), 'results': all_results[:50]}
    
    def _search(self, query: str) -> List[str]:
        urls = []
        if self.use_serpapi and self.serpapi_key:
            try:
                import requests
                params = {'q': query, 'api_key': self.serpapi_key, 'num': 10}
                response = requests.get('https://serpapi.com/search.json', params=params, timeout=10)
                data = response.json()
                for result in data.get('organic_results', []):
                    if result.get('link'):
                        urls.append(result['link'])
            except Exception as e:
                print(f"SerpAPI error: {e}")
        if not urls:
            try:
                import requests
                from bs4 import BeautifulSoup
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(f'https://www.google.com/search?q={quote_plus(query)}', headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                for a in soup.select('a[href]'):
                    href = a.get('href')
                    if href and href.startswith('/url?q='):
                        url = href.split('/url?q=')[1].split('&')[0]
                        if url.startswith('http') and not url.startswith('https://www.google'):
                            urls.append(url)
            except Exception:
                pass
        return urls[:10]
