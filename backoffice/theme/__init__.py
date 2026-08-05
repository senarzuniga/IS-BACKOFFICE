"""INGECART IS-BACKOFFICE — Design System package."""
from .design_system import DS, DARK, LIGHT, INDUSTRIAL
from .global_css import inject_theme, get_theme_css, INDUSTRIAL_CSS

__all__ = ["DS", "DARK", "LIGHT", "INDUSTRIAL", "inject_theme", "get_theme_css", "INDUSTRIAL_CSS"]
