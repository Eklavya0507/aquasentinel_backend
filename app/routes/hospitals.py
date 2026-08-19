from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Hospital

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.get("")
def list_hospitals(state: str | None = None, district: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Hospital)
    if state: stmt = stmt.where(Hospital.state == state)
    if district: stmt = stmt.where(Hospital.district == district)
    rows = db.scalars(stmt.order_by(Hospital.name)).all()
    return [{"id": x.id, "name": x.name, "state": x.state, "district": x.district,
             "locality": x.locality, "phone": x.phone, "latitude": x.latitude,
             "longitude": x.longitude, "emergency_available": x.emergency_available,
             "is_demo": x.is_demo} for x in rows]
