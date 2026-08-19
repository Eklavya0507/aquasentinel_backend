from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, require_roles
from ..models import (
    Account,
    CommunityReport,
    CommunityReportStatus,
    Profile,
    Role,
)
from ..schemas import CommunityReportCreate, CommunityReportReview

router = APIRouter(prefix="/reports", tags=["Community Reports"])


@router.post("")
def submit_report(
    data: CommunityReportCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    if data.profile_id:
        profile = db.scalar(
            select(Profile).where(
                Profile.id == data.profile_id,
                Profile.account_id == account.id,
            )
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    row = CommunityReport(
        **data.model_dump(),
        reporter_account_id=account.id,
        status=CommunityReportStatus.SUBMITTED,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "report_id": row.id,
        "status": row.status.value,
        "message": "Community signal submitted for review",
    }


@router.get("")
def list_reports(
    status: CommunityReportStatus | None = None,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    stmt = select(CommunityReport)
    if status:
        stmt = stmt.where(CommunityReport.status == status)
    rows = db.scalars(stmt.order_by(CommunityReport.created_at.desc())).all()
    return [
        {
            "id": x.id,
            "concern_type": x.concern_type,
            "summary": x.summary,
            "state": x.state,
            "district": x.district,
            "urgency": x.urgency,
            "status": x.status.value,
            "created_at": x.created_at,
        }
        for x in rows
    ]


@router.patch("/{report_id}/review")
def review_report(
    report_id: int,
    data: CommunityReportReview,
    account: Account = Depends(require_roles(Role.GOVERNMENT, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    row = db.get(CommunityReport, report_id)
    if not row:
        raise HTTPException(status_code=404, detail="Community report not found")

    row.status = CommunityReportStatus(data.status)
    row.review_notes = data.review_notes
    row.reviewed_by_account_id = account.id
    row.reviewed_at = datetime.utcnow()
    db.commit()
    return {"status": row.status.value}
