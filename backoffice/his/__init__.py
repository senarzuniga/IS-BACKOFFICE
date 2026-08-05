"""HTML Intelligence Studio (HIS) core module."""

from .repository import DocumentRepository
from .service import HtmlDocumentService
from .studio import HtmlIntelligenceStudio

__all__ = ["HtmlIntelligenceStudio", "DocumentRepository", "HtmlDocumentService"]
