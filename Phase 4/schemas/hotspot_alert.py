from pydantic import BaseModel
from typing import List, Optional


class RiskInfo(BaseModel):
    rule_score: Optional[float] = None
    ml_score: Optional[float] = None
    risk_level: Optional[str] = None


class HotspotItem(BaseModel):
    grid_id: int
    hourly_timestamp: str
    total_sms: float
    total_calls: float
    internet_activity: float
    total_activity: float
    status: str
    risk: RiskInfo


class HotspotResponse(BaseModel):
    as_of: str
    count: int
    hotspots: List[HotspotItem]


class AlertItem(BaseModel):
    grid_id: int
    hourly_timestamp: str
    alert_type: str
    severity: str
    current_activity: float
    baseline_activity: float
    reason: str
    risk: RiskInfo


class AlertResponse(BaseModel):
    as_of: str
    count: int
    alerts: List[AlertItem]