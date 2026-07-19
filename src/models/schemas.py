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
    labour = "labour"
    corporate = "corporate"
    civil = "civil"
    commercial = "commercial"
    tax = "tax"
    property = "property"
    investment = "investment"
    constitutional = "constitutional"
    criminal = "criminal"
    it_cyber = "it_cyber"
    other = "other"


class RiskLevel(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"


# === Citations (used by contract review and agent responses) ===

class Citation(BaseModel):
    law_title: str
    law_number: str
    article: Optional[str] = None
    clause: Optional[str] = None
    text: str
    effective_date: Optional[str] = None
    status: str = "active"


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


# === Usage ===

class UsageResponse(BaseModel):
    company_id: UUID
    period: str  # "2026-03"
    total_requests: int
    quota_limit: int
    quota_remaining: int
    total_tokens: int
    total_cost_usd: float
