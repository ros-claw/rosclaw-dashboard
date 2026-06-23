from datetime import datetime
from enum import Enum
from typing import Any, Literal

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


# ── Runtime Evidence Center schemas ─────────────────────────────────────────

ModuleMode = Literal[
    "real", "mock", "fixture", "rule_based", "unavailable", "degraded"
]


class ModuleStatus(BaseModel):
    name: str
    status: str  # healthy / degraded / unavailable
    mode: ModuleMode
    message: str | None = None
    endpoint: str | None = None
    last_updated: float | None = None
    evidence: dict[str, Any] | None = None


class LiveSessionCreate(BaseModel):
    robot_id: str | None = None
    task: str | None = None
    run_id: str | None = None
    config: dict[str, Any] | None = None


class LiveSessionResponse(BaseModel):
    session_id: str
    run_id: str | None = None
    status: str
    config: dict[str, Any] | None = None
    created_at: float | None = None
    closed_at: float | None = None
    offline_run_id: str | None = None


class LiveSessionListResponse(BaseModel):
    sessions: list[LiveSessionResponse]
    total: int


class RosclawEventEnvelope(BaseModel):
    """Unified envelope for runtime events emitted by ROSClaw modules.

    Dashboard adapters consume this envelope and normalize it into TraceEvent.
    """

    event_id: str
    trace_id: str | None = None
    run_id: str | None = None
    source: str
    type: str
    ts: float
    severity: str = "info"
    payload: dict[str, Any] | None = None
    schema_version: str = "1.0"


# ── Physical Trace Viewer schemas ───────────────────────────────────────────

TraceTrack = Literal[
    "task", "agent", "tool", "provider", "sandbox", "runtime", "robot",
    "critic", "memory", "auto", "failure",
]


class TraceEvent(BaseModel):
    id: str
    run_id: str
    ts: float
    t_rel: float
    source: str
    type: str
    track: TraceTrack
    severity: str = "info"
    title: str
    summary: str | None = None
    entity: str | None = None
    payload: dict[str, Any] | None = None
    links: list[str] | None = None
    tags: list[str] | None = None


class EventFilter(BaseModel):
    track: str | None = None
    severity: str | None = None
    type: str | None = None
    entity: str | None = None
    tag: str | None = None
    start_t_rel: float | None = None
    end_t_rel: float | None = None
    q: str | None = None


class RunSummary(BaseModel):
    run_id: str
    episode_id: str | None = None
    task_id: str | None = None
    trace_id: str | None = None
    status: str
    robot_id: str | None = None
    task: str | None = None
    started_at: float | None = None
    ended_at: float | None = None
    duration_sec: float | None = None
    event_count: int = 0
    failure_count: int = 0
    tracks: list[str] = []
    has_media: bool = False
    has_trajectory: bool = False
    has_curves: bool = False
    manifest_path: str | None = None
    agent_request: dict[str, Any] | None = None
    provider_trace: dict[str, Any] | None = None
    sandbox_result: dict[str, Any] | None = None
    runtime_action: dict[str, Any] | None = None
    critic_result: dict[str, Any] | None = None
    memory_write_result: dict[str, Any] | None = None
    artifact_uri: str | None = None


class RunDetail(RunSummary):
    manifest: dict[str, Any] | None = None


class RunListResponse(BaseModel):
    runs: list[RunSummary]
    total: int


class EventsResponse(BaseModel):
    run_id: str
    events: list[TraceEvent]
    total: int
    next_cursor: str | None = None


class FailureSummary(BaseModel):
    id: str
    t_rel: float
    title: str
    summary: str | None = None
    severity: str
    track: str


class FailuresResponse(BaseModel):
    run_id: str
    failures: list[FailureSummary]


class ReplayManifestMedia(BaseModel):
    kind: str
    path: str
    name: str | None = None
    url: str
    mime_type: str | None = None
    start_t_rel: float | None = None
    end_t_rel: float | None = None


class ReplayManifestCurve(BaseModel):
    name: str
    url: str
    sample_count: int | None = None
    start_t_rel: float | None = None
    end_t_rel: float | None = None


class ReplayManifestTrajectory(BaseModel):
    url: str
    sample_count: int | None = None
    start_t_rel: float | None = None
    end_t_rel: float | None = None


class ReplayManifest(BaseModel):
    run_id: str
    duration_sec: float
    media: list[ReplayManifestMedia]
    curves: list[ReplayManifestCurve]
    trajectory: ReplayManifestTrajectory | None = None
    sandbox_states: list[dict[str, Any]] | None = None
    tracks: list[str] = []


# ── Evidence graph schemas ──────────────────────────────────────────────────

class EvidenceNode(BaseModel):
    id: str
    type: str
    track: str
    label: str
    t_rel: float
    severity: str = "info"
    payload: dict[str, Any] | None = None


class EvidenceEdge(BaseModel):
    source: str
    target: str
    relation: str


class EvidenceGraph(BaseModel):
    run_id: str
    focus_event_id: str | None = None
    nodes: list[EvidenceNode]
    edges: list[EvidenceEdge]


class SandboxDecision(BaseModel):
    event_id: str
    t_rel: float
    decision: str
    reason: str | None = None
    risk_score: float | None = None
    entity: str | None = None
    payload: dict[str, Any] | None = None


class MemoryEvent(BaseModel):
    event_id: str
    t_rel: float
    memory_type: str
    entity: str | None = None
    summary: str | None = None
    payload: dict[str, Any] | None = None


class ProviderRouteTrace(BaseModel):
    event_id: str
    t_rel: float
    provider: str | None = None
    latency_ms: float | None = None
    decision: str | None = None
    payload: dict[str, Any] | None = None


class HowRecovery(BaseModel):
    event_id: str
    t_rel: float
    recovery_type: str
    suggestion: str | None = None
    payload: dict[str, Any] | None = None


class AcceptanceVerdict(str, Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"


class AcceptanceReportSection(BaseModel):
    title: str
    status: str  # pass | partial | fail | info
    findings: list[str]
    evidence: dict[str, Any] | None = None


class AcceptanceReportArtifact(BaseModel):
    name: str
    path: str
    mime_type: str


class AcceptanceReport(BaseModel):
    run_id: str
    generated_at: float
    verdict: AcceptanceVerdict
    summary: str
    sections: list[AcceptanceReportSection]
    artifacts: list[AcceptanceReportArtifact]


class AcceptanceReportResponse(BaseModel):
    report: AcceptanceReport
    download_url: str | None = None


class ExportJobCreate(BaseModel):
    run_id: str
    format: str  # rlds, lerobot, failure_case, skill_candidate
    params: dict[str, Any] | None = None


class ExportJobStatus(BaseModel):
    job_id: str
    run_id: str
    format: str
    state: str  # queued, running, validating, packaging, completed, failed
    progress: float = 0.0
    result_url: str | None = None
    error: str | None = None
    created_at: float
    updated_at: float


class ExportJobListResponse(BaseModel):
    jobs: list[ExportJobStatus]
    total: int
