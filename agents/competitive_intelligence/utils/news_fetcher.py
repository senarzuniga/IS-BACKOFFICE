import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)


def fetch_news(company_name: str, days_back: int = 90, api_key: str = None) -> List[Dict[str, Any]]:
    key = api_key or os.getenv("NEWSAPI_KEY")
    if not key:
        logger.info("NEWSAPI_KEY not configured — skipping news fetch")
        return []

    url = "https://newsapi.org/v2/everything"
    since = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "q": company_name,
        "from": since,
        "sortBy": "relevancy",
        "language": "es,en",
        "pageSize": 100,
        "apiKey": key,
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        j = r.json()
        items = []
        for a in j.get("articles", []):
            items.append({
                "title": a.get("title"),
                "url": a.get("url"),
                "source": a.get("source", {}).get("name"),
                "publishedAt": a.get("publishedAt"),
                "description": a.get("description"),
            })
        return items
    except Exception as e:
        logger.debug("news fetch failed: %s", e)
        return []
