# =============================================================
# DATABASE MODELS — SQLAlchemy ORM for Cyber Incident Portal
# =============================================================
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, create_engine, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///cyber_incidents.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----- 1. RANKS -----
class Rank(Base):
    __tablename__ = "ranks"

    rank_id = Column(Integer, primary_key=True, autoincrement=True)
    rank_name = Column(String(100), nullable=False, unique=True)
    hierarchy_level = Column(Integer, nullable=False)  # higher = more senior

    users = relationship("User", back_populates="rank")


# ----- 2. UNITS -----
class Unit(Base):
    __tablename__ = "units"

    unit_id = Column(Integer, primary_key=True, autoincrement=True)
    unit_name = Column(String(200), nullable=False)
    base_location = Column(String(200), nullable=False)
    is_active_deployment = Column(Boolean, default=False)

    users = relationship("User", back_populates="unit")


# ----- 3. USERS -----
class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    service_number = Column(String(50), nullable=False, unique=True)
    user_type = Column(String(20), nullable=False, default="Active")  # Active/Veteran/Family
    rank_id = Column(Integer, ForeignKey("ranks.rank_id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.unit_id"), nullable=False)

    rank = relationship("Rank", back_populates="users")
    unit = relationship("Unit", back_populates="users")
    incidents = relationship("Incident", back_populates="user")


# ----- 4. INCIDENTS -----
class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    report_text = Column(Text, nullable=False)
    ml_category = Column(String(100))
    ml_confidence = Column(Float)
    risk_score = Column(Float)
    priority_level = Column(String(20))  # Low / Medium / High / Critical
    status = Column(String(20), default="Pending")  # Pending / Investigating / Resolved
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="incidents")


# ----- 5. MITIGATION PLAYBOOKS -----
class MitigationPlaybook(Base):
    __tablename__ = "mitigation_playbooks"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    incident_category = Column(String(100), nullable=False, unique=True)
    action_steps = Column(JSON, nullable=False)  # list of SOP steps


# ----- CREATE ALL TABLES -----
def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
