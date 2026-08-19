from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account
from ..models import Account, ModelAAssessment, ModelBRiskSnapshot, Profile
from ..schemas import ModelAPredictIn, ModelBPredictIn
from ..services import (
    model_a_runtime,
    model_b_runtime,
    profile_context,
)

router = APIRouter(prefix="/ai", tags=["AI"])


def owned_profile(db: Session, account: Account, profile_id: int) -> Profile:
    profile = db.scalar(
        select(Profile).where(
            Profile.id == profile_id,
            Profile.account_id == account.id,
        )
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/model-a/predict")
def model_a_predict(
    data: ModelAPredictIn,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    profile = owned_profile(db, account, data.profile_id)

    inputs = {
        **profile_context(profile),
        **data.symptoms,
        **data.extra_inputs,
    }
    result = model_a_runtime.predict(inputs)

    row = ModelAAssessment(
        profile_id=profile.id,
        symptoms=data.symptoms,
        inputs=inputs,
        predicted_label=result["predicted_label"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        model_version="configured-joblib-model",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "assessment_id": row.id,
        **result,
        "disclaimer": "AI-assisted assessment only; not a confirmed medical diagnosis.",
    }


@router.get("/model-a/history/{profile_id}")
def model_a_history(
    profile_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    owned_profile(db, account, profile_id)
    rows = db.scalars(
        select(ModelAAssessment)
        .where(ModelAAssessment.profile_id == profile_id)
        .order_by(ModelAAssessment.created_at.desc())
    ).all()
    return [
        {
            "id": x.id,
            "predicted_label": x.predicted_label,
            "confidence": x.confidence,
            "probabilities": x.probabilities,
            "created_at": x.created_at,
        }
        for x in rows
    ]


@router.post("/model-b/predict")
def model_b_predict(
    data: ModelBPredictIn,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    profile = owned_profile(db, account, data.profile_id)

    history = [
        {
            "disease": x.disease_name,
            "diagnosis_year": x.diagnosis_year,
            "status": x.current_status,
            "doctor_confirmed": x.doctor_confirmed,
        }
        for x in profile.histories
    ]

    inputs = {
        **profile_context(profile),
        "medical_history": history,
        **data.regional_inputs,
        **data.extra_inputs,
    }

    result = model_b_runtime.predict(inputs)

    risk_label = result["predicted_label"]
    score = result["confidence"]

    row = ModelBRiskSnapshot(
        profile_id=profile.id,
        risk_score=score,
        risk_level=risk_label,
        inputs=inputs,
        factors={"source": "configured model"},
        model_version="configured-joblib-model",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "snapshot_id": row.id,
        "risk_level": risk_label,
        "risk_score": score,
        "probabilities": result["probabilities"],
    }


@router.get("/model-b/latest/{profile_id}")
def model_b_latest(
    profile_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    owned_profile(db, account, profile_id)
    row = db.scalar(
        select(ModelBRiskSnapshot)
        .where(ModelBRiskSnapshot.profile_id == profile_id)
        .order_by(ModelBRiskSnapshot.created_at.desc())
    )
    if not row:
        return {"status": "NO_DATA"}
    return {
        "snapshot_id": row.id,
        "risk_level": row.risk_level,
        "risk_score": row.risk_score,
        "regional_level": row.regional_level,
        "factors": row.factors,
        "created_at": row.created_at,
    }
