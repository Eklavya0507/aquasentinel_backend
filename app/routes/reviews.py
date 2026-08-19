from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account
from ..models import Account, DoctorProfile, DoctorReview, ReviewStatus
from ..schemas import DoctorReviewCreate

router = APIRouter(prefix="/reviews", tags=["Doctor Reviews"])


@router.post("/doctors/{doctor_id}")
def create_review(
    doctor_id: int,
    data: DoctorReviewCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    if not db.get(DoctorProfile, doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found")

    existing = db.scalar(
        select(DoctorReview).where(
            DoctorReview.doctor_id == doctor_id,
            DoctorReview.reviewer_account_id == account.id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="You already reviewed this doctor")

    review = DoctorReview(
        doctor_id=doctor_id,
        reviewer_account_id=account.id,
        **data.model_dump(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {"id": review.id, "message": "Review submitted"}


@router.get("/doctors/{doctor_id}")
def doctor_reviews(doctor_id: int, db: Session = Depends(get_db)):
    reviews = db.scalars(
        select(DoctorReview).where(
            DoctorReview.doctor_id == doctor_id,
            DoctorReview.status == ReviewStatus.VISIBLE,
        )
    ).all()

    avg = db.scalar(
        select(func.avg(DoctorReview.overall_rating)).where(
            DoctorReview.doctor_id == doctor_id,
            DoctorReview.status == ReviewStatus.VISIBLE,
        )
    )
    return {
        "average_rating": round(float(avg), 2) if avg is not None else None,
        "count": len(reviews),
        "reviews": [
            {
                "id": r.id,
                "overall_rating": r.overall_rating,
                "communication_rating": r.communication_rating,
                "language_rating": r.language_rating,
                "professional_rating": r.professional_rating,
                "availability_accurate": r.availability_accurate,
                "preferred_language_met": r.preferred_language_met,
                "language_used": r.language_used,
                "comment": r.comment,
                "created_at": r.created_at,
            }
            for r in reviews
        ],
    }
