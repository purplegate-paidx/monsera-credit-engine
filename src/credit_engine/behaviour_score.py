"""
Behavioural scoring logic for V0 model.
Produces a score between 0 and 100.
"""

def compute_behaviour_score(
    vend_count_last_60_days: int,
    vend_frequency: float,
    median_vend_amount: float,
    vend_amount_volatility: float,
    failed_vend_ratio: float,
    days_since_last_vend: int,
) -> int:
    """
    Produces a 0–100 confidence score.
    Used only for limit scaling, not hard eligibility.
    """

    score = 50  # neutral starting point

    # Engagement
    score += min(vend_count_last_60_days * 3, 20)

    # Capacity proxy
    if median_vend_amount >= 6000:
        score += 15
    elif median_vend_amount >= 3000:
        score += 10
    else:
        score += 5

    # Volatility penalty
    if vend_amount_volatility > 80:
        score -= 25
    elif vend_amount_volatility > 50:
        score -= 15
    elif vend_amount_volatility > 30:
        score -= 8

    # Failed attempts penalty (soft)
    if failed_vend_ratio > 40:
        score -= 20
    elif failed_vend_ratio > 20:
        score -= 10

    # Dormancy penalty (soft)
    if days_since_last_vend > 60:
        score -= 20
    elif days_since_last_vend > 30:
        score -= 10

    return max(0, min(score, 100))
