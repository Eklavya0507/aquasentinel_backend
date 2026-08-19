from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import CommunityReport, Role
from ..schemas import CommunityReportCreate, CommunityReportReview

router = APIRouter(prefix="/reports", tags=["Community Reports"])


@router.post("")
def submit_report(data: CommunityReportCreate, db: Session = Depends(get_db)):
    row = CommunityReport(**data.model_dump(), status="SUBMITTED")
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "report_id": row.id,
        "status": row.status,
        "message": "Community Signal — Unverified. Submitted for official review.",
    }


def report_dict(x: CommunityReport):
    return {
        "id": x.id,
        "concern_type": x.concern_type,
        "summary": x.summary,
        "description": x.description,
        "state": x.state,
        "district": x.district,
        "locality": x.locality,
        "urgency": x.urgency,
        "water_source": x.water_source,
        "people_affected": x.people_affected,
        "status": x.status,
        "review_notes": x.review_notes,
        "created_at": x.created_at,
        "reviewed_at": x.reviewed_at,
    }


@router.get("")
def list_reports(account=Depends(require_roles(Role.GOVERNMENT.value)), db: Session = Depends(get_db)):
    rows = db.scalars(select(CommunityReport).order_by(CommunityReport.created_at.desc()).limit(100)).all()
    return [report_dict(x) for x in rows]


@router.patch("/{report_id}/review")
def review_report(
    report_id: int,
    data: CommunityReportReview,
    account=Depends(require_roles(Role.GOVERNMENT.value)),
    db: Session = Depends(get_db),
):
    row = db.get(CommunityReport, report_id)
    if not row:
        raise HTTPException(status_code=404, detail="Community report not found")
    row.status = data.status
    row.review_notes = data.review_notes
    row.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return report_dict(row)
