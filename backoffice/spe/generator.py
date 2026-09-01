"""Service Proposal Engine — resilient HTML generator with Ingecart fallback template."""
from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from backoffice.his.studio import HtmlIntelligenceStudio

from .models import Proposal


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = REPO_ROOT / "templates" / "spe"
INTERNAL_PAIGE_MODEL = TEMPLATE_DIR / "PAIGE_INGECART_MODEL_B_MASTER_REPORT_2026-08-18.html"
EXTERNAL_PAIGE_MODEL = Path(r"C:\Users\isena\Documents\GitHub\AI-FACTORY-v2\PAIGE_INGECART_MODEL_B_MASTER_REPORT_2026-08-18.html")
LEGACY_CORPORATE_TEMPLATE = Path(r"C:\Users\Inaki Senar\Documents\GitHub\ingesite.github.io\Modelo_HTML.txt")
LOGO_CANDIDATES = [
    REPO_ROOT / "assets" / "branding" / "ingecart_logo.png",
    REPO_ROOT / "scrapes" / "ingecart_proyectos" / "assets" / "Copia-de-ingeeniering.png",
]


class ProposalHTMLGenerator:
    """Generate SPE HTML with HIS when available and a stable local fallback."""

    def __init__(self) -> None:
        self.corporate_model_path = self._resolve_corporate_model_path()
        self.his = HtmlIntelligenceStudio(corporate_model_path=self.corporate_model_path)

    def generate(self, proposal: Proposal, preview: bool = False) -> str:
        payload = self._proposal_to_markdown(proposal)
        output_root = REPO_ROOT / "reports" / "spe" / "runs"
        source_dir = REPO_ROOT / "reports" / "spe" / "sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        slug = (proposal.number or proposal.id or "proposal").replace("/", "-").replace(" ", "_")
        source_file = source_dir / f"{slug}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.md"
        source_file.write_text(payload, encoding="utf-8")

        html = ""
        result: dict[str, Any] = {}
        model_path = Path()
        html_path = Path()
        generation_mode = "local_fallback"

        try:
            result = self.his.create_document(
                document_name=proposal.title or "Service Proposal",
                project=proposal.project or "Service_Proposal_Engine",
                client=proposal.customer or "INGECART Client",
                category="spe",
                language=proposal.language or "en",
                source_format="Markdown",
                sources=[str(source_file)],
                output_root=str(output_root),
                comments="Service Proposal Engine generation via HIS V3",
                objective="Generate corporate service proposal in Ingecart format",
                audience="Commercial and Executive",
                instruction_text="Use PAIGE Ingecart master model style and remove KPI summary block.",
                theme_profile="ingecart_industrial",
            )
            html_path = Path(str(result.get("html_path", "")))
            if html_path.exists():
                self.his.guarantee_standalone_html(html_path)
                html = html_path.read_text(encoding="utf-8", errors="ignore")
                html = self._ensure_ingecart_branding(html)
                html_path.write_text(html, encoding="utf-8")
                generation_mode = "his_v3"
            model_path = Path(str(result.get("document_model_path", "")))
        except Exception:
            html = self._render_local_html(proposal)

        if not html:
            html = self._render_local_html(proposal)
            generation_mode = "local_fallback"
        else:
            html = self._ensure_ingecart_branding(html)

        proposal.report_id = str(result.get("run_id", ""))
        if result.get("docx_path"):
            proposal.docx_path = str(result.get("docx_path", ""))
        if result.get("pdf_path"):
            proposal.pdf_path = str(result.get("pdf_path", ""))

        metadata = {
            "generator": generation_mode,
            "preview": preview,
            "run_id": result.get("run_id", ""),
            "output_dir": result.get("output_dir", ""),
            "document_model_path": str(model_path) if model_path else "",
            "html_path": str(html_path) if html_path else "",
            "quality_report_path": str(result.get("quality_report_path", "")),
            "generated_at": datetime.now(UTC).isoformat(),
        }

        fallback_meta_dir = REPO_ROOT / "reports" / "spe" / "metadata"
        fallback_meta_dir.mkdir(parents=True, exist_ok=True)
        if model_path and model_path.parent.exists():
            meta_file = model_path.parent / "spe_generation_metadata.json"
        else:
            meta_file = fallback_meta_dir / f"{slug}_spe_generation_metadata.json"
        meta_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

        if not preview:
            proposal.html_output = html
        return html

    def get_model_path(self, proposal: Proposal) -> str:
        if not proposal.report_id:
            return ""
        search_root = REPO_ROOT / "reports" / "spe" / "runs"
        candidates = sorted(search_root.glob(f"**/{proposal.report_id}/metadata/document_model.json"), reverse=True)
        if candidates:
            return str(candidates[0])

        for meta in sorted(search_root.glob("**/metadata/spe_generation_metadata.json"), reverse=True):
            try:
                payload = json.loads(meta.read_text(encoding="utf-8"))
            except Exception:
                continue
            if payload.get("run_id") == proposal.report_id:
                model_path = payload.get("document_model_path", "")
                if model_path and Path(model_path).exists():
                    return model_path
        return ""

    def _resolve_corporate_model_path(self) -> Path:
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        if INTERNAL_PAIGE_MODEL.exists():
            return INTERNAL_PAIGE_MODEL
        if EXTERNAL_PAIGE_MODEL.exists():
            INTERNAL_PAIGE_MODEL.write_text(EXTERNAL_PAIGE_MODEL.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            return INTERNAL_PAIGE_MODEL
        return LEGACY_CORPORATE_TEMPLATE

    def _render_local_html(self, proposal: Proposal) -> str:
        language = "es" if (proposal.language or "es").lower().startswith("es") else "en"
        toc = []
        body = []
        sections = [
            ("executive-summary", "Resumen ejecutivo", proposal.executive_summary),
            ("scope-services", "Programa anual de mantenimiento", proposal.maintenance_programme),
            ("ingpro", "Servicio INGEPRO de monitorización industrial", proposal.ingpro_section),
            ("deliverables", "Entregables operativos y de negocio", proposal.deliverables),
            ("conditions", "Condiciones comerciales", proposal.commercial_conditions),
            ("pricing", "Resumen económico", proposal.pricing_summary),
            ("acceptance", "Aceptación", proposal.acceptance),
        ]
        for anchor, title, content in sections:
            normalized = self._normalize_section_content(content)
            if not normalized:
                continue
            toc.append(f'<a href="#{anchor}">{title}</a>')
            body.append(
                f"""
      <section id="{anchor}">
        <div class="section-no">{title.upper()}</div>
        <h2>{title}</h2>
        {normalized}
      </section>
""".rstrip()
            )

        services_rows = []
        for service in proposal.services:
            if not service.enabled:
                continue
            services_rows.append(
                "<tr>"
                f"<td>{self._escape(service.name)}</td>"
                f"<td>{self._escape(service.frequency or service.unit or '-') }</td>"
                f"<td>{self._escape(service.coverage or '-')}</td>"
                f"<td class='number'>{service.total_price:,.0f} {proposal.currency}</td>"
                "</tr>"
            )
        if not services_rows:
            services_rows.append("<tr><td colspan='4'>No hay servicios configurados.</td></tr>")
        toc_html = "\n".join(toc) if toc else '<a href="#services">Servicios</a>'
        logo_data_uri = self._logo_data_uri()

        return f"""<!DOCTYPE html>
<html lang="{language}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Oferta de servicio Ingecart" />
  <title>{self._escape(proposal.title or "Oferta de Servicio Ingecart")}</title>
  <style>
    :root {{
      --ink:#171717; --paper:#f4efe8; --surface:#fff; --line:#d9d1c6; --muted:#5f5d5a;
      --orange:#ff5a10; --orange-dark:#a84700; --black:#0d0d0d;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font-family:"Aptos","Segoe UI",sans-serif; line-height:1.6; }}
    .hero {{ min-height:48vh; display:flex; align-items:flex-end; background:linear-gradient(100deg,#000,#222); color:#fff; border-bottom:7px solid var(--orange); }}
    .hero-inner,.layout {{ width:min(1240px,calc(100% - 48px)); margin:0 auto; }}
    .hero-inner {{ padding:70px 0 50px; }}
    .brand-mark {{ display:inline-flex; align-items:center; gap:10px; font:800 13px "Cascadia Mono",Consolas,monospace; letter-spacing:.1em; }}
    .brand-mark img {{ width:58px; height:58px; object-fit:contain; background:#fff; border:2px solid #fff; }}
    h1 {{ margin:16px 0 10px; font:800 clamp(34px,5.6vw,60px)/1 Georgia,serif; }}
    .layout {{ display:grid; grid-template-columns:250px minmax(0,1fr); gap:42px; }}
    aside {{ padding:34px 0; }}
    .toc {{ position:sticky; top:20px; border-top:5px solid var(--orange); padding-top:12px; }}
    .toc a {{ display:block; padding:7px 0; border-bottom:1px solid var(--line); color:var(--muted); text-decoration:none; font-size:13px; }}
    main {{ padding:40px 0 70px; }}
    section {{ margin-bottom:64px; }}
    .section-no {{ color:var(--orange-dark); font:800 12px "Cascadia Mono",Consolas,monospace; }}
    h2 {{ margin:7px 0 18px; font:800 clamp(26px,4vw,40px)/1.06 Georgia,serif; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); background:var(--surface); }}
    table {{ width:100%; min-width:680px; border-collapse:collapse; }}
    th,td {{ padding:13px 14px; border-bottom:1px solid var(--line); vertical-align:top; }}
    th {{ background:var(--black); color:#fff; font:800 11px "Cascadia Mono",Consolas,monospace; text-transform:uppercase; }}
    .number {{ white-space:nowrap; font-family:"Cascadia Mono",Consolas,monospace; font-weight:800; text-align:right; }}
    footer {{ background:var(--black); color:#fff; padding:18px 0 30px; }}
    @media (max-width:980px) {{ .layout {{ grid-template-columns:1fr; }} aside {{ display:none; }} }}
    @media print {{ body {{ background:#fff; }} aside {{ display:none; }} main {{ padding:10mm; }} }}
  </style>
</head>
<body>
  <header class="hero">
    <div class="hero-inner">
      <div class="brand-mark"><img src="{logo_data_uri}" alt="Ingecart"><span>INGECART</span></div>
      <h1>{self._escape(proposal.title or "Oferta Anual de Mantenimiento Ingecart")}</h1>
      <p>{self._escape(proposal.customer or "Cliente")} · {self._escape(proposal.plant or "Planta")} · {self._escape(proposal.number or "OFF-XXXX")}</p>
    </div>
  </header>
  <div class="layout">
    <aside><div class="toc"><strong>CONTENIDO</strong>{toc_html}</div></aside>
    <main>
      <section id="services">
        <div class="section-no">SERVICIOS</div>
        <h2>Oferta anual recomendada</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Servicio</th><th>Frecuencia</th><th>Cobertura</th><th>Importe anual</th></tr></thead>
            <tbody>{"".join(services_rows)}</tbody>
          </table>
        </div>
      </section>
      {"".join(body)}
    </main>
  </div>
  <footer><div class="hero-inner">INGECART · Oferta de servicio anual · {self._escape(proposal.number or "")}</div></footer>
</body>
</html>"""

    def _logo_data_uri(self) -> str:
        for candidate in LOGO_CANDIDATES:
            if not candidate.exists():
                continue
            mime = "image/png" if candidate.suffix.lower() == ".png" else "image/jpeg"
            encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{encoded}"
        return ""

    def _ensure_ingecart_branding(self, html: str) -> str:
        logo_data_uri = self._logo_data_uri()
        if not logo_data_uri:
            return html
        lower = html.lower()
        if "<img" in lower and ("ingecart" in lower or "data:image/" in lower):
            return html
        soup = BeautifulSoup(html, "html.parser")
        brand = soup.find(class_="brand-mark")
        if brand is None:
            hero = soup.find(class_="hero")
            brand = soup.new_tag("div", attrs={"class": "brand-mark"})
            if hero is not None:
                hero.insert(0, brand)
            elif soup.body is not None:
                soup.body.insert(0, brand)
            else:
                return html
        if not brand.find("img"):
            img = soup.new_tag("img", src=logo_data_uri, alt="Ingecart")
            brand.insert(0, img)
        if "ingecart" not in brand.get_text(" ", strip=True).lower():
            label = soup.new_tag("span")
            label.string = "INGECART"
            brand.append(label)
        return str(soup)

    def _normalize_section_content(self, content: str) -> str:
        value = (content or "").strip()
        if not value:
            return ""
        if "<" in value and ">" in value:
            return value
        paragraphs = [line.strip() for line in value.splitlines() if line.strip()]
        return "".join(f"<p>{self._escape(line)}</p>" for line in paragraphs)

    def _proposal_to_markdown(self, proposal: Proposal) -> str:
        lines: list[str] = []
        lines.append(f"# {proposal.title or 'Service Proposal'}")
        lines.append("")
        lines.append("## Proposal Metadata")
        lines.append(f"- Number: {proposal.number or 'pending'}")
        lines.append(f"- Customer: {proposal.customer or '-'}")
        lines.append(f"- Plant: {proposal.plant or '-'}")
        lines.append(f"- Country: {proposal.customer_country or '-'}")
        lines.append(f"- Language: {proposal.language or 'en'}")
        lines.append(f"- Currency: {proposal.currency or 'EUR'}")
        lines.append(f"- Duration: {proposal.duration or '-'}")
        lines.append(f"- Validity Days: {proposal.validity_days}")
        lines.append(f"- Payment Terms: {proposal.payment_terms or '-'}")
        lines.append("")

        lines.append("## Executive Summary")
        lines.append(proposal.executive_summary or "Corporate service proposal generated under AHDE governance.")
        lines.append("")
        lines.append("## Services")
        for service in proposal.services:
            if not service.enabled:
                continue
            lines.append(f"### {service.name}")
            lines.append(service.description or "")
            lines.append(f"- Frequency: {service.frequency or service.unit}")
            lines.append(f"- Total: {service.total_price:.2f} {proposal.currency}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _escape(value: str) -> str:
        return (
            (value or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
