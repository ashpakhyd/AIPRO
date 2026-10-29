from fastapi import APIRouter, BackgroundTasks
from app.news.service import get_top5_events, run_news_pipeline, get_all_articles

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/top5")
async def top5_events():
    events = await get_top5_events()
    return {"events": events, "total": len(events)}


@router.get("/articles")
async def all_articles(limit: int = 50):
    articles = await get_all_articles(limit)
    return {"articles": articles, "total": len(articles)}


@router.post("/refresh")
async def refresh_news(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_news_pipeline)
    return {"message": "News refresh started in background"}
