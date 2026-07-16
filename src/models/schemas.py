"""Pydantic schemas for API requests/responses."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# === Enums ===

class PlanType(str, Enum):
    trial = "trial"
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class AgentType(str, Enum):
    qa = "qa"
    review = "review"
    compliance = "compliance"
    draft = "draft"
    research = "research"
    general = "general"


class LegalDomain(str, Enum):
    lao_dong = "lao_dong"
    doanh_nghiep = "doanh_nghiep"
    dan_su = "dan_su"
    thuong_mai = "thuong_mai"
    thue = "thue"
    dat_dai = "dat_dai"
    dau_tu = "dau_tu"
    bhxh = "bhxh"
    atvs_ld = "atvs_ld"
    so_huu_tri_tue = "so_huu_tri_tue"
    other = "other"


class RiskLevel(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"


# === Legal Q&A ===

class LegalQuestionRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000)
    context: Optional[dict] = None
    domains: Optional[list[LegalDomain]] = None
    include_citations: bool = True
    include_related: bool = True
    language: str = "vi"


class Citation(BaseModel):
    law_title: str
    law_number: str
    article: Optional[str] = None
    clause: Optional[str] = None
    text: str
    effective_date: Optional[str] = None
    status: str = "active"


class LegalAnswerResponse(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)
    citations: list[Citation] = []
    related_topics: list[str] = []
    disclaimer: str = "This advice is for reference purposes only. Please consult a qualified advocate for specific legal matters."
    usage: dict = {}


# === Contract Review ===

class ContractReviewRequest(BaseModel):
    contract_type: Optional[str] = None  # auto-detect if None
    review_depth: str = "standard"  # quick | standard | comprehensive
    focus_areas: Optional[list[str]] = None


class ContractIssue(BaseModel):
    severity: RiskLevel
    clause: str
    issue: str
    law_reference: Optional[str] = None
    recommendation: str


class ContractReviewResponse(BaseModel):
    job_id: str
    status: str  # processing | completed | error
    overall_risk: Optional[RiskLevel] = None
    score: Optional[int] = None  # 0-100
    summary: Optional[str] = None
    issues: list[ContractIssue] = []
    missing_clauses: list[str] = []
    compliance_status: dict = {}


# === Law Search ===

class LawSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    domains: Optional[list[LegalDomain]] = None
    law_type: Optional[str] = None
    status: Optional[str] = "active"
    limit: int = Field(default=10, ge=1, le=50)


class LawChunkResult(BaseModel):
    law_title: str
    law_number: str
    article: Optional[str] = None
    clause: Optional[str] = None
    content: str
    relevance_score: float
    status: str


class LawSearchResponse(BaseModel):
    results: list[LawChunkResult]
    total: int
    query: str


# === Chat ===

class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[UUID] = None  # create new if None
    agent_type: AgentType = AgentType.qa


class ChatMessageResponse(BaseModel):
    session_id: UUID
    message_id: UUID
    role: str = "assistant"
    content: str
    citations: list[Citation] = []
    confidence: Optional[float] = None


# === Usage ===

class UsageResponse(BaseModel):
    company_id: UUID
    period: str  # "2026-03"
    total_requests: int
    quota_limit: int
    quota_remaining: int
    total_tokens: int
    total_cost_usd: float
