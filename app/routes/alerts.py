from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import Account, AlertSeverity, RegionalAlert, Role
from ..schemas import AlertCreate

router = APIRouter(prefix="/alerts", tags=["Regional Alerts"])


@router.get("")
def list_alerts(
    state: str | None = None,
    district: str | None = None,
    severity: AlertSeverity | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(RegionalAlert).where(RegionalAlert.status == "ACTIVE")
    if state:
        stmt = stmt.where(RegionalAlert.state == state)
    if district:
        stmt = stmt.where(RegionalAlert.district == district)
    if severity:
        stmt = stmt.where(RegionalAlert.severity == severity)

    rows = db.scalars(stmt.order_by(RegionalAlert.created_at.desc())).all()
    return [
        {
            "id": x.id,
            "state": x.state,
            "district": x.district,
            "disease": x.disease,
            "severity": x.severity.value,
            "title": x.title,
            "reason": x.reason,
            "current_cases": x.current_cases,
            "expected_min": x.expected_min,
            "expected_max": x.expected_max,
            "created_at": x.created_at,
        }
        for x in rows
    ]


@router.post("")
def create_alert(
    data: AlertCreate,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    row = RegionalAlert(
        state=data.state,
        district=data.district,
        disease=data.disease,
        severity=AlertSeverity(data.severity),
        title=data.title,
        reason=data.reason,
        current_cases=data.current_cases,
        expected_min=data.expected_min,
        expected_max=data.expected_max,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "message": "Alert created"}
