"""Back Office System package."""

__all__ = ["CommercialIntelligenceOS"]


def __getattr__(name: str):
	if name == "CommercialIntelligenceOS":
		from .orchestration import CommercialIntelligenceOS
		return CommercialIntelligenceOS
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
