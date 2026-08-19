from fastapi import APIRouter

from ..schemas import B1EnvironmentalInput
from ..services import predict_b1

router = APIRouter(prefix="/ai", tags=["AI / B1"])


@router.get("/status")
def status():
    return {"b1": "CONFIGURED", "model_a_symptom": "NOT_PROVIDED",
            "message": "Uploaded B1 model is environmental-risk prediction, not a symptom diagnosis model."}


@router.post("/environmental-risk/predict")
def environmental_predict(data: B1EnvironmentalInput):
    return predict_b1(data.model_dump())
