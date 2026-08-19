from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Account, DoctorProfile, Role

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("")
def list_doctors(specialization: str | None = None, db: Session = Depends(get_db)):
    stmt = select(DoctorProfile)
    if specialization:
        stmt = stmt.where(DoctorProfile.specialization.ilike(f"%{specialization}%"))
    rows = db.scalars(stmt).all()
    return [{"id": d.id, "name": d.account.full_name, "specialization": d.specialization,
             "qualification": d.qualification, "years_experience": d.years_experience,
             "languages": d.languages, "verification_status": d.account.status} for d in rows]
