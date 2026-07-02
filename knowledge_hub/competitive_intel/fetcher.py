"""Fetcher interface (safe stub).

This module contains a non-networking placeholder Fetcher used by the
scaffold and tests. It deliberately does not perform HTTP requests.
"""

from typing import Optional


class Fetcher:
    def __init__(self, obey_robots: bool = True, rate_limit: float = 1.0) -> None:
        self.obey_robots = obey_robots
        self.rate_limit = rate_limit

    def fetch(self, url: str) -> str:
        """Return a placeholder response for `url`.

        Real network fetching must be implemented separately and must
        respect robots, rate limits and corporate policies.
        """
        return f"[FETCH_PLACEHOLDER] {url}"
