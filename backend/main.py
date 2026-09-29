import os
import sys

# Ensure project root is on the path so `backend.*` imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import LOCAL_API_KEY, SERVER_HOST, SERVER_PORT
from backend.routers import upload, generate, export, ai

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Synthetic Data Platform API",
    description="Schema-aware synthetic data generation: tabular, relational, and documents.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production via ALLOWED_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(export.router)
app.include_router(ai.router)

# ── Health / Root ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "service": "Synthetic Data Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Root"])
def health_check():
    return {
        "status": "healthy",
        "service": "synthetic-data-platform",
        "host": f"{SERVER_HOST}:{SERVER_PORT}",
        "local_key_configured": bool(LOCAL_API_KEY),
    }


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"🚀 Starting server at http://{SERVER_HOST}:{SERVER_PORT}")
    import uvicorn
    uvicorn.run("backend.main:app", host=SERVER_HOST, port=int(SERVER_PORT), reload=True)