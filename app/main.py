from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routes import ai, alerts, auth, cases, doctors, hospitals, profiles, reports, reviews

settings = get_settings()

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AquaSentinel SIH backend API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(doctors.router, prefix="/api")
app.include_router(hospitals.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
def root():
    return {
        "message": "AquaSentinel Backend",
        "docs": "/docs",
        "health": "/api/health",
    }
