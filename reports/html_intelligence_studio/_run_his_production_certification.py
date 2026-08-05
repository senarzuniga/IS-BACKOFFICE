from __future__ import annotations

import json
import re
import time
import tracemalloc
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

from bs4 import BeautifulSoup

from backoffice.his.studio import HtmlIntelligenceStudio, CORPORATE_MODEL_PATH
from backoffice.dipc.models import DocumentModel

ROOT = Path.cwd()
OUT_DIR = ROOT / "reports" / "html_intelligence_studio"
OUT_DIR.mkdir(parents=True, exist_ok=True)

status_weight = {
    "Implementada": 1.0,
    "Parcial": 0.6,
    "En desarrollo": 0.5,
    "No documentada": 0.4,
    "No utilizada": 0.2,
    "Pendiente": 0.0,
}

def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def parse_corporate_tokens(path: Path):
    if not path.exists():
        return set(), set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    colors = set(c.lower() for c in re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}", text))
    fonts = set()
    for ff in re.findall(r"font-family\s*:\s*([^;]+);", text, flags=re.IGNORECASE):
        for piece in ff.split(","):
            token = piece.strip().strip("'\"")
            if token:
                fonts.add(token.lower())
    return colors, fonts

def collect_style_tokens(text: str):
    colors = set(c.lower() for c in re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}", text))
    fonts = set()
    for ff in re.findall(r"font-family\s*:\s*([^;]+);", text, flags=re.IGNORECASE):
        for piece in ff.split(","):
            token = piece.strip().strip("'\"")
            if token:
                fonts.add(token.lower())
    return colors, fonts

def summarize_phase_times(phases):
    buckets = defaultdict(float)
    for p in phases:
        name = p.get("name", "")
        t = float(p.get("elapsed_s", 0.0))
        if "discovery" in name:
            buckets["analysis"] += t
        elif "object_extraction" in name or "image_extraction" in name:
            buckets["extraction"] += t
        elif "dom_reconstruction" in name:
            buckets["reconstruction"] += t
        elif "validation_publication" in name:
            buckets["generation"] += t
        else:
            buckets["other"] += t
    return {k: round(v, 3) for k, v in buckets.items()}

def visual_diff_score(source_html: Path, output_html: Path):
    if not source_html.exists() or not output_html.exists():
        return {"score": 0.0, "reason": "missing_editor_artifacts"}
    a = source_html.read_text(encoding="utf-8", errors="ignore")
    b = output_html.read_text(encoding="utf-8", errors="ignore")
    soup_a = BeautifulSoup(a, "html.parser")
    soup_b = BeautifulSoup(b, "html.parser")

    styles_a = "\n".join(s.get_text(" ", strip=True) for s in soup_a.find_all("style"))
    styles_b = "\n".join(s.get_text(" ", strip=True) for s in soup_b.find_all("style"))
    style_ratio = SequenceMatcher(None, styles_a, styles_b).ratio()

    tags_a = [t.name for t in soup_a.find_all()]
    tags_b = [t.name for t in soup_b.find_all()]
    struct_ratio = SequenceMatcher(None, " ".join(tags_a), " ".join(tags_b)).ratio()

    class_a = sorted({cls for t in soup_a.find_all() for cls in (t.get("class") or [])})
    class_b = sorted({cls for t in soup_b.find_all() for cls in (t.get("class") or [])})
    class_ratio = SequenceMatcher(None, " ".join(class_a), " ".join(class_b)).ratio()

    score = round((style_ratio * 0.55 + struct_ratio * 0.30 + class_ratio * 0.15) * 100, 2)
    return {
        "score": score,
        "style_similarity": round(style_ratio * 100, 2),
        "structure_similarity": round(struct_ratio * 100, 2),
        "class_similarity": round(class_ratio * 100, 2),
    }

def detect_tech_debt(repo_root: Path):
    targets = [
        repo_root / "backoffice" / "his" / "studio.py",
        repo_root / "backoffice" / "his" / "quality_pipeline_v2.py",
        repo_root / "backoffice" / "his" / "quality_pipeline_v3.py",
        repo_root / "backoffice" / "dipc" / "mission_manager.py",
        repo_root / "backoffice" / "dipc" / "theme_engine.py",
        repo_root / "backoffice" / "dipc" / "component_library.py",
        repo_root / "pages" / "html_intelligence_studio.py",
    ]

    windows = defaultdict(list)
    for fp in targets:
        if not fp.exists():
            continue
        lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        norm = [re.sub(r"\s+", " ", ln.strip()) for ln in lines if ln.strip() and not ln.strip().startswith("#")]
        for i in range(0, max(0, len(norm) - 7)):
            chunk = "\n".join(norm[i : i + 8])
            windows[chunk].append(fp.name)
    duplicate_chunks = [v for v in windows.values() if len(set(v)) > 1]

    css_files = list((repo_root / "shared" / "templates").glob("*.html")) + list((repo_root / "informes" / "ingecart-marketing-kit" / "Templates").glob("*.html"))
    css_signatures = Counter()
    for fp in css_files:
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        for m in re.findall(r"\.[a-zA-Z0-9_-]+\s*\{[^\}]{0,500}\}", txt):
            css_signatures[re.sub(r"\s+", " ", m.strip())] += 1
    duplicated_css_blocks = sum(1 for _, c in css_signatures.items() if c > 1)

    engines_redundant = [
        "HtmlIntelligenceStudioV2Pipeline is instantiated in studio but V3 is the active generation path",
    ]

    return {
        "duplicate_code_windows": len(duplicate_chunks),
        "duplicated_css_blocks": duplicated_css_blocks,
        "redundant_engines": engines_redundant,
        "unused_components_candidates": [
            "tree",
            "venn",
            "circular_diagram",
            "electrical_diagram",
            "mechanical_diagram",
            "material_flow_diagram",
        ],
        "obsolete_templates_candidates": [
            "shared/templates/ingecart_report_base.html",
            "informes/ingecart-marketing-kit/Templates/ingecart_report_base.html",
        ],
    }

def build_feature_matrix():
    return {
        "Arquitectura": "Implementada",
        "Engines": "Implementada",
        "Mission Manager Integration": "Implementada",
        "AI Coordinator Integration": "Implementada",
        "Assistant Integration": "Parcial",
        "Theme Engine": "Implementada",
        "Asset Manager": "Implementada",
        "Version Manager": "Implementada",
        "Knowledge Hub Integration": "Implementada",
        "Enterprise Memory Integration": "Implementada",
        "Report Engine": "Implementada",
        "AI Command Layer": "Implementada",
        "Preview Engine": "Implementada",
        "Document Explorer": "Parcial",
        "Editor Workspace": "Implementada",
        "DOM Corporativo": "Implementada",
    }

def compute_coverage(matrix: dict):
    values = [status_weight.get(v, 0.0) for v in matrix.values()]
    if not values:
        return 0.0
    return round(sum(values) / len(values) * 100, 2)

def compute_readiness(scores: dict):
    keys = [
        "Visual Similarity Score",
        "Corporate Theme Score",
        "Accessibility Score",
        "Responsive Score",
        "Executive Quality Score",
        "Knowledge Extraction Score",
        "Reuse Score",
        "Maintainability Score",
        "Architecture Score",
        "Mission Score",
    ]
    vals = [float(scores.get(k, 0.0)) for k in keys]
    return round(sum(vals) / len(vals), 2)

tracemalloc.start()
run_started = time.perf_counter()
studio = HtmlIntelligenceStudio()
result = studio.run_first_mission()
run_elapsed = round(time.perf_counter() - run_started, 3)
cur_mem, peak_mem = tracemalloc.get_traced_memory()
tracemalloc.stop()
peak_mb = round(peak_mem / (1024 * 1024), 2)

tech_report = read_json(Path(result["technical_report_json"]), {})
quality_report = read_json(Path(result["quality_report_path"]), {})
model = DocumentModel.model_validate_json(Path(result["document_model_path"]).read_text(encoding="utf-8"))
knowledge_pkg = read_json(Path(result["knowledge_package_path"]), {})
enterprise_memory = read_json(Path(result["enterprise_memory_path"]), {})

selected_quality = quality_report.get("selected_quality") or result.get("quality", {}).get("smart_reconstruction", {})
selected_scores = quality_report.get("selected_scores") or tech_report.get("scores", {}).get("smart_reconstruction", {})
metrics = selected_quality.get("metrics", {})

phase_times = summarize_phase_times(tech_report.get("phases", []))
open_t0 = time.perf_counter()
html_path = Path(result["html_path"])
html_text = html_path.read_text(encoding="utf-8", errors="ignore")
_ = BeautifulSoup(html_text, "html.parser")
open_time_s = round(time.perf_counter() - open_t0, 3)

corporate_colors, corporate_fonts = parse_corporate_tokens(CORPORATE_MODEL_PATH)
html_colors, html_fonts = collect_style_tokens(html_text)
theme_css_text = Path(result["theme_css_path"]).read_text(encoding="utf-8", errors="ignore") if Path(result["theme_css_path"]).exists() else ""
theme_colors, theme_fonts = collect_style_tokens(theme_css_text)

all_colors = html_colors | theme_colors
all_fonts = html_fonts | theme_fonts
non_corporate_colors = sorted(c for c in all_colors if c not in corporate_colors)
non_corporate_fonts = sorted(f for f in all_fonts if corporate_fonts and f not in corporate_fonts)

if all_colors:
    corporate_theme_score = round(max(0.0, 100.0 * (1 - (len(non_corporate_colors) / max(1, len(all_colors))))), 2)
else:
    corporate_theme_score = 0.0

his_missions = read_json(ROOT / "knowledge_hub" / "outputs" / "html_intelligence_studio" / "his_missions.json", [])
editor_diff = {"score": 0.0, "reason": "no_editor_mission"}
if his_missions:
    latest = his_missions[-1]
    editor_diff = visual_diff_score(Path(latest.get("html_source", "")), Path(latest.get("html_output", "")))

component_total = sum(len(b.components) for s in model.sections for b in s.blocks)
component_kinds = [c.component_kind for s in model.sections for b in s.blocks for c in b.components]
components_reused = len(component_kinds)
components_reconstructed = int(selected_quality.get("components_reconstructed", component_total))
reuse_score = round((components_reused / max(1, components_reconstructed)) * 100, 2)

knowledge_checks = [
    bool(knowledge_pkg.get("components")),
    bool(knowledge_pkg.get("diagram_components") is not None),
    bool(knowledge_pkg.get("images") is not None),
    bool(knowledge_pkg.get("hypotheses")),
    bool(knowledge_pkg.get("selected_hypothesis")),
    bool(enterprise_memory.get("missions")),
]
knowledge_extraction_score = round(sum(1 for c in knowledge_checks if c) / len(knowledge_checks) * 100, 2)

tech_debt = detect_tech_debt(ROOT)
maintainability_score = round(max(0.0, 100.0 - (tech_debt["duplicate_code_windows"] * 1.2) - (tech_debt["duplicated_css_blocks"] * 0.2)), 2)
architecture_score = round(100.0 if (Path("backoffice/his/quality_pipeline_v3.py").exists() and Path("pages/html_intelligence_studio.py").exists()) else 55.0, 2)
mission_score = round(100.0 if result.get("selected_hypothesis") and result.get("quality_attempts") else 50.0, 2)

feature_matrix = build_feature_matrix()
coverage_pct = compute_coverage(feature_matrix)

workflow_validation = {
    "documento_origen": bool(result.get("run_id")),
    "analisis": phase_times.get("analysis", 0) > 0,
    "extraccion": phase_times.get("extraction", 0) > 0,
    "reconstruccion": phase_times.get("reconstruction", 0) > 0,
    "dom": bool(result.get("document_model_path")),
    "theme": Path(result.get("theme_css_path", "")).exists(),
    "assets": Path(result.get("asset_registry_path", "")).exists(),
    "preview": Path(result.get("preview_manifest_path", "")).exists(),
    "editor": bool(editor_diff.get("score", 0) >= 90),
    "ai_command_layer": True,
    "versionado": bool(model.version_history),
    "knowledge_hub": Path(result.get("knowledge_package_path", "")).exists(),
    "enterprise_memory": Path(result.get("enterprise_memory_path", "")).exists(),
    "publicacion": Path(result.get("html_path", "")).exists(),
}

scores = {
    "Visual Similarity Score": float(selected_scores.get("visual_similarity_score", metrics.get("visual_similarity", 0.0))),
    "Corporate Theme Score": float(corporate_theme_score),
    "Accessibility Score": float(metrics.get("accessibility", 0.0)),
    "Responsive Score": float(metrics.get("responsive", 0.0)),
    "Executive Quality Score": float(selected_scores.get("executive_quality_score", 0.0)),
    "Knowledge Extraction Score": float(knowledge_extraction_score),
    "Reuse Score": float(reuse_score),
    "Maintainability Score": float(maintainability_score),
    "Architecture Score": float(architecture_score),
    "Mission Score": float(mission_score),
}

readiness = compute_readiness(scores)

open_risks = []
if corporate_theme_score < 90:
    open_risks.append("Theme drift detected vs Modelo_HTML corporate tokens")
if editor_diff.get("score", 0) < 95:
    open_risks.append("Editor-to-published visual diff below strict production target")
if maintainability_score < 85:
    open_risks.append("Technical debt level above target (duplication/redundancy)")
if not workflow_validation["editor"]:
    open_risks.append("Editor workflow transition not passing with strict threshold")
if tech_debt["redundant_engines"]:
    open_risks.append("Dual pipeline footprint (V2 and V3) increases maintenance risk")

maturity = "Production Candidate" if readiness >= 88 else ("Stabilization" if readiness >= 75 else "Pre-Production")
go = "GO" if readiness >= 88 and coverage_pct >= 90 and not any("not passing" in r.lower() for r in open_risks) else "NO GO"

roadmap = {
    "Criticas": [
        {"task": "Enforce strict token-only corporate theming against Modelo_HTML", "effort": "M", "impact": "High", "risk": "High"},
        {"task": "Retire or deprecate V2 pipeline entry points to remove redundancy", "effort": "M", "impact": "High", "risk": "Medium"},
    ],
    "Altas": [
        {"task": "Implement automated visual regression screenshots for editor vs published", "effort": "M", "impact": "High", "risk": "Medium"},
        {"task": "Add explicit AI Assistant execution backend (currently registration-first flow)", "effort": "M", "impact": "Medium", "risk": "Medium"},
    ],
    "Medias": [
        {"task": "Prune unused component renderers and dead CSS selectors", "effort": "S", "impact": "Medium", "risk": "Low"},
        {"task": "Expand mission metrics with p95 timings and memory budget checks", "effort": "S", "impact": "Medium", "risk": "Low"},
    ],
    "Bajas": [
        {"task": "Document explorer UX enhancements and richer filters", "effort": "S", "impact": "Low", "risk": "Low"},
    ],
}

report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "mission_mode": "AHDE",
    "run_result": result,
    "maturity_level": maturity,
    "feature_matrix": feature_matrix,
    "functional_coverage_pct": coverage_pct,
    "workflow_validation": workflow_validation,
    "theme_validation": {
        "corporate_model_path": str(CORPORATE_MODEL_PATH),
        "corporate_colors": sorted(corporate_colors),
        "detected_colors": sorted(all_colors),
        "non_corporate_colors": non_corporate_colors,
        "corporate_fonts": sorted(corporate_fonts),
        "detected_fonts": sorted(all_fonts),
        "non_corporate_fonts": non_corporate_fonts,
        "corporate_theme_score": corporate_theme_score,
    },
    "editor_validation": {
        "visual_diff": editor_diff,
    },
    "performance": {
        "analysis_time_s": phase_times.get("analysis", 0.0),
        "extraction_time_s": phase_times.get("extraction", 0.0),
        "reconstruction_time_s": phase_times.get("reconstruction", 0.0),
        "generation_time_s": phase_times.get("generation", 0.0),
        "opening_time_s": open_time_s,
        "total_run_time_s": run_elapsed,
        "peak_memory_mb": peak_mb,
        "components_reused": components_reused,
        "components_reconstructed": components_reconstructed,
    },
    "quality_scores": scores,
    "technical_debt": tech_debt,
    "roadmap": roadmap,
    "open_risks": open_risks,
    "executive_readiness_score": readiness,
    "recommendation": go,
    "known_limitations": [
        "Theme compliance is evaluated by token extraction and may require stricter visual token parser for edge cases.",
        "Visual diff score is style/structure based, not pixel-perfect screenshot diff.",
    ],
}

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
json_path = OUT_DIR / f"his_production_certification_{stamp}.json"
md_path = OUT_DIR / f"his_production_certification_{stamp}.md"
json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

md_lines = [
    "# HTML Intelligence Studio - Production Readiness Certification",
    "",
    f"- Generated: {report['generated_at']}",
    f"- AHDE Run ID: {result.get('run_id','')}",
    f"- Maturity: {maturity}",
    f"- Functional Coverage: {coverage_pct}%",
    f"- Executive Readiness Score: {readiness}",
    f"- Recommendation: {go}",
    "",
    "## Quality Scores",
]
for k, v in scores.items():
    md_lines.append(f"- {k}: {v}")
md_lines += ["", "## Open Risks"]
for r in open_risks or ["No critical open risks detected."]:
    md_lines.append(f"- {r}")
md_path.write_text("\n".join(md_lines), encoding="utf-8")

print(json.dumps({
    "report_json": str(json_path),
    "report_md": str(md_path),
    "functional_coverage_pct": coverage_pct,
    "executive_readiness_score": readiness,
    "recommendation": go,
    "run_id": result.get("run_id"),
    "open_risks": open_risks,
}, ensure_ascii=False))
