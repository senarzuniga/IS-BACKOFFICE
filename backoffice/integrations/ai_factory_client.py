from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class AIFactoryClient:
    """HTTP client for AI-FACTORY Cognitive Operating System APIs."""

    def __init__(self, base_url: Optional[str] = None, timeout_s: int = 20):
        self.base_url = (base_url or os.environ.get("AI_FACTORY_API_URL") or "http://localhost:8100").rstrip("/")
        self.timeout_s = int(timeout_s)

    def post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self._url(path)
        try:
            response = requests.post(url, json=payload, timeout=self.timeout_s)
            return self._as_payload(response)
        except requests.RequestException as exc:
            return {
                "status": "unavailable",
                "error": "ai_factory_unreachable",
                "detail": str(exc),
                "url": url,
            }

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self._url(path)
        try:
            response = requests.get(url, params=params, timeout=self.timeout_s)
            return self._as_payload(response)
        except requests.RequestException as exc:
            return {
                "status": "unavailable",
                "error": "ai_factory_unreachable",
                "detail": str(exc),
                "url": url,
            }

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    @staticmethod
    def _as_payload(response: requests.Response) -> Dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        if isinstance(body, dict):
            if "status_code" not in body:
                body["status_code"] = response.status_code
            if response.status_code >= 400 and "status" not in body:
                body["status"] = "error"
            return body

        return {
            "status_code": response.status_code,
            "body": body,
            "status": "ok" if response.status_code < 400 else "error",
        }
