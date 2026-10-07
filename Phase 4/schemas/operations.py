from pydantic import BaseModel
from typing import List


class PipelineMetrics(BaseModel):
    rows_published: int
    grid_count: int
    time_count: int


class PipelineStatusResponse(BaseModel):
    healthy: bool
    reasons: List[str]

    run_timestamp: str
    status: str
    message: str

    as_of: str

    pipeline_metrics: PipelineMetrics


class GridLocationResponse(BaseModel):
    grid_id: int
    centroid_latitude: float
    centroid_longitude: float
    polygon_reference: str


class NeighboursResponse(BaseModel):
    grid_id: int
    neighbours: List[int]