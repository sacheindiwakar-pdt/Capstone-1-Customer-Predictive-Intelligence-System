from pydantic import BaseModel
from typing import List


class ActivityPoint(BaseModel):
    timestamp: str
    total_sms: float
    total_calls: float
    internet_activity: float
    total_activity: float


class GridSummary(BaseModel):
    total_24h_activity: float
    avg_hourly_activity: float
    peak_activity: float


class GridActivityResponse(BaseModel):
    grid_id: int
    as_of: str
    hours_returned: int
    summary: GridSummary
    activity_series: List[ActivityPoint]