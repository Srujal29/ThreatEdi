# =============================================================
# PYDANTIC SCHEMAS — Request/Response Models for FastAPI
# =============================================================
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --------------- RANKS ---------------
class RankOut(BaseModel):
    rank_id: int
    rank_name: str
    hierarchy_level: int

    class Config:
        from_attributes = True


# --------------- UNITS ---------------
class UnitOut(BaseModel):
    unit_id: int
    unit_name: str
    base_location: str
    is_active_deployment: bool

    class Config:
        from_attributes = True


# --------------- USERS ---------------
class UserCreate(BaseModel):
    full_name: str
    email: str
    service_number: str
    user_type: str = Field(default="Active", pattern="^(Active|Veteran|Family)$")
    rank_id: int
    unit_id: int


class UserOut(BaseModel):
    user_id: str
    full_name: str
    email: str
    service_number: str
    user_type: str
    rank_id: int
    unit_id: int
    rank: Optional[RankOut] = None
    unit: Optional[UnitOut] = None

    class Config:
        from_attributes = True


# --------------- INCIDENTS ---------------
class IncidentCreate(BaseModel):
    """What the army user submits — just their ID and the threat report text."""
    user_id: str
    report_text: str


class IncidentOut(BaseModel):
    incident_id: str
    user_id: str
    report_text: str
    ml_category: Optional[str] = None
    ml_confidence: Optional[float] = None
    risk_score: Optional[float] = None
    priority_level: Optional[str] = None
    status: str
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    """Full response after ML + Risk Engine processing."""
    incident: IncidentOut
    playbook: Optional[dict] = None
    risk_breakdown: Optional[dict] = None


# --------------- PLAYBOOKS ---------------
class PlaybookOut(BaseModel):
    category_id: int
    incident_category: str
    action_steps: list

    class Config:
        from_attributes = True
