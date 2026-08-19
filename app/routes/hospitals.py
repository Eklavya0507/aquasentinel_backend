from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, require_roles
from ..models import (
    Account,
    Hospital,
    HospitalHour,
    HospitalScheduleException,
    HospitalSpecialist,
    Role,
)
from ..schemas import (
    HospitalCreate,
    HospitalExceptionIn,
    HospitalHourIn,
    HospitalSpecialistIn,
)
from ..services import hospital_open_now

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.get("")
def list_hospitals(
    state: str | None = None,
    district: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Hospital).where(Hospital.is_active.is_(True))
    if state:
        stmt = stmt.where(Hospital.state == state)
    if district:
        stmt = stmt.where(Hospital.district == district)
    hospitals = db.scalars(stmt).all()
    return [
        {
            "id": h.id,
            "name": h.name,
            "type": h.hospital_type,
            "state": h.state,
            "district": h.district,
            "locality": h.locality,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "emergency_available": h.emergency_available,
            "open_now": hospital_open_now(db, h),
        }
        for h in hospitals
    ]


@router.get("/{hospital_id}")
def get_hospital(hospital_id: int, db: Session = Depends(get_db)):
    h = db.get(Hospital, hospital_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return {
        "id": h.id,
        "name": h.name,
        "type": h.hospital_type,
        "address": h.address,
        "state": h.state,
        "district": h.district,
        "locality": h.locality,
        "latitude": h.latitude,
        "longitude": h.longitude,
        "phone": h.phone,
        "email": h.email,
        "emergency_available": h.emergency_available,
        "open_now": hospital_open_now(db, h),
        "hours": [
            {
                "day_of_week": x.day_of_week,
                "open_time": x.open_time,
                "close_time": x.close_time,
                "is_closed": x.is_closed,
            }
            for x in h.hours
        ],
        "specialists": [
            {
                "specialization": x.specialization,
                "day_of_week": x.day_of_week,
                "start_time": x.start_time,
                "end_time": x.end_time,
            }
            for x in h.specialists
        ],
    }


@router.post("")
def create_hospital(
    data: HospitalCreate,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    h = Hospital(**data.model_dump())
    db.add(h)
    db.commit()
    db.refresh(h)
    return {"id": h.id, "message": "Hospital created"}


@router.put("/{hospital_id}")
def update_hospital(
    hospital_id: int,
    data: HospitalCreate,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    h = db.get(Hospital, hospital_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")
    for key, value in data.model_dump().items():
        setattr(h, key, value)
    db.commit()
    return {"message": "Hospital updated"}


@router.post("/{hospital_id}/hours")
def set_hours(
    hospital_id: int,
    data: HospitalHourIn,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    if not db.get(Hospital, hospital_id):
        raise HTTPException(status_code=404, detail="Hospital not found")

    row = db.scalar(
        select(HospitalHour).where(
            HospitalHour.hospital_id == hospital_id,
            HospitalHour.day_of_week == data.day_of_week,
        )
    )
    if row:
        for k, v in data.model_dump().items():
            setattr(row, k, v)
    else:
        row = HospitalHour(hospital_id=hospital_id, **data.model_dump())
        db.add(row)
    db.commit()
    return {"message": "Hospital hours saved"}


@router.post("/{hospital_id}/exceptions")
def add_exception(
    hospital_id: int,
    data: HospitalExceptionIn,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    if not db.get(Hospital, hospital_id):
        raise HTTPException(status_code=404, detail="Hospital not found")
    row = HospitalScheduleException(hospital_id=hospital_id, **data.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id, "message": "Schedule exception added"}


@router.post("/{hospital_id}/specialists")
def add_specialist(
    hospital_id: int,
    data: HospitalSpecialistIn,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    if not db.get(Hospital, hospital_id):
        raise HTTPException(status_code=404, detail="Hospital not found")
    row = HospitalSpecialist(hospital_id=hospital_id, **data.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id, "message": "Specialist availability added"}
