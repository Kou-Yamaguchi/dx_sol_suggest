from pydantic import BaseModel, Field

from .state import ConstraintCategory, SolutionComplexity


class IssueExtraction(BaseModel):
    department: str | None = None
    situation: str | None = None
    issues: list[str] = Field(default_factory=list)
    workload_raw: str | None = None
    workload_people: int | None = None
    workload_frequency: str | None = None
    workload_time_per_task: str | None = None
    has_explicit_issues: bool = False
    has_workload: bool = False


class RawConstraint(BaseModel):
    text: str
    category: ConstraintCategory = "other"
    budget_text: str | None = None
    duration_text: str | None = None
    flags: list[str] = Field(default_factory=list)


class ConstraintExtraction(BaseModel):
    constraints: list[RawConstraint] = Field(default_factory=list)
    has_constraints: bool = False


class AssumedIssues(BaseModel):
    issues: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    can_assume: bool = False


class SolutionPlan(BaseModel):
    title: str
    pattern_ids: list[str] = Field(default_factory=list)
    summary: str
    scope: str
    steps: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    duration_months: int | None = None
    technologies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    risk_mitigations: list[str] = Field(default_factory=list)
    uses_public_cloud_llm: bool = False
    uses_generative_ai: bool = False
    replaces_existing_system: bool = False
    human_in_the_loop: bool = True
    complexity: SolutionComplexity = "saas"


class QualitativeViolation(BaseModel):
    constraint: str
    reason: str
    fix_hint: str


class QualitativeConstraintCheck(BaseModel):
    violations: list[QualitativeViolation] = Field(default_factory=list)
    compliant: bool = True


class EffectPlan(BaseModel):
    kpis: list[str] = Field(default_factory=list)
    reduction_rate: float | None = Field(
        default=None, description="0.0-1.0 の削減率。定量化できない場合は null"
    )
    qualitative_effects: list[str] = Field(default_factory=list)


class CostPlanItem(BaseModel):
    name: str
    amount_jpy: int
    kind: str = "initial"


class CostPlan(BaseModel):
    items: list[CostPlanItem] = Field(default_factory=list)
    rationale: str = ""


class FinalSummary(BaseModel):
    markdown: str
