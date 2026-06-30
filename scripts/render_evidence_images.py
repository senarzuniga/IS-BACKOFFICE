#!/usr/bin/env python3
"""Render textual evidence (JSON, CSV, folder tree) into PNG images for the RC1 report."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def render_text_to_image(text: str, outpath: Path, w=1200, h=800, bg=(20,20,20), fg=(240,240,240)):
    img = Image.new('RGB', (w, h), color=bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 16)
    except Exception:
        font = ImageFont.load_default()

    margin = 12
    y = margin
    for line in text.splitlines():
        draw.text((margin, y), line[:200], font=font, fill=fg)
        y += 18
        if y > h - margin:
            break

    img.save(outpath)
    print('Wrote', outpath)


def render_summary(json_path: Path, out_img: Path):
    with open(json_path, 'r', encoding='utf-8') as f:
        js = json.load(f)
    lines = [f'Run ID: {js.get("run_id")}', f'Scenario: {js.get("scenario")}', f'Start: {js.get("start_ts")}', f'End: {js.get("end_ts")}', f'Duration (s): {js.get("run_duration_s")}', f'Completed orders: {js.get("completed_orders")}', f'Throughput (rolls/h): {js.get("throughput_rolls_per_hour")}']
    render_text_to_image('\n'.join(lines), out_img)


def render_event_log(csv_path: Path, out_img: Path, max_lines=30):
    lines = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            lines.append(', '.join(row))
            if i >= max_lines:
                break
    render_text_to_image('\n'.join(lines), out_img)


def render_tree(out_txt: Path, out_img: Path):
    try:
        import os
        lines = []
        for root, dirs, files in os.walk('.'):
            level = root.count(os.sep)
            indent = ' ' * 2 * level
            lines.append(f"{indent}{Path(root).name}/")
            for f in files[:10]:
                lines.append(f"{indent}  {f}")
        text = '\n'.join(lines[:200])
        out_txt.write_text(text, encoding='utf-8')
        render_text_to_image(text, out_img)
    except Exception as e:
        print('Error rendering tree', e)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    evidence = repo / 'releases' / 'rc1_evidence'
    evidence.mkdir(parents=True, exist_ok=True)

    summary = evidence / 'run_summary.json'
    if summary.exists():
        render_summary(summary, evidence / 'run_summary.png')

    elog = evidence / 'event_log.csv'
    if elog.exists():
        render_event_log(elog, evidence / 'event_log.png')

    tree_txt = evidence / 'folder_tree.txt'
    tree_img = evidence / 'folder_tree.png'
    render_tree(tree_txt, tree_img)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
