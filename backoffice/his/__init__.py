"""HTML Intelligence Studio (HIS) core module."""

from importlib import import_module
from typing import Any

__all__ = ["HtmlIntelligenceStudio", "DocumentRepository", "HtmlDocumentService"]

_EXPORTS = {
	"HtmlIntelligenceStudio": ("backoffice.his.studio", "HtmlIntelligenceStudio"),
	"DocumentRepository": ("backoffice.his.repository", "DocumentRepository"),
	"HtmlDocumentService": ("backoffice.his.service", "HtmlDocumentService"),
}


def __getattr__(name: str) -> Any:
	if name not in _EXPORTS:
		raise AttributeError(name)
	module_name, attribute_name = _EXPORTS[name]
	value = getattr(import_module(module_name), attribute_name)
	globals()[name] = value
	return value
