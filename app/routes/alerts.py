from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import surveillance_summary

router = APIRouter(prefix="/alerts", tags=["Alerts & B2"])


@router.get("/surveillance")
def surveillance(db: Session = Depends(get_db)):
    rows = surveillance_summary(db)
    return {"method": "7-day recent cases versus previous 4-week average",
            "disclaimer": "Prototype surveillance from registered doctor/government demo entries; production deployment should enforce official verification before alerting.",
            "alerts": rows}


@router.get("")
def alerts(db: Session = Depends(get_db)):
    return [x for x in surveillance_summary(db) if x["level"] != "NORMAL"]
