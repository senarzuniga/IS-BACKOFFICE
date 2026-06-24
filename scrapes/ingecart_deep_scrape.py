#!/usr/bin/env python3
"""Deep scraper using Playwright to render JS and extract structured project data.

Features:
- Renders the page with Playwright (Chromium)
- Finds project card containers that include both a heading and an image
- Optionally follows each project link (depth=1) to capture detail text and images
- Downloads images and writes JSON + Markdown reports
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup


def safe_filename(url: str, default_ext: str = ".jpg") -> str:
    p = urlparse(url)
    name = unquote(Path(p.path).name)
    if not name:
        name = hashlib.sha1(url.encode()).hexdigest() + default_ext
    if not Path(name).suffix:
        name = name + default_ext
    name = re.sub(r"[^A-Za-z0-9._-]", "-", name)
    return name


def download_image(url: str, out_dir: Path) -> Optional[str]:
    try:
        resp = requests.get(url, stream=True, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[WARN] Failed to download image {url}: {e}")
        return None
    fname = safe_filename(url)
    path = out_dir / fname
    try:
        with open(path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
    except Exception as e:
        print(f"[WARN] Error saving image {url} -> {path}: {e}")
        return None
    return str(path.name)


def text_of(elem) -> str:
    if elem is None:
        return ""
    return " ".join(elem.get_text(separator=" ", strip=True).split())


def extract_projects_from_container(container, base_url: str) -> List[Dict]:
    projects = []
    seen = set()
    for tag in container.find_all(lambda t: t.find(['h1', 'h2', 'h3', 'h4', 'h5']) and t.find('img')):
        title_tag = tag.find(['h1', 'h2', 'h3', 'h4', 'h5'])
        title = text_of(title_tag)
        if not title:
            continue
        if title in seen:
            continue
        seen.add(title)

        img_tag = tag.find('img')
        img_src = urljoin(base_url, img_tag.get('src') or img_tag.get('data-src') or '') if img_tag else None

        # description: first paragraph or small text found inside
        desc = ''
        p = tag.find('p') or tag.find('div')
        if p:
            desc = text_of(p)

        # link: prefer anchors wrapping the heading or inside tag
        link = None
        a_wrap = title_tag.find_parent('a') if title_tag else None
        if a_wrap and a_wrap.get('href'):
            link = urljoin(base_url, a_wrap.get('href'))
        else:
            a = tag.find('a', href=True)
            if a:
                link = urljoin(base_url, a.get('href'))

        projects.append({'title': title, 'description': desc, 'link': link, 'image': img_src})

    return projects


def find_project_section(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    # Look for headers containing 'project' (case-insensitive) and return a nearby container
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
        if 'project' in text_of(h).lower() or 'proyecto' in text_of(h).lower():
            # prefer a section or div parent
            parent = h.find_parent(['section', 'div'])
            return parent or h
    # fallback: return the whole body
    return soup.body or soup


def is_internal_link(link: str, base_domain: str) -> bool:
    if not link:
        return False
    try:
        p = urlparse(link)
        if not p.netloc:
            return True
        return base_domain in p.netloc
    except Exception:
        return False


def run(url: str, output_dir: Path, follow_links: bool = True, max_follow: int = 12) -> None:
    from playwright.sync_api import sync_playwright

    outdir = output_dir
    assets_dir = outdir / 'assets'
    outdir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    base_domain = urlparse(url).netloc

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        # set a common user agent to reduce bot blocking
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        context = browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.set_default_navigation_timeout(120000)
        print(f"Loading {url} in headless browser...")

        soup = None
        # Try networkidle first, then fall back to domcontentloaded, then requests
        try:
            page.goto(url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(1000)
            # try scrolling to trigger lazy loading
            try:
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(500)
            except Exception:
                pass
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            print(f"[WARN] networkidle navigation failed: {e}. Retrying with domcontentloaded...")
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(1000)
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
            except Exception as e2:
                print(f"[WARN] domcontentloaded navigation failed: {e2}. Falling back to requests GET...")
                try:
                    import requests as _req

                    html = _req.get(url, timeout=20).text
                    soup = BeautifulSoup(html, 'html.parser')
                except Exception as e3:
                    print(f"[ERROR] Unable to load page by any method: {e3}")
                    soup = BeautifulSoup('<html></html>', 'html.parser')

        section = find_project_section(soup)
        if section is None:
            section = soup

        projects = extract_projects_from_container(section, url)

        # If none found by container heuristic, fallback to scanning whole page
        if not projects:
            projects = extract_projects_from_container(soup, url)

        # Optionally follow links to get details
        followed = 0
        for p in projects:
            if follow_links and p.get('link') and followed < max_follow and is_internal_link(p.get('link'), base_domain):
                try:
                    print(f"Following link: {p.get('link')}")
                    detail_page = context.new_page()
                    try:
                        detail_page.goto(p.get('link'), wait_until='domcontentloaded', timeout=60000)
                        detail_page.wait_for_timeout(800)
                        dhtml = detail_page.content()
                        dsoup = BeautifulSoup(dhtml, 'html.parser')
                        main = dsoup.find('main') or dsoup.find('article') or dsoup.body
                        p['detail_text'] = text_of(main)
                        # gather images from detail page (first few)
                        imgs = []
                        for im in (main.find_all('img') if main else [])[:5]:
                            src = urljoin(p.get('link'), im.get('src') or im.get('data-src') or '')
                            imgs.append(src)
                        p['detail_images'] = imgs
                    except Exception as dex:
                        print(f"[WARN] detail page navigation failed for {p.get('link')}: {dex}")
                    finally:
                        try:
                            detail_page.close()
                        except Exception:
                            pass
                    followed += 1
                except Exception as e:
                    print(f"[WARN] Failed to fetch detail page {p.get('link')}: {e}")

        try:
            browser.close()
        except Exception:
            pass

    # download images
    img_urls = set()
    for p in projects:
        if p.get('image'):
            img_urls.add(p.get('image'))
        for di in p.get('detail_images', []) if p.get('detail_images') else []:
            img_urls.add(di)

    downloaded = {}
    for u in sorted([x for x in img_urls if x]):
        name = download_image(u, assets_dir)
        downloaded[u] = name

    # attach local names
    for p in projects:
        if p.get('image'):
            p['image_local'] = downloaded.get(p.get('image'))
        if p.get('detail_images'):
            p['detail_images_local'] = [downloaded.get(x) for x in p.get('detail_images')]

    data = {
        'url': url,
        'title': text_of(soup.title) if soup.title else '',
        'projects': projects,
    }

    json_path = outdir / 'report.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Markdown
    md_lines = [f"# Deep scrape report for {data.get('title')}", '', f"Source: {url}", '']
    for p in projects:
        md_lines.append(f"## {p.get('title')}")
        if p.get('image_local'):
            md_lines.append(f"![{p.get('title')}]({assets_dir.name}/{p.get('image_local')})")
        if p.get('description'):
            md_lines.append('', p.get('description'))
        if p.get('link'):
            md_lines.append('', f"[Link]({p.get('link')})")
        if p.get('detail_text'):
            md_lines.append('', p.get('detail_text')[:1000] + ('...' if len(p.get('detail_text')) > 1000 else ''))
        md_lines.append('')

    md_path = outdir / 'report.md'
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')

    print(f"Deep scrape complete. Wrote: {json_path} and {md_path}. Downloaded {len([v for v in downloaded.values() if v])} images")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output-dir', default='scrapes/ingecart_proyectos_deep')
    parser.add_argument('--no-follow', dest='follow', action='store_false')
    parser.add_argument('--max-follow', type=int, default=12)
    args = parser.parse_args()

    run(args.url, Path(args.output_dir), follow_links=args.follow, max_follow=args.max_follow)


if __name__ == '__main__':
    main()
