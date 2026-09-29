import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
except ImportError:
    from backend.compat.fastapi_compat import (
        FastAPI, CORSMiddleware, StaticFiles, HTMLResponse, JSONResponse
    )

from backend.config import LOCAL_API_KEY, SERVER_HOST, SERVER_PORT
from backend.routers import upload, generate, export, ai

app = FastAPI(
    title="Synthetic Data Platform API",
    description="A schema-aware synthetic data generation platform.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(export.router)
app.include_router(ai.router)

# Mount Static UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "synthetic-data-platform",
        "host": f"{SERVER_HOST}:{SERVER_PORT}",
        "local_key_configured": bool(LOCAL_API_KEY)
    }

if __name__ == "__main__":
    print(f"Starting server at http://{SERVER_HOST}:{SERVER_PORT}")
    try:
        import uvicorn
        uvicorn.run("backend.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
    except ImportError:
        from backend.compat.fastapi_compat import run_compat_server
        run_compat_server(app, host=SERVER_HOST, port=SERVER_PORT)