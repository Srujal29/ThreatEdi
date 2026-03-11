# =============================================================
# FASTAPI MAIN — Cyber Incident Portal Backend
# =============================================================
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db, init_db, Rank, Unit, User, Incident, MitigationPlaybook
from app.schemas import (
    RankOut, UnitOut, UserCreate, UserOut,
    IncidentCreate, IncidentOut, IncidentResponse,
    PlaybookOut,
)
from app.ml_model import predict, load_model, get_categories
from app.risk_engine import compute_risk_score
from app.seed_data import seed_all

# --- App Setup ---
app = FastAPI(
    title="🛡️ AI-Enabled Cyber Incident Portal",
    description="Army personnel cyber threat reporting with ML-powered classification and risk scoring.",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    """Initialize DB, seed data, and load ML model on startup."""
    init_db()
    seed_all()
    loaded = load_model()
    if not loaded:
        print("⚠️  No trained model found. Run `python run_training.py` first.")
        print("   The /api/incidents/report endpoint will fail until the model is trained.")


# =====================================================================
# RANK ENDPOINTS
# =====================================================================
@app.get("/api/ranks/", response_model=List[RankOut], tags=["Ranks"])
def list_ranks(db: Session = Depends(get_db)):
    """List all army ranks."""
    return db.query(Rank).order_by(Rank.hierarchy_level).all()


# =====================================================================
# UNIT ENDPOINTS
# =====================================================================
@app.get("/api/units/", response_model=List[UnitOut], tags=["Units"])
def list_units(db: Session = Depends(get_db)):
    """List all army units."""
    return db.query(Unit).all()


# =====================================================================
# USER ENDPOINTS
# =====================================================================
@app.post("/api/users/", response_model=UserOut, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new army user (Active/Veteran/Family)."""
    # Validate rank and unit exist
    rank = db.query(Rank).filter_by(rank_id=user.rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail=f"Rank ID {user.rank_id} not found")

    unit = db.query(Unit).filter_by(unit_id=user.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit ID {user.unit_id} not found")

    # Check for duplicate email/service_number
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
    """Get user details by ID."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users/", response_model=List[UserOut], tags=["Users"])
def list_users(db: Session = Depends(get_db)):
    """List all registered users."""
    return db.query(User).all()


# =====================================================================
# INCIDENT ENDPOINTS — The Core Feature
# =====================================================================
@app.post("/api/incidents/report", response_model=IncidentResponse, tags=["Incidents"])
def report_incident(incident_req: IncidentCreate, db: Session = Depends(get_db)):
    """
    🚨 MAIN ENDPOINT — Army personnel submits a threat report.

    Pipeline:
    1. Look up reporter's rank + unit from the database
    2. ML model classifies the threat type from report text
    3. Risk Engine computes risk score using ML output + rank + deployment context
    4. Incident saved to database with full classification
    5. Returns classification, risk score, and mitigation playbook
    """
    # 1. Validate user exists and fetch context
    user = db.query(User).filter_by(user_id=incident_req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Register first via POST /api/users/")

    rank = db.query(Rank).filter_by(rank_id=user.rank_id).first()
    unit = db.query(Unit).filter_by(unit_id=user.unit_id).first()

    # 2. ML Classification
    try:
        ml_result = predict(incident_req.report_text)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # 3. Risk Engine (context-aware scoring)
    risk_result = compute_risk_score(
        ml_category=ml_result["category"],
        ml_confidence=ml_result["confidence"],
        report_text=incident_req.report_text,
        rank_hierarchy_level=rank.hierarchy_level if rank else 1,
        is_active_deployment=unit.is_active_deployment if unit else False,
    )

    # 4. Save to database
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

    # 5. Fetch playbook (try exact match, then case-insensitive)
    playbook = db.query(MitigationPlaybook).filter_by(
        incident_category=ml_result["category"]
    ).first()
    if not playbook:
        # Try case-insensitive match
        playbook = db.query(MitigationPlaybook).filter(
            MitigationPlaybook.incident_category.ilike(ml_result["category"])
        ).first()

    playbook_data = None
    if playbook:
        playbook_data = {
            "category": playbook.incident_category,
            "action_steps": playbook.action_steps,
        }

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
    """Get details of a specific incident."""
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
    """List all incidents with optional filters."""
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
    """Update the status of an incident."""
    if new_status not in ("Pending", "Investigating", "Resolved"):
        raise HTTPException(status_code=400, detail="Invalid status")
    incident = db.query(Incident).filter_by(incident_id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = new_status
    db.commit()
    db.refresh(incident)
    return incident


# =====================================================================
# PLAYBOOK ENDPOINTS
# =====================================================================
@app.get("/api/playbooks/{category}", response_model=PlaybookOut, tags=["Playbooks"])
def get_playbook(category: str, db: Session = Depends(get_db)):
    """Get the mitigation playbook for a threat category."""
    playbook = db.query(MitigationPlaybook).filter(
        MitigationPlaybook.incident_category.ilike(category)
    ).first()
    if not playbook:
        raise HTTPException(status_code=404, detail=f"No playbook for category: {category}")
    return playbook


@app.get("/api/playbooks/", response_model=List[PlaybookOut], tags=["Playbooks"])
def list_playbooks(db: Session = Depends(get_db)):
    """List all available mitigation playbooks."""
    return db.query(MitigationPlaybook).all()


# =====================================================================
# UTILITY ENDPOINTS
# =====================================================================
@app.get("/api/categories/", tags=["Utility"])
def list_ml_categories():
    """List all threat categories the ML model can classify."""
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
