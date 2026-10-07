from fastapi import APIRouter
from fastapi import HTTPException

from schemas.hotspot_alert import (
    HotspotResponse,
    AlertResponse
)

from services.hotspot_alert_service import (
    get_hotspots,
    get_alerts
)

router = APIRouter()


@router.get(
    "/network/hotspots",
    response_model=HotspotResponse
)
def network_hotspots(
    limit: int = 10,
    as_of: str | None = None
):
    try:

        return get_hotspots(
            limit=limit,
            as_of=as_of
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve hotspots: {str(e)}"
        )


@router.get(
    "/network/alerts",
    response_model=AlertResponse
)
def network_alerts(
    limit: int = 10,
    severity: str | None = None,
    as_of: str | None = None
):
    try:

        return get_alerts(
            limit=limit,
            severity=severity,
            as_of=as_of
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve alerts: {str(e)}"
        )