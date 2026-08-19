from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import CaseReport, Role
from ..schemas import CaseCreate

router = APIRouter(prefix="/cases", tags=["Case Surveillance"])
OFFICIAL_ROLES = (Role.DOCTOR.value, Role.GOVERNMENT.value)


@router.post("")
def create_case(data: CaseCreate, account=Depends(require_roles(*OFFICIAL_ROLES)), db: Session = Depends(get_db)):
    row = CaseReport(reporter_account_id=account.id, **data.model_dump(), status="DEMO_OFFICIAL_ENTRY")
    db.add(row); db.commit(); db.refresh(row)
    return {"case_id": row.id, "status": row.status}


@router.get("")
def list_cases(account=Depends(require_roles(*OFFICIAL_ROLES)), db: Session = Depends(get_db)):
    rows = db.scalars(select(CaseReport).order_by(CaseReport.case_date.desc(), CaseReport.id.desc()).limit(200)).all()
    return [{"id": x.id, "disease": x.disease, "case_date": x.case_date, "state": x.state,
             "district": x.district, "confirmed_cases": x.confirmed_cases,
             "suspected_cases": x.suspected_cases, "status": x.status} for x in rows]
