"""
News fetcher — uses free RSS feeds, no API key required.
Optional: NewsAPI for more sources (set NEWS_API_KEY in .env)
"""
import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

import feedparser
import httpx

from app.core.logging import logger
from app.core.config import get_settings

settings = get_settings()

RSS_SOURCES = [
    # Geopolitics & World Affairs
    {"name": "Reuters World",       "url": "https://feeds.reuters.com/reuters/worldNews",                        "category": "geopolitics"},
    {"name": "Reuters Politics",     "url": "https://feeds.reuters.com/reuters/politicsNews",                    "category": "politics"},
    {"name": "BBC World",            "url": "http://feeds.bbci.co.uk/news/world/rss.xml",                       "category": "world"},
    {"name": "Al Jazeera",           "url": "https://www.aljazeera.com/xml/rss/all.xml",                        "category": "geopolitics"},
    {"name": "The Guardian World",   "url": "https://www.theguardian.com/world/rss",                            "category": "world"},
    {"name": "Foreign Policy",       "url": "https://foreignpolicy.com/feed/",                                  "category": "geopolitics"},
    # Economy & Markets
    {"name": "Reuters Business",     "url": "https://feeds.reuters.com/reuters/businessNews",                   "category": "economy"},
    {"name": "Reuters Finance",      "url": "https://feeds.reuters.com/reuters/financialNews",                  "category": "economy"},
    {"name": "Bloomberg Markets",    "url": "https://feeds.bloomberg.com/markets/news.rss",                     "category": "economy"},
    {"name": "FT World",             "url": "https://www.ft.com/world?format=rss",                              "category": "economy"},
    # Conflicts & Security
    {"name": "BBC Middle East",      "url": "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml",           "category": "conflict"},
    {"name": "BBC Asia",             "url": "http://feeds.bbci.co.uk/news/world/asia/rss.xml",                  "category": "conflict"},
    {"name": "BBC Europe",           "url": "http://feeds.bbci.co.uk/news/world/europe/rss.xml",                "category": "conflict"},
    {"name": "Al Jazeera War",       "url": "https://www.aljazeera.com/xml/rss/all.xml",                        "category": "conflict"},
    # Political Crisis
    {"name": "The Guardian Politics","url": "https://www.theguardian.com/politics/rss",                         "category": "politics"},
    {"name": "Politico",             "url": "https://www.politico.com/rss/politicopicks.xml",                   "category": "politics"},
    # Tech & AI disruption
    {"name": "BBC Technology",       "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",                  "category": "technology"},
    {"name": "TechCrunch",           "url": "https://techcrunch.com/feed/",                                     "category": "technology"},
]


def _make_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _parse_date(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_rss_articles() -> List[Dict[str, Any]]:
    articles = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:10]:
                url = getattr(entry, "link", "")
                if not url:
                    continue
                title = _strip_html(getattr(entry, "title", ""))
                summary = _strip_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))[:500]
                articles.append({
                    "id": str(uuid.uuid4()),
                    "source_name": source["name"],
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "category": source["category"],
                    "published_at": _parse_date(entry),
                    "content_hash": _make_hash(url),
                    "event_id": None,
                })
            logger.info(f"Fetched {len(feed.entries)} articles from {source['name']}")
        except Exception as e:
            logger.warning(f"RSS fetch failed for {source['name']}: {e}")

    if settings.news_api_key:
        try:
            articles += _fetch_newsapi()
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}")

    return articles


def _fetch_newsapi() -> List[Dict[str, Any]]:
    resp = httpx.get(
        "https://newsapi.org/v2/top-headlines",
        params={"language": "en", "pageSize": 20, "apiKey": settings.news_api_key},
        timeout=10,
    )
    resp.raise_for_status()
    articles = []
    for a in resp.json().get("articles", []):
        url = a.get("url", "")
        if not url:
            continue
        articles.append({
            "id": str(uuid.uuid4()),
            "source_name": a.get("source", {}).get("name", "NewsAPI"),
            "title": (a.get("title") or "").strip(),
            "url": url,
            "summary": (a.get("description") or "")[:500],
            "category": "general",
            "published_at": datetime.now(timezone.utc),
            "content_hash": _make_hash(url),
            "event_id": None,
        })
    return articles
