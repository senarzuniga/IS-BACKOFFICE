"""Discovery layer (stubs).

These are intentionally lightweight stubs used for architecture and tests.
Do NOT perform network operations here.
"""

from typing import List


class Discovery:
    """Stub discovery component.

    Example usage (no network):
        d = Discovery()
        urls = d.discover('https://example.com')  # returns []
    """

    def __init__(self) -> None:
        pass

    def discover(self, seed_url: str) -> List[str]:
        """Discover candidate source URLs from a seed.

        This implementation is a placeholder and returns an empty list.
        Real discovery should be implemented in a separate integration.
        """
        return []
