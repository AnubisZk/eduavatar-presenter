"""FastAPI entrypoint for EduAvatar Presenter Studio."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import avatar, presentation, render, upload, voice


# Storage is kept inside the backend tree so local development is simple.
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"


def _allowed_origins() -> list[str]:
    """Read comma-separated frontend origins for deployed environments."""
    default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    configured = os.getenv("FRONTEND_ORIGINS", "")
    extra_origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return default_origins + extra_origins


app = FastAPI(
    title="EduAvatar Presenter Studio API",
    description="Modular backend for consent-first avatar presentation generation.",
    version="0.1.0",
)


# Vite runs on port 5173 by default; permissive local CORS keeps the prototype easy to run.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_origin_regex=(
        r"http://(localhost|127\.0\.0\.1):\d+"
        r"|https://([a-z0-9-]+--)?eduavatar-presenter\.netlify\.app"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Expose generated media through stable URLs that the React preview can display.
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")


# Route modules are intentionally separated by workflow area for future model integrations.
app.include_router(upload.router)
app.include_router(presentation.router)
app.include_router(voice.router)
app.include_router(avatar.router)
app.include_router(render.router)


@app.get("/health")
def health_check():
    """Return a small health payload for frontend connectivity checks."""
    return {"status": "ok", "service": "eduavatar-presenter-api"}
