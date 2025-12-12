"""
V0 Credit Scoring Engine

Deterministic, rule-based scoring model used to:
- compute a credit score (0–100)
- assign a risk band
- determine an advance amount

"""

from credit_engine.config import (
    TENURE_WEIGHTS,
    SPEND_WEIGHTS,
    FREQUENCY_WEIGHTS,
    VOLATILITY_WEIGHTS,
    FAILED_VEND_PENALTIES,
    MIN_LIMIT,
    MAX_LIMIT,
)
from .utils import clamp


def v0_score(
    tenure_months: int,
    avg_monthly_spend: float,
    vend_frequency: float,
    amount_volatility: float,
    failed_vend_ratio: float,
    is_new_user: bool = False,
):
    """
    Compute the V0 credit score, risk band, and credit limit.

    Returns:
        dict with keys:
        - score
        - risk_band
        - credit_limit
    """

    # --- New user rule ---
    if is_new_user:
        return {
            "score": 45,
            "risk_band": "Marginal",
            "credit_limit": MIN_LIMIT,
            "reason": "New user with no historical data",
        }

    total_score = 0

    # --- Tenure scoring ---
    if tenure_months >= 12:
        total_score += TENURE_WEIGHTS[">=12"]
    elif tenure_months >= 6:
        total_score += TENURE_WEIGHTS["6-11"]
    elif tenure_months >= 3:
        total_score += TENURE_WEIGHTS["3-5"]
    else:
        total_score += TENURE_WEIGHTS["<3"]

    # --- Spend scoring ---
    if avg_monthly_spend >= 8000:
        total_score += SPEND_WEIGHTS[">=8000"]
    elif avg_monthly_spend >= 5000:
        total_score += SPEND_WEIGHTS["5000-7999"]
    elif avg_monthly_spend >= 3000:
        total_score += SPEND_WEIGHTS["3000-4999"]
    else:
        total_score += SPEND_WEIGHTS["<3000"]

    # --- Frequency scoring ---
    if vend_frequency >= 5:
        total_score += FREQUENCY_WEIGHTS[">=5"]
    elif vend_frequency >= 3:
        total_score += FREQUENCY_WEIGHTS["3-4"]
    elif vend_frequency >= 1:
        total_score += FREQUENCY_WEIGHTS["1-2"]
    else:
        total_score += FREQUENCY_WEIGHTS["<1"]

    # --- Volatility scoring ---
    if amount_volatility <= 30:
        total_score += VOLATILITY_WEIGHTS["<=30"]
    elif amount_volatility <= 60:
        total_score += VOLATILITY_WEIGHTS["31-60"]
    else:
        total_score += VOLATILITY_WEIGHTS[">60"]

    # --- Failed vend penalties ---
    if failed_vend_ratio >= 20:
        total_score += FAILED_VEND_PENALTIES[">=20"]
    elif failed_vend_ratio >= 10:
        total_score += FAILED_VEND_PENALTIES["10-19"]
    else:
        total_score += FAILED_VEND_PENALTIES["<10"]

    # --- Clamp score ---
    score = clamp(total_score)

    # --- Risk band mapping ---
    if score < 40:
        risk_band = "High Risk"
    elif score < 60:
        risk_band = "Marginal"
    elif score < 80:
        risk_band = "Bankable"
    else:
        risk_band = "Prime Meter"

    # --- Credit limit determination ---
    if score < 40:
        credit_limit = 0
    elif score < 60:
        credit_limit = MIN_LIMIT
    elif score < 80:
        credit_limit = min(int(avg_monthly_spend * 0.10), 10000)
    else:
        credit_limit = min(int(avg_monthly_spend * 0.20), MAX_LIMIT)

    return {
        "score": score,
        "risk_band": risk_band,
        "credit_limit": credit_limit,
    }
