from fastapi import APIRouter
from fastapi import HTTPException

from schemas.grid_features import (
    GridFeaturesResponse
)

from services.feature_service import (
    get_grid_features
)

router = APIRouter()


@router.get(
    "/network/grid/{grid_id}/features",
    response_model=GridFeaturesResponse
)
def network_grid_features(
    grid_id: int
):
    try:

        return get_grid_features(
            grid_id
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve features: {str(e)}"
        )