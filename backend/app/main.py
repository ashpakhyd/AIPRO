from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler, generic_error_handler
from app.core.logging import logger
from app.database.db import init_db
from app.api import health, documents, chat
from app.api import news as news_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Knowledge Assistant backend...")
    await init_db()

    import os
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.data_dir, exist_ok=True)

    # Start news scheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.news.service import run_news_pipeline

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_news_pipeline,
        "interval",
        minutes=settings.news_fetch_interval_minutes,
        id="news_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"News scheduler started — interval: {settings.news_fetch_interval_minutes} min")

    # Run once on startup
    import asyncio
    asyncio.create_task(run_news_pipeline())

    yield

    scheduler.shutdown()
    logger.info("Shutting down.")


app = FastAPI(
    title="AI Knowledge Assistant",
    version="1.0.0",
    description="RAG-powered document Q&A with agentic workflows + News Intelligence.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(news_router.router, prefix="/api", tags=["News"])
