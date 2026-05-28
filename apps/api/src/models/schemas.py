from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class RobotBase(BaseModel):
    id: str
    name: str
    model: str
    eurdf_version: str = "v0.1.0"
    status: str = "offline"


class RobotCreate(RobotBase):
    pass


class RobotResponse(RobotBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SensorBase(BaseModel):
    id: str
    robot_id: str
    name: str
    type: str
    frame_id: str | None = None
    health_status: str = "unknown"


class SensorResponse(SensorBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime | None = None


class ActuatorBase(BaseModel):
    id: str
    robot_id: str
    name: str
    type: str
    command_topic: str | None = None
    health_status: str = "unknown"


class ActuatorResponse(ActuatorBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime | None = None


class SkillBase(BaseModel):
    id: str
    robot_id: str
    name: str
    skill_type: str
    status: str = "unknown"
    approval_required: bool = False
    description: str | None = None


class SkillResponse(SkillBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime | None = None


class MissionBase(BaseModel):
    id: str
    robot_id: str
    agent_id: str | None = None
    title: str
    status: str = "pending"


class MissionCreate(MissionBase):
    pass


class MissionResponse(MissionBase):
    model_config = ConfigDict(from_attributes=True)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime | None = None


class SkillRunBase(BaseModel):
    id: str
    mission_id: str
    skill_name: str
    status: str = "pending"
    mcap_segment_id: str | None = None


class SkillRunResponse(SkillRunBase):
    model_config = ConfigDict(from_attributes=True)
    started_at: datetime | None = None
    ended_at: datetime | None = None


class AgentEventBase(BaseModel):
    id: str
    mission_id: str
    event_type: str
    payload_json: str | None = None


class AgentEventResponse(AgentEventBase):
    model_config = ConfigDict(from_attributes=True)
    timestamp: datetime | None = None


class MCAPFileBase(BaseModel):
    id: str
    robot_id: str
    path: str
    start_time: float | None = None
    end_time: float | None = None
    duration_sec: float | None = None
    size_bytes: int | None = None


class MCAPFileResponse(MCAPFileBase):
    model_config = ConfigDict(from_attributes=True)
    imported_at: datetime | None = None


class EmbodimentResponse(BaseModel):
    robot: RobotResponse
    sensors: list[SensorResponse]
    actuators: list[ActuatorResponse]
    skills: list[SkillResponse]


class ExecutionTraceResponse(BaseModel):
    mission: MissionResponse
    events: list[AgentEventResponse]
    skill_runs: list[SkillRunResponse]


class MemoryEntryBase(BaseModel):
    id: str
    robot_id: str
    memory_type: str
    content_json: str
    embedding_vector: str | None = None
    source_skill: str | None = None
    source_mission: str | None = None
    confidence: float = 1.0


class MemoryEntryResponse(MemoryEntryBase):
    model_config = ConfigDict(from_attributes=True)
    timestamp: datetime | None = None


class SafetyAuditBase(BaseModel):
    id: str
    robot_id: str
    audit_type: str
    status: str = "pending"
    findings_json: str | None = None
    next_due_at: datetime | None = None


class SafetyAuditResponse(SafetyAuditBase):
    model_config = ConfigDict(from_attributes=True)
    conducted_at: datetime | None = None


class SafetyRuleBase(BaseModel):
    id: str
    robot_id: str
    rule_name: str
    rule_type: str
    parameters_json: str
    active: bool = True


class SafetyRuleResponse(SafetyRuleBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    version: str


class RobotImportRequest(BaseModel):
    robot_id: str
    directory: str
