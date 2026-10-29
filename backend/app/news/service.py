"""
News service — fetch, deduplicate, store, rank, AI analyze.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.database.db import NewsArticle, NewsEvent, AsyncSessionLocal
from app.news.fetcher import fetch_rss_articles
from app.news.ranker import get_top_events
from app.news.geo import detect_geo
from app.models.llm_provider import generate_text


async def run_news_pipeline():
    """Full pipeline: fetch → store → rank → AI analyze."""
    logger.info("Starting news pipeline...")
    async with AsyncSessionLocal() as db:
        articles = fetch_rss_articles()
        new_articles = await _store_articles(db, articles)
        logger.info(f"Stored {len(new_articles)} new articles")

        all_articles = await _get_recent_articles(db)
        top_events = get_top_events(all_articles, top_n=5)

        await _store_events(db, top_events)
        logger.info(f"Updated {len(top_events)} top events")


async def _store_articles(db: AsyncSession, articles: List[Dict]) -> List[Dict]:
    new_ones = []
    for a in articles:
        existing = await db.execute(
            select(NewsArticle).where(NewsArticle.content_hash == a["content_hash"])
        )
        if existing.scalar_one_or_none():
            continue
        record = NewsArticle(
            id=a["id"],
            source_name=a["source_name"],
            title=a["title"],
            url=a["url"],
            summary=a["summary"],
            category=a["category"],
            published_at=a["published_at"],
            content_hash=a["content_hash"],
        )
        db.add(record)
        new_ones.append(a)
    await db.commit()
    return new_ones


async def _get_recent_articles(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        select(NewsArticle).order_by(NewsArticle.fetched_at.desc()).limit(200)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "source_name": r.source_name,
            "title": r.title,
            "url": r.url,
            "summary": r.summary or "",
            "category": r.category,
            "published_at": r.published_at or datetime.now(timezone.utc),
            "content_hash": r.content_hash,
            "event_id": r.event_id,
        }
        for r in records
    ]


async def _store_events(db: AsyncSession, events: List[Dict]):
    # Clear old events
    from sqlalchemy import delete
    await db.execute(delete(NewsEvent))

    for event in events:
        articles_data = [
            {"title": a["title"], "url": a["url"], "source_name": a["source_name"]}
            for a in event["articles"]
        ]
        ai_analysis = await _generate_analysis(event)
        future_scenarios = await _generate_scenarios(event)

        country, lat, lng = detect_geo(event["title"] + " " + (event.get("summary") or ""))
        record = NewsEvent(
            id=str(uuid.uuid4()),
            title=event["title"],
            summary=event["summary"],
            category=event["category"],
            importance_score=event["importance_score"],
            source_count=event["source_count"],
            ai_analysis=ai_analysis,
            future_scenarios=future_scenarios,
            articles_json=json.dumps(articles_data),
            latitude=lat,
            longitude=lng,
            country=country,
            prediction_confidence=event.get("prediction_confidence", "MEDIUM"),
            score_breakdown_json=json.dumps(event.get("score_breakdown", {})),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(record)

    await db.commit()


async def _generate_analysis(event: Dict) -> str:
    try:
        sources_text = "\n".join(
            f"- {a['source_name']}: {a['title']}"
            for a in event["articles"][:5]
        )
        breakdown = event.get("score_breakdown", {})
        confidence = event.get("prediction_confidence", "MEDIUM")
        danger = breakdown.get("danger", 0)
        recency = breakdown.get("recency", 50)

        urgency = "BREAKING" if recency > 70 else "DEVELOPING" if recency > 30 else "ONGOING"
        threat_level = "CRITICAL" if danger >= 24 else "HIGH" if danger >= 16 else "MODERATE"

        prompt = (
            f"Tu ek bold global intelligence analyst hai.\n"
            f"Event Status: {urgency} | Threat Level: {threat_level} | Confidence: {confidence}\n\n"
            f"Hinglish mein (Roman script) 3-4 punchy sentences mein batao:\n"
            f"- Ye event kyun duniya ke liye khatarnak ya game-changing hai?\n"
            f"- Koi government gir sakti hai? Economy collapse ho sakti hai? War badh sakta hai?\n"
            f"- Iska seedha asar kahan padega aur kaun se countries affected honge?\n\n"
            f"Event: {event['title']}\n"
            f"Category: {event['category']}\n"
            f"Summary: {event['summary']}\n"
            f"Independent Sources ({event['source_count']}):\n{sources_text}\n\n"
            f"Bold Hinglish analysis (no sugarcoating, be direct):"
        )
        return generate_text(prompt).strip()
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
        return event.get("summary", "")


async def _generate_scenarios(event: Dict) -> str:
    try:
        confidence = event.get("prediction_confidence", "MEDIUM")
        breakdown = event.get("score_breakdown", {})
        danger = breakdown.get("danger", 0)

        prompt = (
            f"Tu ek geopolitical risk analyst hai. Prediction Confidence: {confidence}\n"
            f"Is event ke baad kya ho sakta hai? Hinglish mein (Roman script), evidence-based, 2 scenarios:\n\n"
            f"Event: {event['title']}\n"
            f"Summary: {event['summary']}\n"
            f"Danger Score: {danger}/40 | Sources: {event['source_count']}\n\n"
            f"Format exactly:\n"
            f"🔴 Sabse bada khatra: [worst case - specific consequences batao]\n"
            f"🟡 Agar control hua toh: [best case - kya conditions chahiye]"
        )
        return generate_text(prompt).strip()
    except Exception as e:
        logger.warning(f"Scenario generation failed: {e}")
        return ""


async def get_all_articles(limit: int = 50) -> List[Dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(NewsArticle).order_by(NewsArticle.fetched_at.desc()).limit(limit)
        )
        records = result.scalars().all()
        return [
            {
                "id": r.id,
                "source_name": r.source_name,
                "title": r.title,
                "url": r.url,
                "summary": r.summary or "",
                "category": r.category,
                "published_at": r.published_at.isoformat() if r.published_at else None,
            }
            for r in records
        ]


async def get_top5_events() -> List[Dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(NewsEvent).order_by(NewsEvent.importance_score.desc()).limit(5)
        )
        events = result.scalars().all()
        return [
            {
                "id": e.id,
                "title": e.title,
                "summary": e.summary,
                "category": e.category,
                "importance_score": e.importance_score,
                "source_count": e.source_count,
                "ai_analysis": e.ai_analysis,
                "future_scenarios": e.future_scenarios,
                "articles": json.loads(e.articles_json or "[]"),
                "latitude": e.latitude,
                "longitude": e.longitude,
                "country": e.country,
                "prediction_confidence": e.prediction_confidence,
                "score_breakdown": json.loads(e.score_breakdown_json or "{}"),
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in events
        ]
