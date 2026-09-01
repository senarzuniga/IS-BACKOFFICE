from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PORTAL_PARTES_PATH = REPO_ROOT / "portal_partes.html"


@dataclass(frozen=True)
class PortalPartesAnalysis:
    title: str
    tabs: list[str]
    panel_ids: list[str]
    default_category_count: int
    default_categories: list[str]
    capabilities: list[str]
    persistence_modes: list[str]
    admin_entities: list[str]
    reporting_outputs: list[str]
    limitations: list[str]


def portal_partes_path() -> Path:
    return PORTAL_PARTES_PATH


def load_portal_partes_html(path: Path | None = None) -> str:
    target = path or PORTAL_PARTES_PATH
    if not target.exists():
        raise FileNotFoundError(f"No se encontro el portal de partes: {target}")
    return target.read_text(encoding="utf-8")


def analyze_portal_partes(path: Path | None = None) -> PortalPartesAnalysis:
    html = load_portal_partes_html(path)
    title = _extract_title(html)
    tabs = re.findall(r'data-tab="([^"]+)"[^>]*>([^<]+)</button>', html)
    panel_ids = re.findall(r'<section class="panel(?: active)?" id="panel-([^"]+)">', html)
    default_categories = _extract_default_categories(html)

    capabilities: list[str] = []
    if 'id="btnLogin"' in html and "hashPin(" in html:
        capabilities.append("Login por trabajador con PIN hasheado en el navegador")
    if 'id="btnCargarParte"' in html:
        capabilities.append("Registro de partes por trabajador, OF/proyecto, fecha, categoria y horas")
    if 'id="tablaUltimos"' in html and 'data-edit="' in html:
        capabilities.append("Edicion y borrado de partes recientes por el propio usuario")
    if 'id="btnConsultar"' in html and "donutSVG(" in html:
        capabilities.append("Consulta operativa por OF con KPIs, timeline, reparto por categorias y trabajadores")
    if 'id="btnAddTrab"' in html and 'id="btnAddOf"' in html and 'id="btnAddCat"' in html:
        capabilities.append("Mantenimiento administrativo de trabajadores, OF/proyectos y categorias")
    if 'id="btnCsvOf"' in html and 'id="btnCsvTodo"' in html and 'id="btnInforme"' in html:
        capabilities.append("Exportacion a CSV y generacion de informe imprimible/PDF")

    persistence_modes: list[str] = []
    if "localStorage.setItem" in html:
        persistence_modes.append("Persistencia local en navegador")
    if "indexedDB.open" in html:
        persistence_modes.append("Recuperacion de manejador mediante IndexedDB")
    if "showSaveFilePicker" in html and "showOpenFilePicker" in html:
        persistence_modes.append("Sincronizacion de fichero JSON con OneDrive mediante File System Access API")

    admin_entities = ["Trabajadores", "OF / Proyectos", "Categorias de trabajo"]
    reporting_outputs = ["Consulta SCADA por OF", "CSV filtrado", "CSV global", "Informe imprimible / PDF"]

    limitations: list[str] = []
    if "el último que guarda manda" in html:
        limitations.append("Concurrencia basica: el ultimo guardado sobrescribe el estado compartido")
    if "SharePoint / Microsoft Graph" in html:
        limitations.append("No existe backend multiusuario real; el propio HTML recomienda evolucionar a SharePoint/Microsoft Graph")
    if "if(!FSA)" in html:
        limitations.append("La escritura en nube depende de Edge/Chrome con soporte File System Access")
    if "window.open" in html:
        limitations.append("El informe PDF depende de ventanas emergentes del navegador")

    return PortalPartesAnalysis(
        title=title,
        tabs=[label.strip() for _, label in tabs],
        panel_ids=panel_ids,
        default_category_count=len(default_categories),
        default_categories=default_categories,
        capabilities=capabilities,
        persistence_modes=persistence_modes,
        admin_entities=admin_entities,
        reporting_outputs=reporting_outputs,
        limitations=limitations,
    )


def _extract_title(html: str) -> str:
    match = re.search(r"<title>([^<]+)</title>", html)
    return match.group(1).strip() if match else "Portal de Partes"


def _extract_default_categories(html: str) -> list[str]:
    match = re.search(r"const CATS_DEFECTO=\[(.*?)\];", html, re.DOTALL)
    if not match:
        return []
    return re.findall(r"'([^']+)'", match.group(1))
