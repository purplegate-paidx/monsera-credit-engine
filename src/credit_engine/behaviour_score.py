"""
Behavioural scoring logic for V0 model.
Produces a score between 0 and 100.
"""

from src.credit_engine.utils import clamp


def compute_behaviour_score(
    vend_frequency: float,
    inter_vend_variance: float,
    median_vend_amount: float,
    vend_amount_volatility: float,
    failed_vend_ratio: float,
) -> int:
    """
    Behaviour score composed of:
    - Frequency (repayment opportunities)
    - Consistency (predictability)
    - Capacity (typical spend level)
    - Reliability (friction & failures)
    """

    score = 0

    # Frequency Score (0–30)
    if vend_frequency >= 5:
        score += 30
    elif vend_frequency >= 3:
        score += 20
    elif vend_frequency >= 1:
        score += 10

    # Consistency Score (0–25)
    # Inter-vend variance + volatility jointly matter
    if inter_vend_variance <= 20 and vend_amount_volatility <= 30:
        score += 25
    elif inter_vend_variance <= 50 and vend_amount_volatility <= 60:
        score += 15
    else:
        score += 5

    # Capacity Score (0–25)
    # Median amount adjusted for volatility
    if median_vend_amount >= 5000 and vend_amount_volatility <= 40:
        score += 25
    elif median_vend_amount >= 3000:
        score += 15
    else:
        score += 5

    # Reliability Score (0–20)
    if failed_vend_ratio < 5:
        score += 20
    elif failed_vend_ratio < 10:
        score += 10
    else:
        score += 0

    return int(clamp(score))
