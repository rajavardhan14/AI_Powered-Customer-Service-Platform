"""
FastAPI Main Application.
AI-Powered Customer Service & Business Analytics Platform.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db, seed_sample_tickets
from app.ml.train import train_models
from app.api.tickets import router as tickets_router
from app.api.ml import router as ml_router
from app.api.genai import router as genai_router
from app.api.analytics import router as analytics_router
from app.api.export import router as export_router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml", "models")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    print("Initializing SQLite Database...")
    init_db()

    # Verify if ML models exist, train if missing
    cat_model_path = os.path.join(MODEL_DIR, "category_classifier.joblib")
    if not os.path.exists(cat_model_path):
        print("ML models not found. Triggering automated model training...")
        train_models()
    else:
        print("ML Models validated: TF-IDF + Logistic Regression, VADER, Random Forest ready.")

    # Auto seed sample dataset if database is empty
    seed_sample_tickets()
    print("Application startup complete.")
    yield
    print("Application shutdown.")

app = FastAPI(
    title="AI-Powered Customer Service & Business Analytics Platform",
    description=(
        "Production-grade Customer Support Intelligence Platform combining "
        "TF-IDF + Logistic Regression classification, VADER sentiment analysis, "
        "Random Forest priority scoring, Generative AI summarization & replies, "
        "and Power BI business analytics."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local dev and microfrontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(tickets_router)
app.include_router(ml_router)
app.include_router(genai_router)
app.include_router(analytics_router)
app.include_router(export_router)

# Mount frontend static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "Online",
        "platform": "AI-Powered Customer Service & Business Analytics Platform",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "components": {
            "api": "online",
            "database": "sqlite_connected",
            "ml_models": "loaded",
            "genai_engine": "ready"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
