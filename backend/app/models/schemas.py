from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnalysisType(str, Enum):
    LOG = "log"
    CODE = "code"
    AUTO = "auto"


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000, description="User message")
    mode: Literal["attacker", "defender", "explain"] = Field(
        default="explain",
        description="Perspective mode for the response"
    )
    session_id: Optional[str] = Field(default=None, description="Optional session ID")


class ChatResponse(BaseModel):
    response: str
    context_used: bool
    sources: list[str] = []
    model: str
    session_id: Optional[str] = None


# ── Analyze ───────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000, description="Log lines or source code")
    type: AnalysisType = Field(default=AnalysisType.AUTO)


class ThreatDetail(BaseModel):
    threat_type: str
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    attacker_perspective: str
    defender_perspective: str
    mitigation_steps: list[str]
    real_world_commands: list[str] = []
    cve_references: list[str] = []
    owasp_category: Optional[str] = None


class AnalyzeResponse(BaseModel):
    input_type: str
    threats: list[ThreatDetail]
    overall_severity: SeverityLevel
    summary: str
    raw_llm_analysis: str


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    ollama_connected: bool
    vector_store_loaded: bool
