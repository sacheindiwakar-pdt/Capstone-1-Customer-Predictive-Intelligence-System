from fastapi import APIRouter
from fastapi import HTTPException

from schemas.grid_activity import GridActivityResponse
from services.grid_service import get_grid_activity

router = APIRouter()


@router.get(
    "/network/grid/{grid_id}",
    response_model=GridActivityResponse
)
def network_grid(
    grid_id: int,
    date: str | None = None,
    hour: int | None = None,
    as_of: str | None = None
):
    try:

        return get_grid_activity(
            grid_id=grid_id,
            date=date,
            hour=hour,
            as_of=as_of
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve grid activity: {str(e)}"
        )