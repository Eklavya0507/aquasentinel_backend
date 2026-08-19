from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import joblib
import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import CaseReport

settings = get_settings()
_B1_MODEL = None
_B1_ENCODER = None

B1_FEATURES = [
    "state", "district", "latitude", "longitude", "is_urban", "population_density", "age", "gender",
    "water_source", "water_treatment", "ph", "turbidity_ntu", "dissolved_oxygen_mg_l", "bod_mg_l",
    "fecal_coliform_per_100ml", "total_coliform_per_100ml", "tds_mg_l", "nitrate_mg_l", "fluoride_mg_l",
    "arsenic_ug_l", "open_defecation_rate", "toilet_access", "sewage_treatment_pct", "handwashing_practice",
    "month", "season", "avg_temperature_c", "avg_rainfall_mm", "avg_humidity_pct", "flooding",
]


def load_b1():
    global _B1_MODEL, _B1_ENCODER
    model_path = Path(settings.MODEL_B1_PATH)
    encoder_path = Path(settings.MODEL_B1_ENCODER_PATH)
    if not model_path.exists() or not encoder_path.exists():
        raise HTTPException(status_code=503, detail="B1 model files are not configured")
    if _B1_MODEL is None:
        try:
            _B1_MODEL = joblib.load(model_path)
            _B1_ENCODER = joblib.load(encoder_path)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"B1 model could not be loaded: {exc}")
    return _B1_MODEL, _B1_ENCODER


def predict_b1(inputs: dict) -> dict:
    model, encoder = load_b1()
    row = pd.DataFrame([{k: inputs[k] for k in B1_FEATURES}], columns=B1_FEATURES)
    try:
        encoded = int(model.predict(row)[0])
        probs = model.predict_proba(row)[0]
        classes = [str(x) for x in encoder.classes_]
        predicted_label = str(encoder.inverse_transform([encoded])[0])
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"B1 prediction failed: {exc}")
    probabilities = {name: float(prob) for name, prob in zip(classes, probs)}
    no_disease = probabilities.get("No_Disease", 0.0)
    environmental_score = round((1.0 - no_disease) * 100, 2)
    if environmental_score < 25:
        risk_level = "LOW"
    elif environmental_score < 50:
        risk_level = "MODERATE"
    elif environmental_score < 75:
        risk_level = "HIGH"
    else:
        risk_level = "VERY_HIGH"
    return {
        "predicted_label": predicted_label,
        "confidence": round(float(max(probs)), 4),
        "environmental_risk_score": environmental_score,
        "risk_level": risk_level,
        "probabilities": dict(sorted(probabilities.items(), key=lambda x: x[1], reverse=True)),
        "note": "Prototype environmental-risk model output; not a medical diagnosis or outbreak confirmation.",
    }


def surveillance_summary(db: Session) -> list[dict]:
    today = date.today()
    recent_start = today - timedelta(days=6)
    baseline_start = today - timedelta(days=34)
    baseline_end = today - timedelta(days=7)
    rows = db.scalars(select(CaseReport).where(CaseReport.case_date >= baseline_start)).all()
    grouped = defaultdict(lambda: {"recent": 0, "baseline_total": 0, "state": ""})
    for row in rows:
        if row.disease.strip().lower() in {"no_disease", "no disease"}:
            continue
        key = (row.district, row.disease)
        count = int(row.confirmed_cases or 0) + int(row.suspected_cases or 0)
        grouped[key]["state"] = row.state
        if recent_start <= row.case_date <= today:
            grouped[key]["recent"] += count
        elif baseline_start <= row.case_date <= baseline_end:
            grouped[key]["baseline_total"] += count

    output = []
    for (district, disease), value in grouped.items():
        recent = value["recent"]
        baseline_weekly = value["baseline_total"] / 4.0
        if recent == 0:
            level = "NORMAL"
            deviation = 0.0
        elif baseline_weekly <= 0:
            deviation = 100.0 if recent >= 3 else 0.0
            level = "WATCH" if recent >= 3 else "NORMAL"
        else:
            deviation = ((recent - baseline_weekly) / baseline_weekly) * 100
            if deviation >= 100 and recent >= 5:
                level = "CRITICAL"
            elif deviation >= 50:
                level = "HIGH"
            elif deviation >= 25:
                level = "WATCH"
            else:
                level = "NORMAL"
        output.append({
            "state": value["state"],
            "district": district,
            "disease": disease,
            "recent_7d_cases": recent,
            "baseline_weekly": round(baseline_weekly, 2),
            "deviation_pct": round(deviation, 1),
            "level": level,
            "source": "REGISTERED_OFFICIAL_DEMO_ENTRIES",
        })
    priority = {"CRITICAL": 4, "HIGH": 3, "WATCH": 2, "NORMAL": 1}
    output.sort(key=lambda x: (priority[x["level"]], x["recent_7d_cases"]), reverse=True)
    return output
