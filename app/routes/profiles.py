import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_account
from ..models import Account, MedicalDocument, MedicalHistory, Profile
from ..schemas import MedicalHistoryCreate, ProfileCreate

router = APIRouter(prefix="/profiles", tags=["User Profiles"])
settings = get_settings()


def owned_profile(db: Session, account: Account, profile_id: int) -> Profile:
    profile = db.scalar(
        select(Profile).where(Profile.id == profile_id, Profile.account_id == account.id)
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("")
def list_profiles(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    profiles = db.scalars(select(Profile).where(Profile.account_id == account.id)).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "relationship": p.relationship,
            "date_of_birth": p.date_of_birth,
            "current_state": p.current_state,
            "current_district": p.current_district,
            "preferred_languages": p.preferred_languages,
        }
        for p in profiles
    ]


@router.post("")
def create_profile(
    data: ProfileCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    profile = Profile(account_id=account.id, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return {"id": profile.id, "message": "Profile created"}


@router.get("/{profile_id}")
def get_profile(
    profile_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    p = owned_profile(db, account, profile_id)
    return {
        "id": p.id,
        "name": p.name,
        "relationship": p.relationship,
        "date_of_birth": p.date_of_birth,
        "gender": p.gender,
        "caregiver_managed": p.caregiver_managed,
        "primary_residence": {
            "state": p.primary_state,
            "district": p.primary_district,
            "locality": p.primary_locality,
        },
        "current_residence": {
            "state": p.current_state,
            "district": p.current_district,
            "locality": p.current_locality,
            "latitude": p.current_latitude,
            "longitude": p.current_longitude,
        },
        "preferred_languages": p.preferred_languages,
    }


@router.post("/{profile_id}/medical-history")
def add_medical_history(
    profile_id: int,
    data: MedicalHistoryCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    owned_profile(db, account, profile_id)
    item = MedicalHistory(profile_id=profile_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "Medical history added"}


@router.get("/{profile_id}/medical-history")
def get_medical_history(
    profile_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    owned_profile(db, account, profile_id)
    items = db.scalars(
        select(MedicalHistory).where(MedicalHistory.profile_id == profile_id)
    ).all()
    return [
        {
            "id": x.id,
            "disease_name": x.disease_name,
            "diagnosis_year": x.diagnosis_year,
            "current_status": x.current_status,
            "doctor_confirmed": x.doctor_confirmed,
            "notes": x.notes,
        }
        for x in items
    ]


@router.post("/{profile_id}/documents")
def upload_medical_document(
    profile_id: int,
    document_type: str = Form(...),
    history_id: int | None = Form(default=None),
    file: UploadFile = File(...),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    owned_profile(db, account, profile_id)

    if history_id:
        history = db.scalar(
            select(MedicalHistory).where(
                MedicalHistory.id == history_id,
                MedicalHistory.profile_id == profile_id,
            )
        )
        if not history:
            raise HTTPException(status_code=404, detail="Medical history item not found")

    max_size = settings.MAX_UPLOAD_MB * 1024 * 1024
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > max_size:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB")

    safe_ext = Path(file.filename or "").suffix.lower()
    if safe_ext not in {".pdf", ".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=415, detail="Unsupported document format")

    upload_root = Path(settings.UPLOAD_DIR) / "medical" / str(account.id) / str(profile_id)
    upload_root.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{safe_ext}"
    stored_path = upload_root / stored_name

    with stored_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    doc = MedicalDocument(
        profile_id=profile_id,
        history_id=history_id,
        document_type=document_type,
        original_name=file.filename or stored_name,
        stored_path=str(stored_path),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "message": "Document uploaded", "original_name": doc.original_name}
