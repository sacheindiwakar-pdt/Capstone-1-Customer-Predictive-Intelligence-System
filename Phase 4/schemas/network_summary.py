from pydantic import BaseModel

class NetworkSummaryResponse(BaseModel):
    as_of: str
    total_activity: float
    active_grids: int
    peak_hour: int
    top_grid: int