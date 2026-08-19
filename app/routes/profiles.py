from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account
from ..models import Account, MedicalHistory, Profile
from ..schemas import MedicalHistoryCreate, ProfileCreate

router = APIRouter(prefix="/profiles", tags=["Profiles"])


def owned(db: Session, account: Account, profile_id: int) -> Profile:
    row = db.scalar(select(Profile).where(Profile.id == profile_id, Profile.account_id == account.id))
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return row


def as_dict(x: Profile):
    return {"id": x.id, "name": x.name, "relationship": x.relationship,
            "date_of_birth": x.date_of_birth, "gender": x.gender,
            "caregiver_managed": x.caregiver_managed, "primary_state": x.primary_state,
            "primary_district": x.primary_district, "primary_locality": x.primary_locality,
            "current_state": x.current_state, "current_district": x.current_district,
            "current_locality": x.current_locality, "current_latitude": x.current_latitude,
            "current_longitude": x.current_longitude, "preferred_languages": x.preferred_languages}


@router.get("")
def list_profiles(account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    rows = db.scalars(select(Profile).where(Profile.account_id == account.id).order_by(Profile.id)).all()
    return [as_dict(x) for x in rows]


@router.post("")
def create_profile(data: ProfileCreate, account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    row = Profile(account_id=account.id, **data.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return as_dict(row)


@router.get("/{profile_id}")
def get_profile(profile_id: int, account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    return as_dict(owned(db, account, profile_id))


@router.get("/{profile_id}/medical-history")
def list_history(profile_id: int, account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    profile = owned(db, account, profile_id)
    return [{"id": h.id, "disease_name": h.disease_name, "diagnosis_year": h.diagnosis_year,
             "current_status": h.current_status, "doctor_confirmed": h.doctor_confirmed, "notes": h.notes}
            for h in profile.histories]


@router.post("/{profile_id}/medical-history")
def add_history(profile_id: int, data: MedicalHistoryCreate, account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    profile = owned(db, account, profile_id)
    row = MedicalHistory(profile_id=profile.id, **data.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "status": "SAVED"}
