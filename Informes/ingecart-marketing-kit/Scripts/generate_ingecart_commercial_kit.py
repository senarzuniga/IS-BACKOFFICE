from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from document_analysis.context_analyzer import ContextAnalyzer
from document_analysis.content_extractor import ContentExtractor
from document_analysis.document_parser import DocumentParser
from document_analysis.folder_reader import FolderReader
from document_analysis.models import FolderStats, OutputFormat
from document_analysis.output_generator import OutputGenerator


TARGET_FOLDER = Path(
    r"C:\Users\Inaki Senar\Documents\CTA ISENAR\MARKETING\POSIBLES CONTENIDOS\TEXTOS COMUNICACION CLIENTE"
)
SOURCE_FOLDER = TARGET_FOLDER / "TEXTOS COMUNICACION CLIENTE Y PROSPECCION"

REPO_ROOT = Path(__file__).resolve().parents[1]
INGECART_RESEARCH = REPO_ROOT / "research" / "ingecart"
INGECART_ASSETS = REPO_ROOT / "ingecart_assets_v2"
INGECART_FUSION = REPO_ROOT / "ingecart_assets_fusion"

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".json", ".xml", ".html", ".pptx", ".md"}


def _now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)


def _iter_supported_files(folder: Path) -> Iterable[Path]:
    if not folder.exists():
        return []
    return [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]


def _discover_sources(reader: FolderReader) -> list[dict[str, Any]]:
    discovered: list[dict[str, Any]] = []
    seen: set[str] = set()

    sources = [SOURCE_FOLDER, INGECART_RESEARCH, INGECART_ASSETS, INGECART_FUSION]
    for src_root in sources:
        if not src_root.exists():
            continue
        items = reader.discover_files(str(src_root))
        for item in items:
            path = str(Path(item["path"]).resolve())
            if path in seen:
                continue
            seen.add(path)
            discovered.append(item)

    return discovered


def _build_stats(folder_path: Path, files: list[dict[str, Any]]) -> FolderStats:
    ext_counter = Counter(item.get("doc_type", "unknown") for item in files)
    total_size = 0
    for item in files:
        try:
            total_size += Path(item["path"]).stat().st_size
        except Exception:
            pass

    return FolderStats(
        folder_path=str(folder_path),
        total_files=len(files),
        supported_files=len(files),
        unsupported_files=0,
        total_size_bytes=total_size,
        files_by_type=dict(ext_counter),
    )


def _extract_brief_facts() -> dict[str, Any]:
    facts: dict[str, Any] = {
        "company": "Ingecart",
        "tagline": "Engineering and auditing tailored automation and intralogistics",
        "stats": {},
        "corrugated_offer": [],
        "services_sheet_markers": [],
    }

    brand_json = INGECART_ASSETS / "ingecart_brand_complete.json"
    if brand_json.exists():
        data = json.loads(brand_json.read_text(encoding="utf-8"))
        facts["company"] = data.get("company_name") or facts["company"]
        facts["tagline"] = data.get("tagline") or facts["tagline"]
        facts["stats"] = (data.get("texts") or {}).get("stats") or {}

    psc_json = INGECART_ASSETS / "psc_source_summary.json"
    if psc_json.exists():
        data = json.loads(psc_json.read_text(encoding="utf-8"))
        sheets = ((data.get("main_xlsx") or {}).get("sheets") or {})

        corr_rows = sheets.get("CORRUGATED LINE SHEET", [])
        for row in corr_rows:
            for cell in row:
                cell_text = str(cell).strip()
                if not cell_text:
                    continue
                if any(k in cell_text.lower() for k in ["bhs", "corrugator", "offer", "model", "mpm"]):
                    facts["corrugated_offer"].append(cell_text)

        service_rows = sheets.get("SERVICES SHEET", [])
        for row in service_rows:
            row_text = " | ".join(str(c).strip() for c in row if str(c).strip())
            if row_text and any(k in row_text.lower() for k in ["purchase", "sale", "benefit", "cantidad"]):
                facts["services_sheet_markers"].append(row_text)

    facts["corrugated_offer"] = list(dict.fromkeys(facts["corrugated_offer"]))[:10]
    facts["services_sheet_markers"] = list(dict.fromkeys(facts["services_sheet_markers"]))[:10]
    return facts


def _top_entities(analysis) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    seen: set[tuple[str, str]] = set()
    for doc in analysis.documents:
        for ent in doc.entities:
            key = (ent.entity_type.value, ent.text.lower())
            if key in seen:
                continue
            seen.add(key)
            grouped.setdefault(ent.entity_type.value, []).append(ent.text)

    for k in grouped:
        grouped[k] = grouped[k][:20]
    return grouped


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _build_custom_docs(output_dir: Path, analysis, facts: dict[str, Any]) -> None:
    entities = _top_entities(analysis)
    themes = analysis.cross_themes[:12]

    company = facts.get("company", "Ingecart")
    tagline = facts.get("tagline", "")
    stats = facts.get("stats", {})
    corr_offer = facts.get("corrugated_offer", [])

    stats_line = ", ".join(f"{k}: {v}" for k, v in stats.items()) if stats else "No numeric brand stats were found."
    theme_line = ", ".join(themes) if themes else "automation, reliability, services, corrugated production"

    possible_news = f"""
# Posibles noticias para {company}

Base editorial utilizada:
- Carpeta de textos de comunicacion comercial del cliente.
- Repositorio de inteligencia y contenidos historicos de {company}.
- Temas recurrentes detectados: {theme_line}

## Noticias propuestas (multiplataforma)

1. {company} refuerza su propuesta de productividad para plantas de carton corrugado.
- Enfoque web: Caso de uso y resultado operativo.
- Enfoque LinkedIn: Liderazgo tecnico y mejora continua.
- Enfoque prensa sectorial: Tendencias de automatizacion y competitividad.

2. Nueva etapa de servicio integral: consultoria, ingenieria y soporte de planta.
- Enfoque web: Cobertura completa desde diagnostico hasta puesta en marcha.
- Enfoque LinkedIn: Equipos multidisciplinares y acompanamiento real.
- Enfoque prensa sectorial: Modelo de servicio orientado a KPI industrial.

3. Proyecto de optimizacion de cuellos de botella en lineas corrugadas.
- Enfoque web: Beneficios en throughput, scrap y tiempos muertos.
- Enfoque LinkedIn: Metodologia de analisis y estandarizacion.
- Enfoque prensa sectorial: Buenas practicas replicables en el sector.

4. {company} impulsa upgrades en lineas existentes sin frenar la produccion.
- Enfoque web: Modernizacion escalable.
- Enfoque LinkedIn: Valor de la retrocompatibilidad y la flexibilidad.
- Enfoque prensa sectorial: Inversion gradual con retorno medible.

5. Servicio de repuestos y reparacion para continuidad operativa.
- Enfoque web: Disponibilidad y respuesta.
- Enfoque LinkedIn: Cultura de fiabilidad.
- Enfoque prensa sectorial: Reduccion de riesgo de parada.

6. Soluciones para incremento de produccion con control de calidad.
- Enfoque web: Productividad sin comprometer calidad.
- Enfoque LinkedIn: Discipline operacional y estandares.
- Enfoque prensa sectorial: Competitividad internacional.

7. Alianzas tecnologicas y ecosistema de partners para proyectos complejos.
- Enfoque web: Capacidad de integracion.
- Enfoque LinkedIn: Cooperacion para resultados.
- Enfoque prensa sectorial: Innovacion abierta en industria.

8. Casos de exito en automatizacion intralogistica aplicada al corrugado.
- Enfoque web: Antes y despues del proyecto.
- Enfoque LinkedIn: Historias de impacto en planta.
- Enfoque prensa sectorial: Transformacion operacional con datos.

9. {company} y su enfoque en cumplimiento de plazos y costes.
- Enfoque web: Gobernanza de proyecto.
- Enfoque LinkedIn: Confianza, transparencia y ejecucion.
- Enfoque prensa sectorial: Gestion industrial orientada a resultados.

10. Hoja de ruta 2026 para innovacion en servicios y maquinaria del corrugado.
- Enfoque web: Vision anual.
- Enfoque LinkedIn: Invitacion a colaboracion y demos.
- Enfoque prensa sectorial: Perspectivas de mercado.

## Datos de apoyo recomendados para cada publicacion
- KPI de produccion antes/despues.
- Testimonio de cliente.
- Visual de linea o componente.
- CTA comercial claro (demo, visita tecnica, reunion).
"""

    brochure_products = f"""
# Brochure de productos y servicios - {company}

## Propuesta de valor
{company} ofrece una propuesta integral para la industria: {tagline}.

## Capacidades principales
- Ingenieria aplicada a mejora de lineas y procesos.
- Auditoria tecnica y operativa con foco en eficiencia.
- Automatizacion y soluciones de intralogistica.
- Servicios de soporte, repuestos y reparacion.
- Upgrades y optimizacion de procesos sin parar la operacion.

## Beneficios para cliente
- Mayor rendimiento de linea y estabilidad operacional.
- Mejora de calidad de producto y consistencia de produccion.
- Reduccion de riesgo por paradas no planificadas.
- Implementacion por fases con control de coste.

## Credenciales y traccion de marca
- Indicadores detectados en activos de marca: {stats_line}
- Evidencias tematicas recurrentes en contenidos: {theme_line}

## Modelo de trabajo
1. Diagnostico tecnico y de negocio.
2. Diseno de solucion y plan de implantacion.
3. Ejecucion con hitos y gobierno de proyecto.
4. Soporte post-implementacion y mejora continua.
"""

    brochure_corrugated = f"""
# Brochure de propuesta al sector del carton corrugado

## Enfoque sectorial
{company} centra su propuesta en resolver los retos de productividad, calidad y continuidad operativa de plantas de carton corrugado.

## Problemas que resolvemos
- Cuellos de botella en la linea.
- Variabilidad de calidad.
- Costes de parada y mantenimiento reactivo.
- Limitaciones de capacidad en picos de demanda.

## Solucion integral
- Diagnostico de linea corrugada y mapa de perdidas.
- Upgrades de equipos y procesos.
- Automatizacion de etapas criticas.
- Estrategia de repuestos y mantenimiento.
- Soporte tecnico especializado en planta.

## Referencias detectadas en datos internos
"""

    corr_lines = corr_offer or ["BHS wave line offer in Turkey", "Complete corrugator BHS 2500 mm model JETS 300-2500II up to 300 mpm"]
    brochure_corrugated += "\n".join(f"- {line}" for line in corr_lines)
    brochure_corrugated += """

## Resultado esperado
- Aumento de throughput.
- Mejora de OEE y reduccion de scrap.
- Menor tiempo de inactividad.
- Mayor previsibilidad de coste y plazo.
"""

    catalog_doc = f"""
# Catalogo comercial de soluciones {company}

## 1. Soluciones de maquinaria y automatizacion
- Automatizacion de procesos para corrugado.
- Integracion de equipos y perifericos.
- Modernizacion y upgrade de lineas existentes.

## 2. Servicios tecnicos
- Auditoria tecnico-operativa.
- Ingenieria de mejora y estandarizacion.
- Soporte de planta, repuestos y reparacion.
- Programas de optimizacion de procesos.

## 3. Soluciones por objetivo de negocio
- Incremento de produccion.
- Mejora de calidad de producto.
- Cumplimiento de plazo y coste.
- Reduccion de riesgo operacional.

## 4. Formatos de contratacion
- Proyecto llave en mano.
- Fases de mejora incremental.
- Servicios recurrentes de soporte.
"""

    messaging_doc = f"""
# Informe de mensajes y puntos clave de comunicacion

## Mensaje marco
{company} ayuda a fabricantes industriales, especialmente del carton corrugado, a producir mejor, con menor riesgo y mayor rentabilidad.

## Mensajes clave por prioridad
1. Fiabilidad operacional: menos paradas, mayor continuidad.
2. Productividad sostenible: mas capacidad con mejor calidad.
3. Flexibilidad tecnica: upgrades y mejoras sin bloqueos.
4. Soporte experto: acompanamiento antes, durante y despues del proyecto.
5. Solvencia de marca y partners: confianza para decisiones criticas.

## Pruebas y evidencias sugeridas
- Casos de mejora de throughput y calidad.
- Comparativas antes/despues de intervencion.
- KPIs de mantenimiento y disponibilidad.
- Referencias de clientes y socios.

## Objeciones comerciales y respuesta
- "No quiero riesgo operativo": plan por fases + mitigaciones + soporte.
- "No puedo parar planta": enfoque de modernizacion escalable.
- "Dudo del retorno": KPI base, objetivo y seguimiento de ROI.

## Adaptacion por canal
- Web: educar y demostrar autoridad.
- LinkedIn: liderazgo tecnico y casos.
- Email comercial: propuesta concreta con CTA.
- Dossier de ventas: argumento tecnico + economico.
"""

    toolkit_doc = f"""
# Kit de documentos comerciales recomendados

## Entregables ya generados en este paquete
- Noticias propuestas multi-plataforma.
- Brochure de productos y servicios.
- Brochure sector carton corrugado.
- Catalogo comercial de soluciones y servicios.
- Informe de mensajes y puntos clave.
- Documentos analiticos del motor de IA del workspace (summary, report, executive summary, presentation, timeline, comparison, client brief, intelligence brief, knowledge graph).

## Piezas sugeridas para siguiente iteracion
- Fichas de producto por familia de solucion.
- One-pager por vertical de cliente.
- Secuencias de email para prospeccion.
- Guiones para video comercial corto.
- Landing copy con CTA por caso de uso.

## Entidades y temas detectados (muestra)
- Organizaciones: {", ".join(entities.get("organization", [])[:12]) or "N/A"}
- Productos/tecnologias: {", ".join(entities.get("product", [])[:12]) or "N/A"}
- Temas: {theme_line}
"""

    _write(output_dir / "01_noticias_multiplataforma_ingecart.md", possible_news)
    _write(output_dir / "02_brochure_productos_y_servicios_ingecart.md", brochure_products)
    _write(output_dir / "03_brochure_sector_carton_corrugado_ingecart.md", brochure_corrugated)
    _write(output_dir / "04_catalogo_comercial_ingecart.md", catalog_doc)
    _write(output_dir / "05_mensajes_clave_y_argumentario_ingecart.md", messaging_doc)
    _write(output_dir / "06_kit_documental_comercial_ingecart.md", toolkit_doc)


def main() -> None:
    if not SOURCE_FOLDER.exists():
        raise FileNotFoundError(f"Target source folder not found: {SOURCE_FOLDER}")

    tag = _now_tag()
    output_dir = TARGET_FOLDER / f"ENTREGABLES_INGECART_{tag}"
    std_dir = output_dir / "_analisis_automatico"

    output_dir.mkdir(parents=True, exist_ok=True)
    std_dir.mkdir(parents=True, exist_ok=True)

    reader = FolderReader(recursive=True, max_file_size_mb=80)
    discovered = _discover_sources(reader)

    parser = DocumentParser()
    extractor = ContentExtractor(use_spacy=True)
    docs = []
    for item in discovered:
        try:
            doc = parser.parse(item["path"])
            doc = extractor.enrich(doc)
            docs.append(doc)
        except Exception as exc:
            from document_analysis.models import DocumentInfo, DocumentType

            docs.append(
                DocumentInfo(
                    file_path=item["path"],
                    file_name=Path(item["path"]).name,
                    doc_type=DocumentType.UNKNOWN,
                    error=str(exc),
                )
            )

    stats = _build_stats(output_dir, discovered)
    analysis = ContextAnalyzer().analyze_folder(docs, str(output_dir), stats)

    generator = OutputGenerator()
    std_outputs = {
        "summary": OutputFormat.SUMMARY,
        "executive_summary": OutputFormat.EXECUTIVE_SUMMARY,
        "report": OutputFormat.REPORT,
        "presentation": OutputFormat.PRESENTATION,
        "list": OutputFormat.LIST,
        "timeline": OutputFormat.TIMELINE,
        "comparison": OutputFormat.COMPARISON,
        "client_brief": OutputFormat.CLIENT_BRIEF,
        "new_brief": OutputFormat.NEW_BRIEF,
        "knowledge_graph": OutputFormat.KNOWLEDGE_GRAPH,
        "database_entry": OutputFormat.DATABASE_ENTRY,
    }

    for name, fmt in std_outputs.items():
        out = generator.generate(analysis, fmt)
        if name == "database_entry":
            _write(std_dir / f"{name}.json", out.content)
        else:
            _write(std_dir / f"{name}.md", out.content)

    facts = _extract_brief_facts()
    _build_custom_docs(output_dir, analysis, facts)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "bundle_dir": None,
        "files_copied_to_bundle": 0,
        "supported_files_discovered": len(discovered),
        "parsed_documents": len(docs),
        "cross_themes": analysis.cross_themes,
        "gaps": analysis.gaps,
        "contradictions": analysis.contradictions,
    }
    _write(output_dir / "00_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

    print(f"KIT_GENERADO={output_dir}")
    print("FUENTES_COPIADAS=0")
    print(f"DOCUMENTOS_ANALIZADOS={len(discovered)}")


if __name__ == "__main__":
    main()
