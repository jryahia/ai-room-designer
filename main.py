import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn

logger = logging.getLogger(__name__)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db
from router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("data").mkdir(exist_ok=True)
    init_db()

    if not settings.openai_api_key:
        logger.warning(
            "OPENAI_API_KEY is not set. "
            "Design generation and image rendering will be unavailable. "
            "Set it in .env file: OPENAI_API_KEY=sk-..."
        )
    else:
        logger.info("OpenAI API key loaded (model: %s)", settings.openai_model)

    logger.info("AI Room Designer running at http://%s:%s", settings.app_host, settings.app_port)
    yield
    logger.info("Shutting down AI Room Designer")


app = FastAPI(
    title="AI Room Designer",
    description="AI-powered interior design proposals with photorealistic renders",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="info",
    )
