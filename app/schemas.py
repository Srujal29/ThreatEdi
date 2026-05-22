from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RankOut(BaseModel):
    rank_id: int
    rank_name: str
    hierarchy_level: int

    class Config:
        from_attributes = True

class UnitOut(BaseModel):
    unit_id: int
    unit_name: str
    base_location: str
    is_active_deployment: bool

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    full_name: str
    email: str
    service_number: str
    user_type: str = Field(default="Active", pattern="^(Active|Veteran|Family|Admin|CRT)$")
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

class UserInternalOut(UserOut):
    password_hash: str

class IncidentCreate(BaseModel):
    user_id: str
    report_text: str
    evidence_url: Optional[str] = None
    rank_id: Optional[int] = None
    unit_id: Optional[int] = None

class IncidentOut(BaseModel):
    incident_id: str
    user_id: str
    report_text: str
    ml_category: Optional[str] = None
    ml_confidence: Optional[float] = None
    risk_score: Optional[float] = None
    priority_level: Optional[str] = None
    evidence_analysis: Optional[str] = None
    inferred_threat_type: Optional[str] = None
    status: str
    timestamp: Optional[datetime] = None
    risk_breakdown: Optional[dict] = None

    class Config:
        from_attributes = True

class IncidentResponse(BaseModel):
    incident: IncidentOut
    playbook: Optional[dict] = None
    risk_breakdown: Optional[dict] = None

class PlaybookOut(BaseModel):
    category_id: int
    incident_category: str
    action_steps: list

    class Config:
        from_attributes = True

class PredictRequest(BaseModel):
    report_text: str
    rank_level: int = 1
    is_active_deployment: bool = False

class GenerateOTPRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp_code: str

class UpdatePasswordRequest(BaseModel):
    email: str
    new_password_hash: str
