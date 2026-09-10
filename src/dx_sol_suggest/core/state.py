from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field

ConstraintCategory = Literal[
    "budget",
    "timeline",
    "security",
    "existing_system",
    "personnel",
    "accuracy",
    "other",
]
BudgetKind = Literal["initial", "annual", "monthly", "none"]
ItemSource = Literal["user", "assumed"]
SolutionComplexity = Literal["rules", "rpa", "saas", "ml", "custom"]


class Issue(BaseModel):
    text: str
    is_assumed: bool = False
    source: ItemSource = "user"


class Constraint(BaseModel):
    text: str
    category: ConstraintCategory = "other"
    is_assumed: bool = False
    source: ItemSource = "user"
    budget_jpy: int | None = None
    budget_kind: BudgetKind | None = None
    duration_months: int | None = None
    flags: list[str] = Field(default_factory=list)


class Workload(BaseModel):
    people: int | None = None
    frequency_text: str | None = None
    time_per_task_text: str | None = None
    tasks_per_year: float | None = None
    minutes_per_task: float | None = None
    annual_hours: float | None = None
    raw_text: str | None = None
    is_assumed: bool = False


class Solution(BaseModel):
    title: str
    pattern_ids: list[str] = Field(default_factory=list)
    summary: str = ""
    scope: str = ""
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


class ConstraintViolation(BaseModel):
    constraint: str
    reason: str
    fix_hint: str


class CostItem(BaseModel):
    name: str
    amount_jpy: int
    kind: Literal["initial", "annual"] = "initial"


class CostEstimate(BaseModel):
    items: list[CostItem] = Field(default_factory=list)
    initial_total_jpy: int = 0
    annual_total_jpy: int = 0


class EffectEstimate(BaseModel):
    kpis: list[str] = Field(default_factory=list)
    reduction_rate: float | None = None
    annual_hours_saved: float | None = None
    hourly_wage_jpy: int | None = None
    annual_saving_jpy: int | None = None
    qualitative_effects: list[str] = Field(default_factory=list)
    can_quantify: bool = False


class RoiEstimate(BaseModel):
    can_calculate: bool = False
    roi: float | None = None
    payback_months: float | None = None
    reason_if_unavailable: str | None = None


class BudgetInfo(BaseModel):
    initial_cap_jpy: int | None = None
    annual_cap_jpy: int | None = None
    raw_text: str | None = None
    is_unknown: bool = True


class AgentState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)
    department: str | None = None
    situation: str | None = None
    issues: list[Issue] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    workload: Workload | None = None
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    solution: Solution | None = None
    constraint_violations: list[ConstraintViolation] = Field(default_factory=list)
    retry_count: int = 0
    budget_retry_count: int = 0
    max_retries: int = 2
    effect: EffectEstimate | None = None
    cost: CostEstimate | None = None
    budget: BudgetInfo | None = None
    roi: RoiEstimate | None = None
    summary: str = ""
    should_propose: bool = True
    budget_ok: bool = True
    constraints_ok: bool = True
    scale_down_requested: bool = False
