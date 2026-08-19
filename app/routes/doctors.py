from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, require_roles
from ..models import (
    Account,
    DoctorLanguage,
    DoctorProfile,
    DoctorSchedule,
    Profile,
    Role,
    VerificationStatus,
)
from ..schemas import DoctorScheduleCreate, RecommendationQuery
from ..services import recommend_doctors

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("")
def list_doctors(
    specialization: str | None = None,
    language: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(DoctorProfile).where(
        DoctorProfile.verification_status == VerificationStatus.APPROVED
    )
    if specialization:
        stmt = stmt.where(DoctorProfile.specialization.ilike(f"%{specialization}%"))

    doctors = db.scalars(stmt).all()
    result = []
    for d in doctors:
        languages = [x.language_code for x in d.languages]
        if language and language.lower() not in [x.lower() for x in languages]:
            continue
        result.append(
            {
                "id": d.id,
                "name": d.account.full_name,
                "specialization": d.specialization,
                "qualification": d.qualification,
                "years_experience": d.years_experience,
                "languages": languages,
            }
        )
    return result


@router.get("/me")
def doctor_me(
    account: Account = Depends(require_roles(Role.DOCTOR)),
):
    if not account.doctor_profile:
        raise HTTPException(status_code=404, detail="Doctor profile missing")
    d = account.doctor_profile
    return {
        "id": d.id,
        "name": account.full_name,
        "registration_number": d.registration_number,
        "specialization": d.specialization,
        "verification_status": d.verification_status.value,
        "languages": [x.language_code for x in d.languages],
        "schedules": [
            {
                "id": s.id,
                "hospital_id": s.hospital_id,
                "hospital_name": s.hospital.name if s.hospital else None,
                "day_of_week": s.day_of_week,
                "start_time": s.start_time,
                "end_time": s.end_time,
            }
            for s in d.schedules
        ],
    }


@router.post("/me/languages")
def add_language(
    language_code: str,
    account: Account = Depends(require_roles(Role.DOCTOR)),
    db: Session = Depends(get_db),
):
    d = account.doctor_profile
    if not d:
        raise HTTPException(status_code=404, detail="Doctor profile missing")
    existing = db.scalar(
        select(DoctorLanguage).where(
            DoctorLanguage.doctor_id == d.id,
            DoctorLanguage.language_code == language_code,
        )
    )
    if not existing:
        db.add(DoctorLanguage(doctor_id=d.id, language_code=language_code))
        db.commit()
    return {"message": "Language saved"}


@router.post("/me/schedules")
def add_schedule(
    data: DoctorScheduleCreate,
    account: Account = Depends(require_roles(Role.DOCTOR)),
    db: Session = Depends(get_db),
):
    d = account.doctor_profile
    if not d:
        raise HTTPException(status_code=404, detail="Doctor profile missing")
    row = DoctorSchedule(doctor_id=d.id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "message": "Schedule added"}


@router.post("/recommend")
def recommend(
    query: RecommendationQuery,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    profile = db.scalar(
        select(Profile).where(
            Profile.id == query.profile_id,
            Profile.account_id == account.id,
        )
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    preferred_language = query.preferred_language
    if not preferred_language and profile.preferred_languages:
        preferred_language = profile.preferred_languages[0]

    return recommend_doctors(
        db,
        profile,
        query.specialization,
        preferred_language,
        query.max_distance_km or 50,
    )


@router.patch("/{doctor_id}/verify")
def verify_doctor(
    doctor_id: int,
    approved: bool = True,
    account: Account = Depends(require_roles(Role.ADMIN, Role.GOVERNMENT)),
    db: Session = Depends(get_db),
):
    doctor = db.get(DoctorProfile, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.verification_status = (
        VerificationStatus.APPROVED if approved else VerificationStatus.REJECTED
    )
    doctor.account.status = doctor.verification_status
    db.commit()
    return {"message": "Doctor verification updated"}
