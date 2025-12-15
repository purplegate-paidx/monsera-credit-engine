from fastapi import FastAPI
from pydantic import BaseModel
from src.credit_engine.scoring import v0_score

from src.credit_engine.engine import BehaviouralV0Engine
from src.credit_engine.schema import MeterSnapshot, CreditInquiry, RiskEnvelope

app = FastAPI(title="Monsera Credit Engine – V0")


class CreditRequest(BaseModel):
    tenure_months: int
    avg_monthly_spend: float
    vend_frequency: float
    amount_volatility: float
    failed_vend_ratio: float
    is_new_user: bool = False


@app.post("/score")
def score(request: CreditRequest):
    """
    Score a user and return eligibility and credit limit.
    """
    return v0_score(**request.model_dump())




engine = BehaviouralV0Engine()
@app.post("/v0/behavioural-decision")
def behavioural_decision(payload: dict):
    snapshot = MeterSnapshot(**payload["meter_snapshot"])
    inquiry = CreditInquiry(**payload["credit_inquiry"])
    risk_env = RiskEnvelope(**payload.get("risk_envelope", {}))

    decision = engine.assess(inquiry=inquiry, snapshot=snapshot, risk_env=risk_env)

    return {
        "eligible": decision.eligible,
        "behaviour_score": decision.behaviour_score,
        "risk_tier": decision.risk_tier,
        "approved_value": decision.approved_value,
        "explanations": decision.explanations,
        "scorecard": {
            "usage_intensity": decision.scorecard.usage_intensity,
            "usage_stability": decision.scorecard.usage_stability,
            "spending_capacity": decision.scorecard.spending_capacity,
            "operational_reliability": decision.scorecard.operational_reliability,
        } if decision.scorecard else None,
    }

