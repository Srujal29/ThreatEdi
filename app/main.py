from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.mitigation_engine import generate_dynamic_mitigation

from app.database import get_db, init_db, Rank, Unit, User, Incident, MitigationPlaybook
from app.schemas import (
    RankOut, UnitOut, UserCreate, UserOut,
    IncidentCreate, IncidentOut, IncidentResponse,
    PlaybookOut,
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

    rank = db.query(Rank).filter_by(rank_id=user.rank_id).first()
    unit = db.query(Unit).filter_by(unit_id=user.unit_id).first()

    try:
        ml_result = predict(incident_req.report_text)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    risk_result = compute_risk_score(
        ml_category=ml_result["category"],
        ml_confidence=ml_result["confidence"],
        report_text=incident_req.report_text,
        rank_hierarchy_level=rank.hierarchy_level if rank else 1,
        is_active_deployment=unit.is_active_deployment if unit else False,
    )

    db_incident = Incident(
        user_id=user.user_id,
        report_text=incident_req.report_text,
        ml_category=ml_result["category"],
        ml_confidence=ml_result["confidence"],
        risk_score=risk_result["risk_score"],
        priority_level=risk_result["priority_level"],
        status="Pending",
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    playbook_data = generate_dynamic_mitigation(
        category=ml_result["category"],
        risk_score=risk_result["risk_score"],
        priority_level=risk_result["priority_level"],
        ml_confidence=ml_result["confidence"],
        report_text=incident_req.report_text,
        rank_level=rank.hierarchy_level if rank else 1,
        is_active_deployment=unit.is_active_deployment if unit else False,
    )

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

@app.get("/api/incidents/{incident_id}", response_model=IncidentOut, tags=["Incidents"])
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter_by(incident_id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

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
