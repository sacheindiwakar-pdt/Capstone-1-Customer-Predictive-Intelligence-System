from fastapi import APIRouter, HTTPException

from schemas.network_summary import NetworkSummaryResponse
from services.summary_service import get_network_summary

router = APIRouter()

@router.get(
    "/network/summary",
    response_model=NetworkSummaryResponse
)
def network_summary(as_of: str = None):

    try:
        return get_network_summary(as_of)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve network summary: {str(e)}"
        )
    