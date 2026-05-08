"""Structured data extractors: market intelligence, B2B leads, content aggregation."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

# ── Compiled patterns ─────────────────────────────────────────────────────────

PRICE_RE = re.compile(
    r"(?:[\$€£¥]|EUR|USD|GBP|CHF)\s*[\d\.,]+|[\d\.,]+\s*(?:€|EUR|USD|\$|£|GBP)",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?){2,4}\d{2,4}"
)
LINKEDIN_RE = re.compile(r"linkedin\.com/(?:in|company)/[\w\-]+", re.IGNORECASE)
DATE_RE = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}")

ROLE_KEYWORDS = [
    "CEO", "CTO", "CFO", "COO", "CMO", "CSO",
    "Director", "Manager", "Head of", "VP", "Vice President", "President",
    "Founder", "Partner", "Sales", "Marketing", "Procurement",
    "Supply Chain", "Operations", "Director Comercial", "Responsable de",
    "Jefe de", "Gerente", "Delegado", "Country Manager",
]

BLOCKED_EMAILS = {"example", "test", "sample", "noreply", "no-reply",
                  "donotreply", "info@example", "user@example"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "html.parser")


def _og_site_name(html: str) -> str:
    s = _soup(html[:5_000])
    tag = s.find("meta", property="og:site_name")
    if tag and tag.get("content"):
        return str(tag["content"]).strip()
    return ""


def _domain_company(url: str) -> str:
    netloc = urlparse(url).netloc.lower().replace("www.", "")
    return netloc.split(".")[0].title()


# ── Market Extractor ─────────────────────────────────────────────────────────

class MarketExtractor:
    """Extract pricing, product catalogue, and competitor data from a crawled page."""

    PRODUCT_SELECTORS = (
        "[class*='product']", "[class*='item']", "[class*='catalog']",
        "[class*='listing']", "[class*='card']", "article",
    )

    CATEGORIES: Dict[str, List[str]] = {
        "machinery":   ["machinery", "machine", "equipment", "maquinaria", "equipo", "corrugadora"],
        "software":    ["software", "platform", "saas", "digital", "app", "cloud"],
        "services":    ["service", "consulting", "servicio", "consultoría", "asesoría"],
        "printing":    ["print", "impresión", "corrugado", "packaging", "paper"],
        "automation":  ["automation", "robot", "automatización", "conveyor", "transport"],
        "retail":      ["shop", "store", "tienda", "retail", "e-commerce"],
    }

    def extract(self, page: Dict[str, Any]) -> Dict[str, Any]:
        text = page.get("text", "")
        html = page.get("html", "")
        url  = page.get("url", "")

        company  = _og_site_name(html) or _domain_company(url)
        prices   = self._extract_prices(text)
        products = self._extract_products(html)
        category = self._classify_category(text)

        return {
            "url":        url,
            "company":    company,
            "title":      page.get("title", ""),
            "prices":     prices,
            "products":   products,
            "category":   category,
            "crawled_at": page.get("crawled_at"),
        }

    def _extract_prices(self, text: str) -> List[str]:
        return list(dict.fromkeys(PRICE_RE.findall(text)))[:30]

    def _extract_products(self, html: str) -> List[Dict[str, str]]:
        soup = _soup(html)
        products: List[Dict[str, str]] = []
        seen: set = set()
        for sel in self.PRODUCT_SELECTORS:
            for el in soup.select(sel)[:30]:
                heading = el.find(["h1", "h2", "h3", "h4"])
                if not heading:
                    continue
                name = heading.get_text(strip=True)
                if not name or name in seen or len(name) > 250:
                    continue
                seen.add(name)
                m = PRICE_RE.search(el.get_text())
                price = m.group(0) if m else ""
                description_tag = el.find("p")
                description = description_tag.get_text(strip=True)[:300] if description_tag else ""
                products.append({"name": name, "price": price, "description": description})
        return products[:20]

    def _classify_category(self, text: str) -> str:
        t = text.lower()
        for cat, kws in self.CATEGORIES.items():
            if any(kw in t for kw in kws):
                return cat
        return "general"


# ── Lead Extractor ────────────────────────────────────────────────────────────

class LeadExtractor:
    """Extract B2B leads: contacts, emails, phones, roles, LinkedIn profiles."""

    SECTORS: Dict[str, List[str]] = {
        "manufacturing": ["manufactur", "fabricac", "industrial", "plant", "factory"],
        "printing":      ["print", "impres", "packaging", "corrugado", "label"],
        "technology":    ["software", "tech", "digital", "ai", "ia", "cloud", "saas"],
        "services":      ["consult", "service", "asesor", "advisory"],
        "retail":        ["retail", "shop", "store", "tienda", "ecommerce"],
        "logistics":     ["logistic", "logistics", "transport", "supply chain", "warehouse"],
    }

    TLD_COUNTRY: Dict[str, str] = {
        "es": "España", "fr": "Francia", "de": "Alemania",
        "uk": "Reino Unido", "it": "Italia", "pt": "Portugal",
        "nl": "Países Bajos", "be": "Bélgica", "ch": "Suiza",
        "eu": "Europa", "com": "Internacional",
    }

    def extract(self, page: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = page.get("text", "")
        html = page.get("html", "")
        url  = page.get("url", "")

        emails    = [e for e in EMAIL_RE.findall(text) if self._valid_email(e)]
        phones    = self._clean_phones(PHONE_RE.findall(text))
        linkedins = LINKEDIN_RE.findall(html)
        roles     = self._detect_roles(text)
        names     = self._extract_names(html)
        company   = _og_site_name(html) or _domain_company(url)
        sector    = self._classify_sector(text)
        country   = self._infer_country(url, text)

        leads: List[Dict[str, Any]] = []

        for email in emails[:15]:
            idx = text.find(email)
            context = text[max(0, idx - 300):idx + 300]
            role = next((r for r in roles if r.lower() in context.lower()), "")
            name = self._find_name_near(context, names)
            leads.append({
                "company":      company,
                "email":        email,
                "phone":        phones[0] if phones else "",
                "linkedin":     linkedins[0] if linkedins else "",
                "role":         role,
                "contact_name": name,
                "source_url":   url,
                "sector":       sector,
                "country":      country,
            })

        # Partial lead when no email but phone/role/LinkedIn found
        if not leads and (phones or roles or linkedins):
            leads.append({
                "company":      company,
                "email":        "",
                "phone":        phones[0] if phones else "",
                "linkedin":     linkedins[0] if linkedins else "",
                "role":         roles[0] if roles else "",
                "contact_name": names[0] if names else "",
                "source_url":   url,
                "sector":       sector,
                "country":      country,
            })

        return leads

    # ── helpers ──────────────────────────────────────────────────

    def _valid_email(self, email: str) -> bool:
        low = email.lower()
        return not any(b in low for b in BLOCKED_EMAILS) and "." in email.split("@")[-1]

    def _clean_phones(self, raw: List[str]) -> List[str]:
        cleaned = []
        for p in raw:
            digits = re.sub(r"\D", "", p)
            if 7 <= len(digits) <= 15:
                cleaned.append(p.strip())
        return list(dict.fromkeys(cleaned))[:5]

    def _detect_roles(self, text: str) -> List[str]:
        found = []
        t = text.lower()
        for role in ROLE_KEYWORDS:
            if role.lower() in t:
                found.append(role)
        return found[:5]

    def _extract_names(self, html: str) -> List[str]:
        soup = _soup(html[:25_000])
        names: List[str] = []
        for el in soup.select(
            "[class*='team'], [class*='person'], [class*='staff'], "
            "[class*='member'], [class*='author'], [class*='bio']"
        ):
            heading = el.find(["h2", "h3", "h4", "strong"])
            if heading:
                name = heading.get_text(strip=True)
                if 3 < len(name) < 60 and sum(c.isalpha() for c in name) / max(len(name), 1) > 0.7:
                    names.append(name)
        return list(dict.fromkeys(names))[:10]

    def _find_name_near(self, context: str, names: List[str]) -> str:
        for name in names:
            if name in context:
                return name
        return ""

    def _classify_sector(self, text: str) -> str:
        t = text.lower()
        for sector, kws in self.SECTORS.items():
            if any(k in t for k in kws):
                return sector
        return "unknown"

    def _infer_country(self, url: str, text: str) -> str:
        tld = urlparse(url).netloc.rsplit(".", 1)[-1].lower()
        return self.TLD_COUNTRY.get(tld, tld.upper())


# ── Content Extractor ─────────────────────────────────────────────────────────

class ContentExtractor:
    """Extract structured content: news, blogs, trends, reviews."""

    TYPE_MAP: Dict[str, List[str]] = {
        "blog":    ["blog", "post", "article", "articulo"],
        "news":    ["news", "noticia", "press", "prensa"],
        "review":  ["review", "reseña", "rating", "opinion", "stars"],
        "trend":   ["trend", "tendencia", "market", "mercado", "insight"],
        "report":  ["report", "informe", "estudio", "whitepaper", "research"],
    }

    def extract(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        html = page.get("html", "")
        text = page.get("text", "")
        url  = page.get("url", "")

        soup = _soup(html)
        title   = page.get("title", "")
        summary = self._extract_summary(soup, text)
        author  = self._extract_author(soup)
        date    = self._extract_date(soup, text)
        tags    = self._extract_tags(soup, text)
        ctype   = self._classify_type(url, text)

        if not title or len(summary) < 50:
            return None

        return {
            "source_url":   url,
            "type":         ctype,
            "title":        title[:300],
            "summary":      summary[:1_000],
            "content":      text[:6_000],
            "author":       author,
            "published_at": date,
            "tags":         tags,
            "scraped_at":   page.get("crawled_at"),
        }

    # ── helpers ──────────────────────────────────────────────────

    def _extract_summary(self, soup: BeautifulSoup, full_text: str) -> str:
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return str(meta["content"])[:600]
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return str(og_desc["content"])[:600]
        # First paragraph longer than 80 chars
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if len(t) > 80:
                return t[:600]
        return full_text[:300]

    def _extract_author(self, soup: BeautifulSoup) -> str:
        for sel in [
            '[class*="author"]', '[rel="author"]',
            'meta[name="author"]', '[itemprop="author"]',
        ]:
            el = soup.select_one(sel)
            if el:
                return (el.get("content") or el.get_text(strip=True) or "")[:100]
        return ""

    def _extract_date(self, soup: BeautifulSoup, text: str) -> str:
        t = soup.find("time")
        if t:
            return str(t.get("datetime") or t.get_text(strip=True))[:30]
        m = DATE_RE.search(text)
        return m.group(0) if m else ""

    def _extract_tags(self, soup: BeautifulSoup, text: str) -> List[str]:
        tags: List[str] = []
        for el in soup.select('[class*="tag"], [class*="category"], [rel="tag"]')[:15]:
            tag = el.get_text(strip=True)
            if tag and len(tag) < 60:
                tags.append(tag)
        return list(dict.fromkeys(tags))[:10]

    def _classify_type(self, url: str, text: str) -> str:
        u = url.lower()
        t = text.lower()
        for ctype, kws in self.TYPE_MAP.items():
            if any(kw in u or kw in t for kw in kws):
                return ctype
        return "general"
