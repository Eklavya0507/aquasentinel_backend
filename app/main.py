from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .config import get_settings
from .database import Base, SessionLocal, engine
from .models import Hospital
from .routes import ai, alerts, auth, cases, doctors, hospitals, profiles, reports

settings = get_settings()
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version="1.0-sih-demo",
              description="AquaSentinel SIH college-level connected prototype backend")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for router in (auth.router, profiles.router, reports.router, cases.router, alerts.router,
               ai.router, hospitals.router, doctors.router):
    app.include_router(router, prefix="/api")


def seed_demo_hospitals():
    db = SessionLocal()
    try:
        if db.scalar(select(Hospital.id).limit(1)) is None:
            db.add_all([
                Hospital(name="AquaSentinel Demo District Hospital", state="Assam", district="Kamrup",
                         locality="Demo locality", phone="0361-DEMO", emergency_available=True, is_demo=True),
                Hospital(name="AquaSentinel Demo Community Health Centre", state="Meghalaya", district="East Khasi Hills",
                         locality="Demo locality", emergency_available=False, is_demo=True),
                Hospital(name="AquaSentinel Demo Referral Centre", state="Tripura", district="West Tripura",
                         locality="Demo locality", emergency_available=True, is_demo=True),
            ])
            db.commit()
    finally:
        db.close()

seed_demo_hospitals()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT,
            "version": "1.0-sih-demo"}


@app.get("/")
def root():
    return {"message": "AquaSentinel Backend", "docs": "/docs", "health": "/api/health"}
