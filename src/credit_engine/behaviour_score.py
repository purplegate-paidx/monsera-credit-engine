"""
Behaviour score = trust / engagement signal.
Does NOT measure smoothness.
"""

def compute_behaviour_score(features: dict) -> int:
    score = 50  # neutral baseline

    # Activity
    if features["vend_count_last_60_days"] >= 10:
        score += 20
    elif features["vend_count_last_60_days"] >= 5:
        score += 10

    # Recency
    if features["days_since_last_vend"] <= 7:
        score += 15
    elif features["days_since_last_vend"] <= 30:
        score += 5

    # Failed vends (only meaningful degradation)
    if features["failed_vend_ratio"] >= 50:
        score -= 20
    elif features["failed_vend_ratio"] >= 30:
        score -= 10

    return max(0, min(100, score))
