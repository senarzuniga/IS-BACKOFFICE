import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def get_company_context(company, web_hint=None):
    """Busca información relevante de la empresa en la web."""
    context = []
    # 1. Buscar web oficial si no está
    if not web_hint or pd.isna(web_hint):
        query = f"{company} sitio oficial"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        context.append(f"Buscar web oficial: {url}")
    else:
        context.append(f"Web: {web_hint}")
        # 2. Intentar obtener descripción de la web
        try:
            resp = requests.get(web_hint, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            desc = ''
            if soup.title:
                desc += f"Título: {soup.title.text}. "
            meta = soup.find('meta', attrs={'name': 'description'})
            if meta and meta.get('content'):
                desc += f"Descripción: {meta['content']}"
            if desc:
                context.append(desc)
        except Exception as e:
            context.append(f"No se pudo obtener descripción web: {e}")
    # 3. Buscar noticias recientes
    news_url = f"https://www.google.com/search?q={company.replace(' ', '+')}+noticias"
    context.append(f"Noticias: {news_url}")
    return ' | '.join(context)

# Cargar leads
leads = pd.read_csv('scripts/leads_fespa2026_temp.csv', skiprows=1)

# Completar y enriquecer
for idx, row in leads.iterrows():
    company = row['Empresa'] if not pd.isna(row['Empresa']) else ''
    web = row['Web'] if 'Web' in row and not pd.isna(row['Web']) else None
    context = get_company_context(company, web)
    leads.at[idx, 'Company Context'] = context
    time.sleep(1)  # Evitar bloqueos

leads.to_excel('scripts/leads_fespa2026_enriched.xlsx', index=False)
print('Archivo enriquecido generado: scripts/leads_fespa2026_enriched.xlsx')
