from fastapi import APIRouter
from fastapi import HTTPException

from schemas.operations import (
    PipelineStatusResponse,
    GridLocationResponse,
    NeighboursResponse
)

from services.operations_service import (
    get_pipeline_status,
    get_grid_location,
    get_neighbours
)

router = APIRouter()


@router.get(
    "/pipeline/status",
    response_model=PipelineStatusResponse
)
def pipeline_status():

    try:
        return get_pipeline_status()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get(
    "/network/grid/{grid_id}/location",
    response_model=GridLocationResponse
)
def grid_location(grid_id: int):

    try:
        return get_grid_location(grid_id)

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get(
    "/network/grid/{grid_id}/neighbours",
    response_model=NeighboursResponse
)
def grid_neighbours(
    grid_id: int,
    limit: int = 5
):

    try:
        return get_neighbours(
            grid_id,
            limit
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )