"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import chat, quiz, progress

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)

app = FastAPI(
    title="Owen's Learn Agent",
    description="An AI-powered tutoring agent built with Azure AI Foundry",
    version="0.1.0",
)

# CORS – allow the frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(chat.router)
app.include_router(quiz.router)
app.include_router(progress.router)

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    """Serve the web UI."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
