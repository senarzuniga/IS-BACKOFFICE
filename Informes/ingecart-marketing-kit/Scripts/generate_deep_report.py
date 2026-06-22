#!/usr/bin/env python3
"""
Deep report generator: multi-channel search, multi-agent scraping cascade,
consolidation into a local JSON DB, validation pass, and final HTML report
with Ingecart dark theme (black background, white body text, orange accents).

This is a simplified, deterministic implementation that simulates cascade
searches using the existing local research files and web fetch placeholders.
#!/usr/bin/env python3
"""
Advanced Deep Report Generator

Implements:
- Multi-channel evidence collection (local files + web crawling + news seeds)
- Multi-agent/cascade crawling: discovered links seed further crawls until
  no new sources are found or limits are reached
- Consolidation into SQLite DB with de-duplication and scoring
- Validation pass to remove low-quality evidence
- Synthesis and final dark-themed HTML report (Ingecart orange accents)

This script is intentionally opinionated: deep reports MUST perform cascade
searches and consolidation before rendering the final report.
"""

import argparse
import os
import json
import datetime
import hashlib
import requests
import sqlite3
import time
import logging
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse


DEFAULT_MAX_URLS = 120
DEFAULT_MAX_ITER = 4
DEFAULT_CONCURRENCY = 6
KEYWORDS = [
    'automat', 'automation', 'automatización', 'palletiz', 'stacker', 'retrofit',
    'digital', 'digitalización', 'ia', 'ai', 'predict', 'maintenance', 'mantenimiento',
    'robot', 'integración', 'integration', 'oem', 'palletizer', 'machine', 'service',
    'optim', 'roi', 'dashboard', 'saas', 'planta'
]


def sha1(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def load_local_research(paths, max_files=500):
    items = []
    seen = set()
    for root in paths:
        if not os.path.exists(root):
            continue
        for dirpath, dirs, files in os.walk(root):
            for f in files:
                ext = f.lower().split('.')[-1]
                if ext not in ('md', 'txt', 'html', 'json', 'htm'):
                    continue
                path = os.path.join(dirpath, f)
                if path in seen:
                    continue
                seen.add(path)
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        text = fh.read()
                except Exception:
                    continue
                items.append({
                    'id': sha1(path),
                    'source': path,
                    'title': f,
                    'snippet': text[:4000],
                    'content': text
                })
                if len(items) >= max_files:
                    return items
    return items


def fetch_url(url, timeout=8):
    headers = {'User-Agent': 'IngecartDeepBot/1.0 (+https://ingecart.com)'}
    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        logging.debug('fetch failed %s: %s', url, e)
        return None
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    desc = ''
    dtag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if dtag and dtag.get('content'):
        desc = dtag.get('content').strip()
    paragraphs = ' '.join([p.get_text(separator=' ', strip=True) for p in soup.find_all('p')])
    snippet = (desc or paragraphs)[:4000]
    links = set()
    base = url
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        try:
            new = urljoin(base, href)
        except Exception:
            continue
        parsed = urlparse(new)
        if parsed.scheme not in ('http', 'https'):
            continue
        if any(parsed.path.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.svg', '.css', '.js')):
            continue
        links.add(new)
    return {'url': url, 'title': title, 'snippet': snippet, 'links': list(links), 'fetched_at': datetime.datetime.utcnow().isoformat() + 'Z'}


def cascade_search(seeds, max_urls=DEFAULT_MAX_URLS, max_iter=DEFAULT_MAX_ITER, concurrency=DEFAULT_CONCURRENCY):
    discovered = set()
    queue = list(dict.fromkeys(seeds))
    results = []
    iter_num = 0
    while queue and iter_num < max_iter and len(discovered) < max_urls:
        logging.info('Cascade iter %s queue=%s discovered=%s', iter_num, len(queue), len(discovered))
        to_fetch = []
        while queue and len(to_fetch) < concurrency * 2 and len(discovered) + len(to_fetch) < max_urls:
            candidate = queue.pop(0)
            if candidate in discovered:
                continue
            to_fetch.append(candidate)
        if not to_fetch:
            break
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = {ex.submit(fetch_url, url): url for url in to_fetch}
            for fut in as_completed(futures):
                url = futures[fut]
                try:
                    res = fut.result()
                except Exception as e:
                    logging.debug('fetch exception %s', e)
                    res = None
                discovered.add(url)
                if res:
                    results.append(res)
                    for link in res['links']:
                        if link not in discovered and link not in queue and len(discovered) + len(queue) < max_urls:
                            queue.append(link)
        iter_num += 1
    return results


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS evidence (
        id TEXT PRIMARY KEY,
        url TEXT,
        source TEXT,
        title TEXT,
        snippet TEXT,
        content TEXT,
        score REAL,
        added_at TEXT
    )
    ''')
    conn.commit()
    return conn


def compute_score(item):
    text = (item.get('snippet') or '') + ' ' + (item.get('content') or '')
    base = min(len(text) / 1000.0, 1.0)
    kw_count = 0
    tl = text.lower()
    for kw in KEYWORDS:
        if kw in tl:
            kw_count += 1
    score = base + 0.18 * min(kw_count, 6)
    return round(score, 3)


def upsert_evidence(conn, item):
    key_source = item.get('url') or item.get('source') or item.get('title') or ''
    id = sha1(key_source)
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    score = compute_score(item)
    cur = conn.cursor()
    cur.execute('SELECT id FROM evidence WHERE id=?', (id,))
    if cur.fetchone():
        cur.execute('UPDATE evidence SET url=?, source=?, title=?, snippet=?, content=?, score=?, added_at=? WHERE id=?',
                    (item.get('url'), item.get('source'), item.get('title'), item.get('snippet'), item.get('content'), score, now, id))
    else:
        cur.execute('INSERT INTO evidence (id,url,source,title,snippet,content,score,added_at) VALUES (?,?,?,?,?,?,?,?)',
                    (id, item.get('url'), item.get('source'), item.get('title'), item.get('snippet'), item.get('content'), score, now))
    conn.commit()
    return id


def validate_and_extract(conn, min_score=0.2):
    cur = conn.cursor()
    cur.execute('SELECT id,url,source,title,snippet,content,score,added_at FROM evidence WHERE score>=? ORDER BY score DESC', (min_score,))
    rows = cur.fetchall()
    result = []
    for r in rows:
        obj = {'id': r[0], 'url': r[1], 'source': r[2], 'title': r[3], 'snippet': r[4], 'content': r[5], 'score': r[6], 'added_at': r[7]}
        result.append(obj)
    return result


def synthesize_summary(items, company):
    counts = {}
    for item in items:
        txt = (item.get('snippet') or '') + ' ' + (item.get('content') or '')
        tl = txt.lower()
        for kw in KEYWORDS:
            if kw in tl:
                counts[kw] = counts.get(kw, 0) + 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:6]
    top_list = ', '.join([k for k, _ in top]) if top else 'no significant themes detected'
    n_sources = len(items)
    summary = f'Informe profundo para {company}. Fuentes consolidadas: {n_sources}. Temas principales: {top_list}.'
    recs = []
    tl_keys = ' '.join(counts.keys())
    if 'retrofit' in tl_keys or 'retrofit' in tl_keys:
        recs.append('Priorizar retrofit y soluciones brownfield con ROI rápido.')
    if any(k in tl_keys for k in ('digital', 'digitalización', 'digitalizacion', 'ia', 'ai', 'predict', 'dashboard', 'saas')):
        recs.append('Invertir en plataforma Smart Plant (dashboard + SaaS) y capacidades IA.')
    if any(k in tl_keys for k in ('integration', 'integración', 'oem')):
        recs.append('Desarrollar oferta de integración multi-OEM y consultoría de optimización.')
    if not recs:
        recs.append('Realizar proyectos piloto centrados en ROI y escalado de servicios digitales.')
    return {'summary': summary, 'recommendations': recs, 'top_themes': top}


def render_final_html(company, validated_items, output_path, brand_css='../BrandGuidelines/ingecart_dark_brand.css'):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    synth = synthesize_summary(validated_items, company)
    known = ['PARA', 'Ingecart', 'Emba', 'Fosber', 'BHS', 'Vestergaard', 'Alliance Machine']
    comp_map = []
    for name in known:
        scores = []
        for it in validated_items:
            txt = (it.get('snippet') or '') + ' ' + (it.get('content') or '')
            if name.lower() in txt.lower():
                scores.append(it['score'])
        avg = round(sum(scores) / len(scores), 3) if scores else 0
        comp_map.append({'company': name, 'presence_score': avg})
    html = []
    html.append('<!doctype html>')
    html.append('<html lang="es">')
    html.append('<head>')
    html.append('<meta charset="utf-8">')
    html.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    html.append(f'<title>{company} — Deep Strategic Report</title>')
    html.append(f'<link rel="stylesheet" href="{brand_css}">')
    html.append('<style>')
    html.append('body{background:#000;color:#fff;font-family:Inter,Segoe UI,Arial;margin:0;padding:0}')
    html.append('.wrap{max-width:1200px;margin:18px auto;padding:24px}')
    html.append('header{display:flex;align-items:center;gap:12px;margin-bottom:18px}')
    html.append('.logo{height:48px}')
    html.append('h1{margin:0;font-size:28px}')
    html.append('h2{color:var(--inge-orange,#ff6a00);margin-top:22px;margin-bottom:8px}')
    html.append('.card{background:#0b0b0b;border:1px solid #111;padding:14px;border-radius:10px;margin-bottom:12px}')
    html.append('.meta{color:#bbb;font-size:0.9em;margin-bottom:8px}')
    html.append('.snippet{color:#eee}')
    html.append('table{width:100%;border-collapse:collapse;margin-top:8px}')
    html.append('th,td{padding:8px;border-bottom:1px solid #222;text-align:left}')
    html.append('a{color:var(--inge-orange,#ff6a00)}')
    html.append('</style>')
    html.append('</head>')
    html.append('<body>')
    html.append('<div class="wrap">')
    logo_path = '../Assets/ingecart_assets_v2/logo%20ingecart%20blanco.png'
    html.append(f'<header><div><h1>{company} — Deep Strategic Report</h1><div class="meta">Generado: {now}</div></div></header>')
    html.append('<section class="card">')
    html.append('<h2>Executive Summary</h2>')
    html.append(f'<p>{synth["summary"]}</p>')
    html.append('<ul>')
    for r in synth['recommendations']:
        html.append(f'<li>{r}</li>')
    html.append('</ul>')
    html.append('</section>')
    html.append('<section class="card">')
    html.append('<h2>Key Themes (evidence-driven)</h2>')
    html.append('<div>')
    if synth['top_themes']:
        html.append('<ul>')
        for k, c in synth['top_themes']:
            html.append(f'<li><strong>{k}</strong>: {c} mentions</li>')
        html.append('</ul>')
    else:
        html.append('<p>No prominent themes detected.</p>')
    html.append('</div>')
    html.append('</section>')
    html.append('<section class="card">')
    html.append('<h2>Competitive Map (presence score)</h2>')
    html.append('<table><thead><tr><th>Company</th><th>Presence Score</th></tr></thead><tbody>')
    for row in comp_map:
        html.append(f'<tr><td>{row["company"]}</td><td>{row["presence_score"]}</td></tr>')
    html.append('</tbody></table>')
    html.append('</section>')
    html.append('<section class="card">')
    html.append('<h2>Consolidated Evidence (validated sources)</h2>')
    for it in validated_items:
        src = it.get('url') or it.get('source') or 'local'
        title = it.get('title') or src
        snippet = it.get('snippet') or (it.get('content') or '')[:500]
        html.append('<div class="card">')
        html.append(f'<strong>{title}</strong>')
        html.append(f'<div class="meta">{src} — score: {it.get("score")}</div>')
        html.append(f'<div class="snippet">{snippet}</div>')
        if it.get('url'):
            html.append(f'<div><a href="{it["url"]}" target="_blank">Open source</a></div>')
        html.append('</div>')
    html.append('</section>')
    html.append('<section class="card">')
    html.append('<h2>Conclusion & Next Steps</h2>')
    html.append('<ol>')
    html.append('<li>Validate top recommendations with pilot projects and ROI tracking.</li>')
    html.append('<li>Develop Smart Plant MVP: dashboard + predictive maintenance pilot.</li>')
    html.append('<li>Build retrofit offer and sales playbook for brownfield plants.</li>')
    html.append('</ol>')
    html.append('</section>')
    html.append('<footer style="color:#777;text-align:center;margin-top:18px;">Generated by Ingecart Deep Report Generator</footer>')
    html.append('</div>')
    html.append('</body>')
    html.append('</html>')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    print(output_path)


def try_load_json_input(company, repo_data_dir):
    candidate = os.path.join(repo_data_dir, f'{company.lower()}_bcg_input.json')
    if os.path.exists(candidate):
        try:
            with open(candidate, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            return None
    return None


def run_pipeline(company, seeds=None, max_urls=DEFAULT_MAX_URLS, max_iter=DEFAULT_MAX_ITER, concurrency=DEFAULT_CONCURRENCY, no_web=False):
    script_dir = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))
    data_dir = os.path.join(os.path.dirname(script_dir), 'Data')
    os.makedirs(data_dir, exist_ok=True)

    # 1) local research (Informes folder + backoffice research)
    local_paths = [os.path.join(repo_root, 'Informes'), os.path.join(repo_root, 'research'), os.path.join(repo_root, 'backoffice')]
    local = load_local_research(local_paths)

    # 2) web cascade
    web_results = []
    if not no_web:
        actual_seeds = seeds or []
        if not actual_seeds:
            cname = company.lower()
            actual_seeds = [f'https://{cname}.com', f'https://www.{cname}.com']
        # run cascade
        web_results = cascade_search(actual_seeds, max_urls=max_urls, max_iter=max_iter, concurrency=concurrency)

    # 3) consolidate into SQLite DB
    db_path = os.path.join(data_dir, f'{company.lower()}_deep.db')
    conn = init_db(db_path)
    # save local items first
    for l in local:
        upsert_evidence(conn, l)
    # then web results
    for w in web_results:
        upsert_evidence(conn, {'url': w.get('url'), 'title': w.get('title'), 'snippet': w.get('snippet'), 'content': ''})

    # 4) validation
    validated = validate_and_extract(conn, min_score=0.25)

    # 5) final render
    out_html = os.path.join(os.path.dirname(script_dir), 'Analysis', f'{company}_Deep_Report.html')
    render_final_html(company, validated, out_html)


def main():
    parser = argparse.ArgumentParser(description='Advanced deep strategic report generator (cascade + DB + synthesis + dark HTML)')
    parser.add_argument('--company', '-c', required=True)
    parser.add_argument('--seed-urls', '-s', nargs='*', help='Seed URLs to start web cascade (optional)')
    parser.add_argument('--no-web', action='store_true', help='Skip web fetching and use local research only')
    parser.add_argument('--max-urls', type=int, default=DEFAULT_MAX_URLS)
    parser.add_argument('--max-iter', type=int, default=DEFAULT_MAX_ITER)
    parser.add_argument('--concurrency', type=int, default=DEFAULT_CONCURRENCY)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    run_pipeline(args.company, seeds=args.seed_urls, max_urls=args.max_urls, max_iter=args.max_iter, concurrency=args.concurrency, no_web=args.no_web)


if __name__ == '__main__':
    main()
