from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backoffice.scraping.high_quality_scraper import HighQualityImageScraper


def run() -> None:
    out_dir = Path(__file__).resolve().parent / "deep_scraped_images"
    out_dir.mkdir(parents=True, exist_ok=True)

    scraper = HighQualityImageScraper(output_dir=str(out_dir))

    targets = [
        {"name": "ingecart", "url": "https://www.ingecart.eu/", "recursive": True, "max_pages": 12, "max_images": 120},
        {"name": "fespa", "url": "https://europe.fespa.com/es/exhibit", "recursive": True, "max_pages": 10, "max_images": 80},
    ]

    all_results = {
        "generated_at": datetime.now().isoformat(),
        "targets": {},
    }

    for t in targets:
        print(f"[scrape] {t['name']} -> {t['url']}")
        scan = scraper.scrape_website(
            url=t["url"],
            min_width=700,
            recursive=t["recursive"],
            max_pages=t["max_pages"],
        )

        downloaded = scraper.download_images(scan.get("images", []), max_images=t["max_images"])
        scan["downloaded_images"] = downloaded

        all_results["targets"][t["name"]] = {
            "url": t["url"],
            "pages_scraped": scan.get("pages_scraped", []),
            "images_found": len(scan.get("images", [])),
            "images_downloaded": len(downloaded),
            "stats": scan.get("stats", {}),
            "downloaded_images": downloaded,
        }

        print(f"[ok] {t['name']}: found={len(scan.get('images', []))} downloaded={len(downloaded)}")

    ts = datetime.now().strftime("%Y-%m-%d")
    metadata_file = Path(__file__).resolve().parent / f"ingecart_fespa_deep_image_metadata_{ts}.json"
    metadata_file.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] metadata: {metadata_file}")


if __name__ == "__main__":
    run()
