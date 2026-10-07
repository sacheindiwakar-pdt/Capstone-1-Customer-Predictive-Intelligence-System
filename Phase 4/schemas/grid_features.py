from pydantic import BaseModel


class FeatureValues(BaseModel):
    avg_activity: float
    activity_growth: float
    active_hours: int
    peak_ratio: float
    variability: float
    internet_share: float


class GridFeaturesResponse(BaseModel):
    grid_id: int
    feature_timestamp: str
    features: FeatureValues