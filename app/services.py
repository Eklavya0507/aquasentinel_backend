from __future__ import annotations

import math
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import pandas as pd
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import (
    DoctorProfile,
    DoctorReview,
    DoctorSchedule,
    Hospital,
    HospitalHour,
    HospitalScheduleException,
    ModelAAssessment,
    ModelBRiskSnapshot,
    Profile,
    VerificationStatus,
)

settings = get_settings()
IST = ZoneInfo("Asia/Kolkata")


def calculate_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def hospital_open_now(db: Session, hospital: Hospital, now: datetime | None = None) -> bool:
    now = now or datetime.now(IST)
    today = now.date()

    exception = db.scalar(
        select(HospitalScheduleException).where(
            HospitalScheduleException.hospital_id == hospital.id,
            HospitalScheduleException.exception_date == today,
        )
    )
    if exception:
        if exception.exception_type.upper() in {"CLOSED", "EMERGENCY_ONLY"}:
            return hospital.emergency_available if exception.exception_type.upper() == "EMERGENCY_ONLY" else False
        if exception.open_time and exception.close_time:
            return exception.open_time <= now.time() <= exception.close_time

    hour = db.scalar(
        select(HospitalHour).where(
            HospitalHour.hospital_id == hospital.id,
            HospitalHour.day_of_week == now.weekday(),
        )
    )
    if not hour:
        return False
    if hour.is_closed:
        return False
    if hour.open_time and hour.close_time:
        return hour.open_time <= now.time() <= hour.close_time
    return False


def doctor_available_now(db: Session, doctor_id: int, hospital_id: int, now: datetime | None = None) -> bool:
    now = now or datetime.now(IST)
    schedule = db.scalar(
        select(DoctorSchedule).where(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.hospital_id == hospital_id,
            DoctorSchedule.day_of_week == now.weekday(),
            DoctorSchedule.is_active.is_(True),
            DoctorSchedule.start_time <= now.time(),
            DoctorSchedule.end_time >= now.time(),
        )
    )
    if not schedule:
        return False
    if schedule.valid_from and now.date() < schedule.valid_from:
        return False
    if schedule.valid_until and now.date() > schedule.valid_until:
        return False
    return True


def doctor_rating(db: Session, doctor_id: int) -> tuple[float | None, int]:
    avg, count = db.execute(
        select(func.avg(DoctorReview.overall_rating), func.count(DoctorReview.id)).where(
            DoctorReview.doctor_id == doctor_id,
            DoctorReview.status == "VISIBLE",
        )
    ).one()
    return (round(float(avg), 2) if avg is not None else None, int(count or 0))


def recommend_doctors(
    db: Session,
    profile: Profile,
    specialization: str | None,
    preferred_language: str | None,
    max_distance_km: float,
):
    doctors = db.scalars(
        select(DoctorProfile).where(
            DoctorProfile.verification_status == VerificationStatus.APPROVED
        )
    ).all()

    results = []
    for doctor in doctors:
        langs = [x.language_code.lower() for x in doctor.languages]
        rating, review_count = doctor_rating(db, doctor.id)

        for schedule in doctor.schedules:
            hospital = schedule.hospital
            if not hospital or not hospital.is_active:
                continue

            distance = haversine_km(
                profile.current_latitude,
                profile.current_longitude,
                hospital.latitude,
                hospital.longitude,
            )
            if distance is not None and distance > max_distance_km:
                continue

            score = 0.0
            reasons = []

            if specialization:
                if specialization.lower() in doctor.specialization.lower():
                    score += 40
                    reasons.append("specialization match")
                else:
                    score += 8
            else:
                score += 20

            is_open = hospital_open_now(db, hospital)
            is_available = doctor_available_now(db, doctor.id, hospital.id)
            if is_open:
                score += 10
                reasons.append("hospital open")
            if is_available:
                score += 20
                reasons.append("doctor available now")

            if preferred_language and preferred_language.lower() in langs:
                score += 15
                reasons.append("language match")

            if distance is not None:
                score += max(0, 10 * (1 - distance / max_distance_km))
                reasons.append(f"{distance:.1f} km away")

            if rating is not None:
                score += (rating / 5) * 5

            results.append(
                {
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.account.full_name,
                    "specialization": doctor.specialization,
                    "hospital_id": hospital.id,
                    "hospital_name": hospital.name,
                    "hospital_open": is_open,
                    "available_now": is_available,
                    "languages": [x.language_code for x in doctor.languages],
                    "distance_km": round(distance, 2) if distance is not None else None,
                    "rating": rating,
                    "review_count": review_count,
                    "score": round(score, 2),
                    "reasons": reasons,
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:20]


class GenericJoblibModel:
    def __init__(self, model_path: str, features_path: str = "", encoder_path: str = ""):
        self.model_path = model_path
        self.features_path = features_path
        self.encoder_path = encoder_path
        self._model = None
        self._features = None
        self._encoder = None

    def _ensure(self):
        if not self.model_path or not Path(self.model_path).exists():
            raise HTTPException(status_code=503, detail="AI model not configured on the backend")

        if self._model is None:
            self._model = joblib.load(self.model_path)

        if self.features_path and Path(self.features_path).exists() and self._features is None:
            self._features = joblib.load(self.features_path)

        if self.encoder_path and Path(self.encoder_path).exists() and self._encoder is None:
            self._encoder = joblib.load(self.encoder_path)

    def predict(self, inputs: dict):
        self._ensure()

        df = pd.DataFrame([inputs])

        features = self._features
        if features is None and hasattr(self._model, "feature_names_in_"):
            features = list(self._model.feature_names_in_)

        if features is not None:
            missing = [f for f in features if f not in df.columns]
            if missing:
                raise HTTPException(
                    status_code=422,
                    detail={"message": "Model inputs missing required features", "missing_features": missing},
                )
            df = df[list(features)]

        pred = self._model.predict(df)[0]
        if self._encoder is not None:
            try:
                pred_label = self._encoder.inverse_transform([pred])[0]
            except Exception:
                pred_label = pred
        else:
            pred_label = pred

        probabilities = None
        confidence = None
        if hasattr(self._model, "predict_proba"):
            probs = self._model.predict_proba(df)[0]
            classes = list(getattr(self._model, "classes_", range(len(probs))))
            labels = classes
            if self._encoder is not None:
                try:
                    labels = list(self._encoder.inverse_transform(classes))
                except Exception:
                    pass
            probabilities = {str(label): float(prob) for label, prob in zip(labels, probs)}
            if probabilities:
                confidence = max(probabilities.values())

        return {
            "predicted_label": str(pred_label),
            "confidence": confidence,
            "probabilities": probabilities,
        }


model_a_runtime = GenericJoblibModel(
    settings.MODEL_A_PATH,
    settings.MODEL_A_FEATURES_PATH,
    settings.MODEL_A_LABEL_ENCODER_PATH,
)

model_b_runtime = GenericJoblibModel(
    settings.MODEL_B_PATH,
    settings.MODEL_B_FEATURES_PATH,
)


def profile_context(profile: Profile) -> dict:
    return {
        "age": calculate_age(profile.date_of_birth),
        "state": profile.current_state or profile.primary_state,
        "district": profile.current_district or profile.primary_district,
        "latitude": profile.current_latitude,
        "longitude": profile.current_longitude,
    }
