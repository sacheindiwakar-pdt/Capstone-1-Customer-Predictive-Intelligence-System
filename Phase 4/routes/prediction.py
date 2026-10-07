from fastapi import APIRouter
from fastapi import HTTPException

from schemas.prediction import (
    PredictionRequest,
    PredictionResponse
)

from services.prediction_service import (
    predict_risk
)

router = APIRouter()


@router.post(
    "/network/predict-risk",
    response_model=PredictionResponse
)
def network_predict_risk(
    request: PredictionRequest
):
    try:

        return predict_risk(request)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )