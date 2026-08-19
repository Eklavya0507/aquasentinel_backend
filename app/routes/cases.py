from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import Account, CaseReport, CaseStatus, Role, VerificationStatus
from ..schemas import CaseCreate

router = APIRouter(prefix="/cases", tags=["Verified Case Surveillance"])


@router.post("")
def submit_case(
    data: CaseCreate,
    account: Account = Depends(require_roles(Role.DOCTOR, Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    if account.role in {Role.DOCTOR, Role.GOVERNMENT} and account.status != VerificationStatus.APPROVED:
        raise HTTPException(status_code=403, detail="Account must be verified before submitting case data")

    row = CaseReport(
        **data.model_dump(),
        submitted_by_account_id=account.id,
        status=CaseStatus.PENDING,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "status": row.status.value}


@router.get("")
def list_cases(
    status: CaseStatus | None = None,
    state: str | None = None,
    district: str | None = None,
    account: Account = Depends(require_roles(Role.DOCTOR, Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    stmt = select(CaseReport)
    if status:
        stmt = stmt.where(CaseReport.status == status)
    if state:
        stmt = stmt.where(CaseReport.state == state)
    if district:
        stmt = stmt.where(CaseReport.district == district)
    rows = db.scalars(stmt.order_by(CaseReport.case_date.desc())).all()
    return [
        {
            "id": x.id,
            "disease": x.disease,
            "case_date": x.case_date,
            "state": x.state,
            "district": x.district,
            "confirmed_cases": x.confirmed_cases,
            "suspected_cases": x.suspected_cases,
            "status": x.status.value,
        }
        for x in rows
    ]


@router.patch("/{case_id}/doctor-verify")
def doctor_verify(
    case_id: int,
    account: Account = Depends(require_roles(Role.DOCTOR, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    row = db.get(CaseReport, case_id)
    if not row:
        raise HTTPException(status_code=404, detail="Case record not found")

    row.doctor_verified_by_account_id = account.id
    row.doctor_verified_at = datetime.utcnow()
    row.status = CaseStatus.DOCTOR_VERIFIED
    db.commit()
    return {"status": row.status.value}


@router.patch("/{case_id}/government-verify")
def government_verify(
    case_id: int,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    row = db.get(CaseReport, case_id)
    if not row:
        raise HTTPException(status_code=404, detail="Case record not found")
    if row.status not in {CaseStatus.DOCTOR_VERIFIED, CaseStatus.PENDING}:
        raise HTTPException(status_code=409, detail="Case is not eligible for verification")

    row.government_verified_by_account_id = account.id
    row.government_verified_at = datetime.utcnow()
    row.status = CaseStatus.FULLY_VERIFIED
    db.commit()
    return {"status": row.status.value}


@router.patch("/{case_id}/reject")
def reject_case(
    case_id: int,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    row = db.get(CaseReport, case_id)
    if not row:
        raise HTTPException(status_code=404, detail="Case record not found")
    row.status = CaseStatus.REJECTED
    db.commit()
    return {"status": row.status.value}
