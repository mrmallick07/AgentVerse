"""
AgentVerse — Multi-Agent Research & Action Platform.
FastAPI application entry point.
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use Vertex AI backend for Gemini (authenticates via gcloud, no API key needed)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT", "prodogenie")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

from backend.api.routes import router

app = FastAPI(
    title="AgentVerse",
    description="Multi-Agent Research & Action Platform",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Serve frontend static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    return FileResponse(str(FRONTEND_DIR / "index.html"))
