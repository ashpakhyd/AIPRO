"""
Improved ranker with:
1. Semantic clustering (sentence-transformers embeddings)
2. Recency decay (exponential)
3. Source diversity + credibility
4. Danger keyword boost
5. Cross-category amplification
6. Prediction confidence score
"""
import math
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import List, Dict, Any

# ── Category base weights ──────────────────────────────────────────────────
CATEGORY_WEIGHTS = {
    "conflict":    2.0,
    "geopolitics": 1.9,
    "politics":    1.7,
    "economy":     1.6,
    "world":       1.3,
    "technology":  1.0,
    "general":     0.8,
}

# ── High-impact danger keywords ────────────────────────────────────────────
DANGER_KEYWORDS = {
    "war", "attack", "invasion", "missile", "nuclear", "bomb", "explosion",
    "coup", "assassination", "troops", "airstrike", "ceasefire", "genocide",
    "collapse", "resign", "impeach", "protest", "riot", "revolution",
    "sanctions", "veto", "emergency", "martial law",
    "recession", "default", "bankruptcy", "crash", "inflation", "devaluation",
    "currency crisis", "bank run", "debt crisis",
    "earthquake", "tsunami", "hurricane", "flood", "wildfire", "pandemic",
    "outbreak", "famine", "hack", "cyberattack", "blackout",
}

# ── Source credibility tiers ───────────────────────────────────────────────
SOURCE_CREDIBILITY = {
    "Reuters World": 1.0, "Reuters Business": 1.0,
    "Reuters Finance": 1.0, "Reuters Politics": 1.0,
    "BBC World": 0.95, "BBC Middle East": 0.95,
    "BBC Asia": 0.95, "BBC Europe": 0.95, "BBC Technology": 0.9,
    "Al Jazeera": 0.9, "Al Jazeera War": 0.9,
    "The Guardian": 0.85, "The Guardian World": 0.85,
    "The Guardian Politics": 0.85, "Foreign Policy": 0.9,
    "Bloomberg Markets": 0.9, "FT World": 0.9,
    "Politico": 0.8, "TechCrunch": 0.75,
}

_embed_model = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            pass
    return _embed_model


def _cosine_sim(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb + 1e-9)


def _string_sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _semantic_sim(title_a: str, title_b: str, cache: Dict) -> float:
    model = _get_embed_model()
    if model is None:
        return _string_sim(title_a, title_b)
    if title_a not in cache:
        cache[title_a] = model.encode(title_a).tolist()
    if title_b not in cache:
        cache[title_b] = model.encode(title_b).tolist()
    return _cosine_sim(cache[title_a], cache[title_b])


def _recency_score(published_at) -> float:
    """Exponential decay: 1hr→95, 6hr→74, 24hr→30, 72hr→5"""
    if published_at is None:
        return 20.0
    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    hours_old = max((now - published_at).total_seconds() / 3600, 0)
    return round(100 * math.exp(-0.05 * hours_old), 2)


def _danger_score(title: str, summary: str) -> float:
    text = (title + " " + summary).lower()
    hits = sum(1 for kw in DANGER_KEYWORDS if kw in text)
    return min(hits * 8, 40)


def _source_score(articles: List[Dict]) -> float:
    unique = set(a["source_name"] for a in articles)
    diversity = min(len(unique) * 15, 45)
    avg_cred = sum(SOURCE_CREDIBILITY.get(s, 0.7) for s in unique) / len(unique)
    return round(diversity * avg_cred, 2)


def _cross_category_boost(title: str, summary: str) -> float:
    text = (title + " " + summary).lower()
    matched = sum(1 for kws in [
        ["war", "troops", "attack", "invasion", "missile"],
        ["economy", "recession", "inflation", "market", "dollar", "debt"],
        ["election", "government", "president", "minister", "resign"],
        ["nuclear", "weapon", "sanction", "nato"],
    ] if any(kw in text for kw in kws))
    return matched * 5.0


def _prediction_confidence(event: Dict) -> str:
    score = event.get("importance_score", 0)
    sources = event.get("source_count", 1)
    recency = event.get("recency_score", 20)
    if score >= 75 and sources >= 3 and recency >= 50:
        return "HIGH"
    elif score >= 45 and sources >= 2:
        return "MEDIUM"
    return "LOW"


def cluster_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    cache: Dict = {}

    for article in articles:
        best_match = None
        best_sim = 0.0

        for event in events:
            cat_match = event["category"] == article["category"]
            sim = _semantic_sim(event["title"], article["title"], cache)
            str_sim = _string_sim(event["title"], article["title"])
            combined = max(sim, str_sim)
            threshold = 0.62 if cat_match else 0.78

            if combined > threshold and combined > best_sim:
                best_sim = combined
                best_match = event

        if best_match:
            best_match["articles"].append(article)
            best_match["source_count"] = len(set(a["source_name"] for a in best_match["articles"]))
            if article["published_at"] and (
                best_match["published_at"] is None or
                article["published_at"] > best_match["published_at"]
            ):
                best_match["published_at"] = article["published_at"]
        else:
            events.append({
                "id": article["id"],
                "title": article["title"],
                "summary": article["summary"],
                "category": article["category"],
                "articles": [article],
                "source_count": 1,
                "published_at": article["published_at"],
            })

    return events


def score_event(event: Dict[str, Any]) -> Dict[str, Any]:
    recency = _recency_score(event.get("published_at"))
    source  = _source_score(event["articles"])
    danger  = _danger_score(event["title"], event.get("summary", ""))
    cross   = _cross_category_boost(event["title"], event.get("summary", ""))
    cat_w   = CATEGORY_WEIGHTS.get(event["category"], 1.0)

    raw = (recency * 0.25 + source * 0.30 + danger * 0.30 + cross * 0.15) * cat_w
    final = round(min(raw, 100), 2)

    event["importance_score"] = final
    event["recency_score"] = recency
    event["score_breakdown"] = {
        "recency":    round(recency, 1),
        "sources":    round(source, 1),
        "danger":     round(danger, 1),
        "cross_cat":  round(cross, 1),
        "cat_weight": cat_w,
        "final":      final,
    }
    return event


def get_top_events(articles: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    events = cluster_articles(articles)
    events = [score_event(e) for e in events]
    events.sort(key=lambda e: e["importance_score"], reverse=True)
    for e in events:
        e["prediction_confidence"] = _prediction_confidence(e)
    return events[:top_n]
