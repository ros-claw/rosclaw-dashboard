from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Float, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import settings

_engine_kwargs = {}
if settings.database_url.startswith("sqlite"):
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

engine = create_engine(settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Robot(Base):
    __tablename__ = "robots"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    eurdf_version = Column(String, default="v0.1.0")
    status = Column(String, default="offline")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(String, primary_key=True, index=True)
    robot_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    frame_id = Column(String)
    health_status = Column(String, default="unknown")
    created_at = Column(DateTime, default=datetime.utcnow)


class Actuator(Base):
    __tablename__ = "actuators"

    id = Column(String, primary_key=True, index=True)
    robot_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    command_topic = Column(String)
    health_status = Column(String, default="unknown")
    created_at = Column(DateTime, default=datetime.utcnow)


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, index=True)
    robot_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    skill_type = Column(String, nullable=False)
    status = Column(String, default="unknown")
    approval_required = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Mission(Base):
    __tablename__ = "missions"

    id = Column(String, primary_key=True, index=True)
    robot_id = Column(String, nullable=False, index=True)
    agent_id = Column(String)
    title = Column(String, nullable=False)
    status = Column(String, default="pending")
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class SkillRun(Base):
    __tablename__ = "skill_runs"

    id = Column(String, primary_key=True, index=True)
    mission_id = Column(String, nullable=False, index=True)
    skill_name = Column(String, nullable=False)
    status = Column(String, default="pending")
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    mcap_segment_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String, primary_key=True, index=True)
    mission_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload_json = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class MCAPFile(Base):
    __tablename__ = "mcap_files"

    id = Column(String, primary_key=True, index=True)
    robot_id = Column(String, nullable=False, index=True)
    path = Column(String, nullable=False)
    start_time = Column(Float)
    end_time = Column(Float)
    duration_sec = Column(Float)
    size_bytes = Column(Integer)
    imported_at = Column(DateTime, default=datetime.utcnow)


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(String, primary_key=True, index=True)
    robot_id = Column(String, nullable=False, index=True)
    memory_type = Column(String, nullable=False)
    content_json = Column(Text, nullable=False)
    embedding_vector = Column(Text)
    source_skill = Column(String)
    source_mission = Column(String)
    confidence = Column(Float, default=1.0)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SafetyAudit(Base):
    __tablename__ = "safety_audits"

    id = Column(String, primary_key=True, index=True)
    robot_id = Column(String, nullable=False, index=True)
    audit_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    findings_json = Column(Text)
    conducted_at = Column(DateTime, default=datetime.utcnow)
    next_due_at = Column(DateTime)


class SafetyRule(Base):
    __tablename__ = "safety_rules"

    id = Column(String, primary_key=True, index=True)
    robot_id = Column(String, nullable=False, index=True)
    rule_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    parameters_json = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TraceRun(Base):
    __tablename__ = "trace_runs"

    run_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="unknown")
    robot_id = Column(String, index=True)
    task = Column(String)
    started_at = Column(Float)
    ended_at = Column(Float)
    duration_sec = Column(Float)
    event_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    tracks = Column(Text, default="")
    manifest_json = Column(Text)
    indexed_at = Column(DateTime, default=datetime.utcnow)


class ReplaySession(Base):
    __tablename__ = "replay_sessions"

    session_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, nullable=False, index=True)
    state_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExportJob(Base):
    __tablename__ = "export_jobs"

    job_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, nullable=False, index=True)
    format = Column(String, nullable=False)
    state = Column(String, default="queued")
    progress = Column(Float, default=0.0)
    result_path = Column(String)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
