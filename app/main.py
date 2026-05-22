import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", ".env"))

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.mitigation_engine import generate_dynamic_mitigation, analyze_evidence_with_gemini, fallback_classification

from app.database import get_db, init_db, Rank, Unit, User, Incident, MitigationPlaybook, OTP
from app.schemas import (
    RankOut, UnitOut, UserCreate, UserOut, UserInternalOut,
    IncidentCreate, IncidentOut, IncidentResponse,
    PlaybookOut, PredictRequest, GenerateOTPRequest, VerifyOTPRequest, UpdatePasswordRequest
)
from app.ml_model import predict, load_model, get_categories
from app.risk_engine import compute_risk_score
from app.seed_data import seed_all

app = FastAPI(
    title=" AI-Enabled Cyber Incident Portal",
    description="Army personnel cyber threat reporting with ML-powered classification and risk scoring.",
    version="1.0.0",
)

@app.on_event("startup")
def startup():
    init_db()
    seed_all()
    loaded = load_model()
    if not loaded:
        print("⚠️  No trained model found. Run `python run_training.py` first.")
        print("   The /api/incidents/report endpoint will fail until the model is trained.")

@app.get("/api/ranks/", response_model=List[RankOut], tags=["Ranks"])
def list_ranks(db: Session = Depends(get_db)):
    return db.query(Rank).order_by(Rank.hierarchy_level).all()

@app.get("/api/units/", response_model=List[UnitOut], tags=["Units"])
def list_units(db: Session = Depends(get_db)):
    return db.query(Unit).all()

@app.post("/api/users/", response_model=UserOut, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    rank = db.query(Rank).filter_by(rank_id=user.rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail=f"Rank ID {user.rank_id} not found")

    unit = db.query(Unit).filter_by(unit_id=user.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit ID {user.unit_id} not found")

    if db.query(User).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter_by(service_number=user.service_number).first():
        raise HTTPException(status_code=400, detail="Service number already registered")

    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/internal/users/email/{email}", response_model=UserInternalOut, tags=["Internal"])
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/internal/users", response_model=UserOut, tags=["Internal"])
def create_internal_user(user_data: dict, db: Session = Depends(get_db)):
    # Check if user already exists by email
    existing_user = db.query(User).filter_by(email=user_data.get("email")).first()
    if existing_user:
        for key, value in user_data.items():
            if hasattr(existing_user, key):
                setattr(existing_user, key, value)
        db.commit()
        db.refresh(existing_user)
        return existing_user

    # Check if service number is already registered
    sn = user_data.get("service_number")
    if sn:
        existing_sn = db.query(User).filter_by(service_number=sn).first()
        if existing_sn:
            raise HTTPException(status_code=400, detail="Service number already registered")

    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/users/{user_id}", response_model=UserOut, tags=["Users"])
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/users/", response_model=List[UserOut], tags=["Users"])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/api/incidents/report", response_model=IncidentResponse, tags=["Incidents"])
def report_incident(incident_req: IncidentCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(user_id=incident_req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Register first via POST /api/users/")

    rank_id = incident_req.rank_id if incident_req.rank_id is not None else user.rank_id
    unit_id = incident_req.unit_id if incident_req.unit_id is not None else user.unit_id

    rank = db.query(Rank).filter_by(rank_id=rank_id).first() if rank_id else None
    if not rank:
        rank = db.query(Rank).filter_by(rank_id=user.rank_id).first()
        
    unit = db.query(Unit).filter_by(unit_id=unit_id).first() if unit_id else None
    if not unit:
        unit = db.query(Unit).filter_by(unit_id=user.unit_id).first()

    try:
        ml_result = predict(incident_req.report_text)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    evidence_analysis = None
    if incident_req.evidence_url:
        evidence_analysis = analyze_evidence_with_gemini(incident_req.evidence_url)
        
    if ml_result["confidence"] < 0.70:
        groq_category = fallback_classification(incident_req.report_text)
        if groq_category != "Unknown":
            ml_result["category"] = groq_category
            ml_result["confidence"] = 0.99 

    risk_result = compute_risk_score(
        ml_category=ml_result["category"],
        ml_confidence=ml_result["confidence"],
        report_text=incident_req.report_text,
        rank_hierarchy_level=rank.hierarchy_level if rank else 1,
        is_active_deployment=unit.is_active_deployment if unit else False,
    )

    playbook_data = generate_dynamic_mitigation(
        category=ml_result["category"],
        risk_score=risk_result["risk_score"],
        priority_level=risk_result["priority_level"],
        ml_confidence=ml_result["confidence"],
        report_text=incident_req.report_text,
        rank_level=rank.hierarchy_level if rank else 1,
        is_active_deployment=unit.is_active_deployment if unit else False,
    )

    db_incident = Incident(
        user_id=user.user_id,
        report_text=incident_req.report_text,
        evidence_url=incident_req.evidence_url,
        ml_category=ml_result["category"],
        ml_confidence=ml_result["confidence"],
        risk_score=risk_result["risk_score"],
        priority_level=risk_result["priority_level"],
        evidence_analysis=evidence_analysis,
        inferred_threat_type=playbook_data.get("inferred_threat_type"),
        status="Pending",
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    return IncidentResponse(
        incident=IncidentOut.model_validate(db_incident),
        playbook=playbook_data,
        risk_breakdown={
            "ml_prediction": ml_result,
            "risk_details": risk_result,
            "reporter_context": {
                "rank": rank.rank_name if rank else "Unknown",
                "rank_level": rank.hierarchy_level if rank else 0,
                "unit": unit.unit_name if unit else "Unknown",
                "is_active_deployment": unit.is_active_deployment if unit else False,
            },
        },
    )

@app.post("/api/ml/predict", tags=["ML Pipeline"])
def predict_incident(req: PredictRequest):
    try:
        ml_result = predict(req.report_text)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    risk_result = compute_risk_score(
        ml_category=ml_result["category"],
        ml_confidence=ml_result["confidence"],
        report_text=req.report_text,
        rank_hierarchy_level=req.rank_level,
        is_active_deployment=req.is_active_deployment,
    )

    playbook_data = generate_dynamic_mitigation(
        category=ml_result["category"],
        risk_score=risk_result["risk_score"],
        priority_level=risk_result["priority_level"],
        ml_confidence=ml_result["confidence"],
        report_text=req.report_text,
        rank_level=req.rank_level,
        is_active_deployment=req.is_active_deployment,
    )

    return {
        "ml_prediction": ml_result,
        "risk_details": risk_result,
        "playbook": playbook_data,
    }

@app.get("/api/incidents/{incident_id}", response_model=IncidentOut, tags=["Incidents"])
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter_by(incident_id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Reconstruct/fetch reporter context to compute dynamic breakdown
    user = incident.user
    rank = user.rank if user else None
    unit = user.unit if user else None
    
    risk_result = compute_risk_score(
        ml_category=incident.ml_category or "benign",
        ml_confidence=incident.ml_confidence or 0.0,
        report_text=incident.report_text or "",
        rank_hierarchy_level=rank.hierarchy_level if rank else 1,
        is_active_deployment=unit.is_active_deployment if unit else False,
    )
    
    breakdown_data = {
        "ml_prediction": {
            "category": incident.ml_category,
            "confidence": incident.ml_confidence,
        },
        "risk_details": risk_result,
        "reporter_context": {
            "rank": rank.rank_name if rank else "Unknown",
            "rank_level": rank.hierarchy_level if rank else 0,
            "unit": unit.unit_name if unit else "Unknown",
            "is_active_deployment": unit.is_active_deployment if unit else False,
        },
    }
    
    out = IncidentOut.model_validate(incident)
    out.risk_breakdown = breakdown_data
    return out

@app.get("/api/incidents/", response_model=List[IncidentOut], tags=["Incidents"])
def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status: Pending/Investigating/Resolved"),
    priority: Optional[str] = Query(None, description="Filter by priority: Low/Medium/High/Critical"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if priority:
        query = query.filter(Incident.priority_level == priority)
    return query.order_by(Incident.timestamp.desc()).limit(limit).all()

@app.patch("/api/incidents/{incident_id}/status", response_model=IncidentOut, tags=["Incidents"])
def update_incident_status(
    incident_id: str,
    new_status: str = Query(..., description="New status: Pending/Investigating/Resolved"),
    db: Session = Depends(get_db),
):
    if new_status not in ("Pending", "Investigating", "Resolved"):
        raise HTTPException(status_code=400, detail="Invalid status")
    incident = db.query(Incident).filter_by(incident_id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = new_status
    db.commit()
    db.refresh(incident)
    return incident

@app.get("/api/playbooks/{category}", response_model=PlaybookOut, tags=["Playbooks"])
def get_playbook(category: str, db: Session = Depends(get_db)):
    playbook = db.query(MitigationPlaybook).filter(
        MitigationPlaybook.incident_category.ilike(category)
    ).first()
    if not playbook:
        raise HTTPException(status_code=404, detail=f"No playbook for category: {category}")
    return playbook

@app.get("/api/playbooks/", response_model=List[PlaybookOut], tags=["Playbooks"])
def list_playbooks(db: Session = Depends(get_db)):
    return db.query(MitigationPlaybook).all()

@app.get("/api/categories/", tags=["Utility"])
def list_ml_categories():
    cats = get_categories()
    if not cats:
        return {"message": "Model not loaded. Run training first.", "categories": []}
    return {"categories": cats, "count": len(cats)}

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "AI-Enabled Cyber Incident Portal",
        "version": "1.0.0",
    }

import random
from datetime import timedelta, datetime

@app.post("/api/internal/otps", tags=["Internal"])
def generate_otp(req: GenerateOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    new_otp = OTP(user_email=req.email, otp_code=otp_code, expires_at=expires_at)
    db.add(new_otp)
    db.commit()
    
    return {"otp_code": otp_code}

@app.post("/api/internal/otps/verify", tags=["Internal"])
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    otp = db.query(OTP).filter(OTP.user_email == req.email, OTP.otp_code == req.otp_code).order_by(OTP.id.desc()).first()
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")
        
    return {"message": "OTP verified successfully"}

@app.patch("/api/internal/users/password", tags=["Internal"])
def update_password(req: UpdatePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password_hash = req.new_password_hash
    db.commit()
    return {"message": "Password updated successfully"}
