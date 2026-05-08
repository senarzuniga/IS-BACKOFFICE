"""
Ingecart asset pack generator.

What this script does:
1) Stores a curated list of image/logo URLs as code (ASSET_CATALOG).
2) Downloads each asset to a local folder for portability.
3) Generates a local HTML gallery so assets can be opened easily on any machine.

Usage:
    python research/ingecart/ingecart_assets_pack.py

Output:
    research/ingecart/assets/
    research/ingecart/assets/gallery.html
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

OUTPUT_DIR = Path(__file__).resolve().parent / "assets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ASSET_CATALOG = [
    {
        "label": "Ingecart brand emblem",
        "type": "logo",
        "source_page": "https://www.ingecart.eu/",
        "url": "https://static.wixstatic.com/media/aa5b12_0fe424559fce4c628f0ef67b3602dff4~mv2.png/v1/fill/w_928,h_930,fp_0.50_0.00,q_90,enc_avif,quality_auto/aa5b12_0fe424559fce4c628f0ef67b3602dff4~mv2.png",
    },
    {
        "label": "Ingecart header artwork",
        "type": "brand_image",
        "source_page": "https://www.ingecart.eu/",
        "url": "https://static.wixstatic.com/media/aa5b12_fe618ec3d7734688820073636552bfe9~mv2.png/v1/fill/w_1015,h_255,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Copia%20de%20ingeeniering.png",
    },
    {
        "label": "Partner marks strip",
        "type": "partners",
        "source_page": "https://www.ingecart.eu/",
        "url": "https://static.wixstatic.com/media/aa5b12_83aeccab15df434ca81ff7286b3f6864~mv2.jpg/v1/crop/x_1694,y_23,w_392,h_157/fill/w_30,h_12,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/MARCAS.jpg",
    },
    {
        "label": "Bobinas installation image",
        "type": "operations",
        "source_page": "https://www.ingecart.eu/",
        "url": "https://static.wixstatic.com/media/aa5b12_2de7495b91294521a3c35de92ec12fef~mv2.jpg/v1/fill/w_147,h_92,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/Bobinas.jpg",
    },
    {
        "label": "Robot FFG palletizer",
        "type": "robotics",
        "source_page": "https://www.ingecart.eu/",
        "url": "https://static.wixstatic.com/media/aa5b12_71c0b32757be45c0a68313485a342813~mv2.jpg/v1/fill/w_147,h_139,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/Robot%20FFG-2.jpg",
    },
    {
        "label": "Ingetrans reel loading",
        "type": "solution_ingetrans",
        "source_page": "https://www.ingecart.eu/ingetrans280",
        "url": "https://static.wixstatic.com/media/aa5b12_10de93d57241406ea1bebe774f363b21~mv2.jpg/v1/fill/w_147,h_102,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/Bobinas-2_edited.jpg",
    },
    {
        "label": "Ingetrans transfer graphic",
        "type": "solution_ingetrans",
        "source_page": "https://www.ingecart.eu/ingetrans280",
        "url": "https://static.wixstatic.com/media/aa5b12_214e312715f847f4847a962be13e1f21~mv2.png/v1/fill/w_49,h_30,al_c,q_85,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/Transfer%209_edited.png",
    },
    {
        "label": "SR1400 retal hero",
        "type": "solution_sr1400",
        "source_page": "https://www.ingecart.eu/sistemaretal1400",
        "url": "https://static.wixstatic.com/media/aa5b12_9ba199809a9749afb5f418edaa8268b0~mv2.jpg/v1/fill/w_147,h_70,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/Retal.jpg",
    },
    {
        "label": "SR1400 schematic",
        "type": "solution_sr1400",
        "source_page": "https://www.ingecart.eu/sistemaretal1400",
        "url": "https://static.wixstatic.com/media/aa5b12_71b48940ed4a4cd383fc7c9051bafc90~mv2.png/v1/fill/w_114,h_223,al_c,q_85,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/Retal-2_edited.png",
    },
    {
        "label": "Technical audit image",
        "type": "consulting",
        "source_page": "https://www.ingecart.eu/auditoriatecnica",
        "url": "https://static.wixstatic.com/media/aa5b12_32214f88679c47a9960ed99fa7412bf2~mv2.jpg/v1/fill/w_147,h_98,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/aa5b12_32214f88679c47a9960ed99fa7412bf2~mv2.jpg",
    },
    {
        "label": "TRIWALL project image",
        "type": "projects",
        "source_page": "https://www.ingecart.eu/proyectosrecientes",
        "url": "https://static.wixstatic.com/media/aa5b12_6b4c8d8442dd42b9ac79f8eef8bab9b2~mv2.png/v1/fill/w_49,h_30,al_c,q_85,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/TRIWALL_edited.png",
    },
    {
        "label": "USA Jumbo project",
        "type": "projects",
        "source_page": "https://www.ingecart.eu/proyectosrecientes",
        "url": "https://static.wixstatic.com/media/aa5b12_093ba955af424435b5d0dabc4787474b~mv2.jpg/v1/fill/w_147,h_104,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/USA%20JUMBO.jpg",
    },
    {
        "label": "Europe corrugator project",
        "type": "projects",
        "source_page": "https://www.ingecart.eu/proyectosrecientes",
        "url": "https://static.wixstatic.com/media/aa5b12_7b728dc16eb2496e8923e8d369da582c~mv2.jpg/v1/fill/w_147,h_104,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/EUROPA%20ONDULADORA.jpg",
    },
    {
        "label": "Palletizer project",
        "type": "projects",
        "source_page": "https://www.ingecart.eu/proyectosrecientes",
        "url": "https://static.wixstatic.com/media/aa5b12_bba7905111314673888bf5b2c49c8557~mv2.jpg/v1/fill/w_141,h_86,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/PALETIZADOR.jpg",
    },
    {
        "label": "EMBA relocation",
        "type": "projects",
        "source_page": "https://www.ingecart.eu/proyectosrecientes",
        "url": "https://static.wixstatic.com/media/aa5b12_a7ea7f32b6384d348f3724033d65d41d~mv2.jpg/v1/fill/w_147,h_104,al_c,q_80,usm_0.66_1.00_0.01,blur_2,enc_avif,quality_auto/EMBA.jpg",
    },
    {
        "label": "News hero MTorres alliance",
        "type": "news",
        "source_page": "https://www.ingecart.eu/noticias-1",
        "url": "https://static.wixstatic.com/media/aa5b12_64a6ac0aec5e41368c404792a6d48737~mv2.jpg/v1/fill/w_932,h_528,fp_0.50_0.50,q_90,enc_avif,quality_auto/aa5b12_64a6ac0aec5e41368c404792a6d48737~mv2.jpg",
    },
    {
        "label": "SuperCorr 2024 image",
        "type": "news",
        "source_page": "https://www.ingecart.eu/noticias-1",
        "url": "https://static.wixstatic.com/media/aa5b12_74e88aeebac54f4e868768154ab771a4~mv2.png/v1/fill/w_932,h_528,fp_0.50_0.50,q_95,enc_avif,quality_auto/aa5b12_74e88aeebac54f4e868768154ab771a4~mv2.png",
    },
    {
        "label": "McKinley SR1400 post image",
        "type": "news",
        "source_page": "https://www.ingecart.eu/noticias-1",
        "url": "https://static.wixstatic.com/media/aa5b12_8001a7b1cbf445d7ae3fa55b8efd3c64~mv2.webp/v1/fill/w_420,h_238,al_c,lg_1,q_90,enc_avif,quality_auto/aa5b12_8001a7b1cbf445d7ae3fa55b8efd3c64~mv2.webp",
    },
]


def _safe_name(url: str) -> str:
    parsed = urlparse(url)
    tail = Path(parsed.path).name or "asset"
    if "." not in tail:
        tail = f"{tail}.bin"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{digest}_{tail}"


def download_asset(url: str, dest: Path) -> tuple[bool, str]:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as response:
            data = response.read()
        dest.write_bytes(data)
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def build_gallery(records: list[dict], gallery_path: Path) -> None:
    rows = []
    for item in records:
        local = item.get("local_file", "")
        img = html.escape(local)
        label = html.escape(item.get("label", ""))
        typ = html.escape(item.get("type", ""))
        src = html.escape(item.get("source_page", ""))
        url = html.escape(item.get("url", ""))
        status = html.escape(item.get("download_status", ""))
        rows.append(
            f"""
            <div class='card'>
              <div class='meta'><b>{label}</b></div>
              <div class='meta'>type: {typ}</div>
              <div class='meta'>status: {status}</div>
              <a href='{url}' target='_blank'>source asset url</a><br>
              <a href='{src}' target='_blank'>source page</a>
              <div class='img-wrap'>
                <img src='{img}' alt='{label}' loading='lazy'>
              </div>
              <div class='meta file'>{img}</div>
            </div>
            """
        )

    html_doc = f"""
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Ingecart Asset Gallery</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 20px; background: #f7f7f8; }}
    h1 {{ margin: 0 0 6px; }}
    p {{ margin: 0 0 16px; color: #444; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }}
    .card {{ background: white; border: 1px solid #ddd; border-radius: 10px; padding: 10px; }}
    .meta {{ font-size: 12px; color: #333; margin-bottom: 4px; word-break: break-word; }}
    .file {{ color: #666; }}
    .img-wrap {{ margin-top: 8px; border: 1px dashed #bbb; border-radius: 8px; padding: 8px; background: #fafafa; }}
    img {{ max-width: 100%; height: auto; display: block; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Ingecart Asset Gallery</h1>
  <p>Generated from code catalog. Open this file directly in a browser.</p>
  <div class='grid'>
    {''.join(rows)}
  </div>
</body>
</html>
"""
    gallery_path.write_text(html_doc, encoding="utf-8")


def main() -> None:
    records = []
    for item in ASSET_CATALOG:
        file_name = _safe_name(item["url"])
        local_path = OUTPUT_DIR / file_name
        ok, msg = download_asset(item["url"], local_path)

        rec = dict(item)
        rec["local_file"] = local_path.name
        rec["download_status"] = "downloaded" if ok else f"failed: {msg}"
        records.append(rec)

    (OUTPUT_DIR / "assets_manifest.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    build_gallery(records, OUTPUT_DIR / "gallery.html")

    print("Asset pack complete")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Manifest: {OUTPUT_DIR / 'assets_manifest.json'}")
    print(f"Gallery: {OUTPUT_DIR / 'gallery.html'}")


if __name__ == "__main__":
    main()
