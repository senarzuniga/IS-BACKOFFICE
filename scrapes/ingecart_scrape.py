#!/usr/bin/env python3
"""Scrape and structure content from a landing page.

Usage:
  python scrapes/ingecart_scrape.py --url <URL> --output-dir scrapes/ingecart_proyectos

Produces:
  - JSON report: <output-dir>/report.json
  - Markdown report: <output-dir>/report.md
  - Downloaded images: <output-dir>/assets/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
    # sanitize
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


def parse_page(soup: BeautifulSoup, base_url: str) -> Dict:
    data: Dict = {}
    data["url"] = base_url

    # Basic metadata
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    m = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if m and m.get("content"):
        meta_desc = m.get("content").strip()
    data.update({"title": title, "meta_description": meta_desc})

    # Navigation and CTAs
    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        links.append({"text": text_of(a), "href": href})
    data["links"] = links

    # Collect images
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        full = urljoin(base_url, src)
        images.append({"src": full, "alt": img.get("alt") or "", "title": img.get("title") or ""})
    data["images"] = images

    # Find headings and structure projects by region
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5"])
    regions: List[Dict] = []
    current_region: Optional[Dict] = None

    # heuristic: short uppercase headings are regions (e.g., USA, EUROPE)
    def is_region_text(t: str) -> bool:
        if not t:
            return False
        t = t.strip()
        if len(t) > 20:
            return False
        # treat numeric headings as non-regions
        if any(c.isdigit() for c in t):
            return False
        # uppercase or short single word
        return t.isupper() or (" " not in t and len(t) <= 6)

    # iterate headings to build structure
    for i, h in enumerate(headings):
        htext = text_of(h)
        if not htext:
            continue

        if is_region_text(htext):
            current_region = {"region": htext, "projects": []}
            regions.append(current_region)
            continue

        # treat as a project entry if it's an H3 or H4 or longer text
        level = int(h.name[1:]) if h.name and h.name[1:].isdigit() else 0
        if level >= 3 or (level >= 2 and len(htext) < 80):
            # description: search next siblings for paragraphs or small text blocks
            desc_parts = []
            link = None
            img = None
            for sib in h.next_siblings:
                if getattr(sib, "name", None) and sib.name and sib.name.startswith("h"):
                    break
                if getattr(sib, "name", None) and sib.name == "p":
                    t = text_of(sib)
                    if t:
                        desc_parts.append(t)
                if getattr(sib, "name", None) and sib.name == "a" and sib.get("href"):
                    link = urljoin(base_url, sib.get("href"))
                # find images nearby
                imgs = []
                try:
                    imgs = sib.find_all("img") if hasattr(sib, "find_all") else []
                except Exception:
                    imgs = []
                if imgs:
                    img = urljoin(base_url, imgs[0].get("src") or imgs[0].get("data-src") or "")

            project = {"title": htext, "description": " ".join(desc_parts).strip(), "link": link, "image": img}
            if current_region is None:
                # put into a default region
                current_region = {"region": "Main", "projects": []}
                regions.append(current_region)
            current_region["projects"].append(project)

    data["regions"] = regions

    # Company numbers: try to capture big numeric counters
    numbers = {}
    for el in soup.find_all():
        txt = text_of(el)
        if txt and re.fullmatch(r"\d{1,4}", txt):
            # look for a label near it
            label = None
            for sib in el.previous_siblings:
                if getattr(sib, "name", None) and sib.name and sib.name.startswith("h"):
                    label = text_of(sib)
                    break
            numbers[label or ""] = txt
    data["numbers"] = numbers

    # partners: images inside a partners section or near the word 'Partners'
    partners = []
    for sec in soup.find_all(lambda tag: tag.name in ["div", "section"] and "partner" in (tag.get("class") or []) ):
        for img in sec.find_all("img"):
            partners.append(urljoin(base_url, img.get("src") or img.get("data-src") or ""))

    # fallback: gather images with 'logo' in filename
    if not partners:
        for img in soup.find_all("img"):
            src = img.get("src") or ""
            if "logo" in src.lower() or "partner" in src.lower():
                partners.append(urljoin(base_url, src))

    data["partners"] = partners

    # footer contact info
    footer = {}
    footer_elem = soup.find("footer")
    if footer_elem:
        footer["text"] = text_of(footer_elem)
        footer["links"] = [urljoin(base_url, a["href"]) for a in footer_elem.find_all("a", href=True)]
    data["footer"] = footer

    return data


def generate_markdown(data: Dict, assets_subdir: str = "assets") -> str:
    lines: List[str] = []
    lines.append(f"# Scrape report for {data.get('title','(no title)')}")
    lines.append("")
    lines.append(f"Source: {data.get('url')}")
    lines.append("")
    if data.get("meta_description"):
        lines.append(f"**Meta description:** {data.get('meta_description')}")
        lines.append("")

    lines.append("## Regions & Projects")
    lines.append("")
    for region in data.get("regions", []):
        lines.append(f"### {region.get('region')}")
        lines.append("")
        for p in region.get("projects", []):
            lines.append(f"#### {p.get('title')}")
            if p.get("image"):
                fname = Path(p.get("image")).name
                lines.append(f"![{p.get('title')}]({assets_subdir}/{fname})")
            if p.get("description"):
                lines.append("")
                lines.append(p.get("description"))
            if p.get("link"):
                lines.append("")
                lines.append(f"[Link]({p.get('link')})")
            lines.append("")

    if data.get("partners"):
        lines.append("## Partners")
        lines.append("")
        for p in data.get("partners", []):
            fname = Path(p).name
            lines.append(f"![partner]({assets_subdir}/{fname})")
        lines.append("")

    if data.get("numbers"):
        lines.append("## Numbers")
        lines.append("")
        for k, v in data.get("numbers", {}).items():
            lines.append(f"- **{k or 'Metric'}**: {v}")
        lines.append("")

    if data.get("footer"):
        lines.append("## Footer")
        lines.append("")
        lines.append(data.get("footer").get("text", ""))
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Page URL to scrape")
    parser.add_argument("--output-dir", default="scrapes/ingecart_proyectos", help="Output directory")
    args = parser.parse_args()

    outdir = Path(args.output_dir)
    assets_dir = outdir / "assets"
    outdir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {args.url}")
    try:
        r = requests.get(args.url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"Error fetching {args.url}: {e}")
        sys.exit(2)

    soup = BeautifulSoup(r.text, "html.parser")
    data = parse_page(soup, args.url)

    # download images referenced in data['images'] and in project entries
    img_urls = set()
    for im in data.get("images", []):
        img_urls.add(im.get("src"))
    for reg in data.get("regions", []):
        for p in reg.get("projects", []):
            if p.get("image"):
                img_urls.add(p.get("image"))
    for p in data.get("partners", []):
        img_urls.add(p)

    downloaded = {}
    for url in sorted(u for u in img_urls if u):
        name = download_image(url, assets_dir)
        downloaded[url] = name

    # update data to include local image filenames
    for im in data.get("images", []):
        im["local"] = downloaded.get(im.get("src"))
    for reg in data.get("regions", []):
        for p in reg.get("projects", []):
            if p.get("image"):
                p["image_local"] = downloaded.get(p.get("image"))
    data["partners_local"] = [downloaded.get(u) for u in data.get("partners", [])]

    # write JSON
    json_path = outdir / "report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # write Markdown
    md = generate_markdown(data, assets_subdir="assets")
    md_path = outdir / "report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Wrote JSON: {json_path}")
    print(f"Wrote Markdown: {md_path}")
    print(f"Downloaded {len([v for v in downloaded.values() if v])} images to {assets_dir}")


if __name__ == "__main__":
    main()
