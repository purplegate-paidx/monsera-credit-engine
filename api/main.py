from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.credit_engine.scoring import v0_decision

app = FastAPI(
    title="Monsera Credit Engine – V0",
    description="Behavioural eligibility and advance decision engine",
    version="0.1.0",
)


class DecisionRequest(BaseModel):
    vend_count_last_60_days: int = Field(..., ge=0)
    days_since_last_vend: int = Field(..., ge=0)
    vend_frequency: float = Field(..., ge=0)
    median_vend_amount: float = Field(..., ge=0)
    vend_amount_volatility: float = Field(..., ge=0)
    inter_vend_variance: float = Field(..., ge=0)
    failed_vend_ratio: float = Field(..., ge=0, le=100)
    has_active_obligation: bool


class DecisionResponse(BaseModel):
    eligible: bool
    score: int | None = None
    band: str | None = None
    approved_amount: int
    reason: str | None = None


@app.post("/decision", response_model=DecisionResponse)
def decision(request: DecisionRequest):
    """
    Run the V0 credit decision engine.

    This endpoint:
    - Enforces hard eligibility gates
    - Computes behaviour score
    - Determines advance amount
    """

    result = v0_decision(request.model_dump())

    return result
