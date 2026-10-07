from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    grid_id: int = Field(..., ge=1, le=10000)
    avg_activity: float
    activity_growth: float
    active_hours: int
    peak_ratio: float
    variability: float
    internet_share: float
    activity_vs_baseline: float
    baseline_gap: float
    feature_timestamp: str


class PredictionResponse(BaseModel):
    grid_id: int
    risk_score: float
    risk_level: str
    model_version: str
    explanation_note: str