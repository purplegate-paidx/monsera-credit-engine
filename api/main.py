from fastapi import FastAPI
from pydantic import BaseModel
from credit_engine.scoring import v0_score

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
