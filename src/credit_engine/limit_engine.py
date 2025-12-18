"""
Limit sizing engine for Monsera V0.

Principles:
- Median vend expresses capacity
- Score expresses confidence
- Volatility & variance reduce exposure, not access
"""

from src.credit_engine.config import MIN_ADVANCE, MAX_ADVANCE

BAND_CAPS = {
    "A": 20000,
    "B": 10000,
    "C": 5000,
    "D": 2000,
}


def _volatility_dampener(vend_amount_volatility: float) -> float:
    if vend_amount_volatility <= 30:
        return 1.00
    elif vend_amount_volatility <= 60:
        return 0.90
    elif vend_amount_volatility <= 100:
        return 0.75
    else:
        return 0.60


def _variance_dampener(inter_vend_variance: float) -> float:
    if inter_vend_variance <= 20:
        return 1.00
    elif inter_vend_variance <= 50:
        return 0.90
    elif inter_vend_variance <= 100:
        return 0.80
    else:
        return 0.70


def determine_limit(features: dict, score: int, band: str) -> int:
    # Starter users
    if features["vend_count_last_60_days"] < 3:
        return MIN_ADVANCE

    median_vend = features["median_vend_amount"]

    # Base capacity-driven amount
    confidence_multiplier = 0.6 + (score / 100) * 0.6
    base_limit = median_vend * confidence_multiplier

    # Behavioural dampening
    base_limit *= _volatility_dampener(features["vend_amount_volatility"])
    base_limit *= _variance_dampener(features["inter_vend_variance"])

    approved = int(base_limit)

    # Apply band cap FIRST
    band_cap = BAND_CAPS.get(band, MIN_ADVANCE)
    approved = min(approved, band_cap)

    # Apply global bounds
    approved = max(approved, MIN_ADVANCE)
    approved = min(approved, MAX_ADVANCE)

    return approved
