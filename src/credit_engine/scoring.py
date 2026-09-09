"""
V0 Credit Decision Orchestrator
"""

from src.credit_engine.behaviour_score import compute_behaviour_score
from src.credit_engine.hard_gates import check_hard_gates
from src.credit_engine.limit_engine import determine_limit


def v0_decision(features: dict) -> dict:
    blocked, reason = check_hard_gates(features)
    if blocked:
        return {
            "eligible": False,
            "approved_amount": 0,
            "reason": reason,
            "score": 0,
            "band": "REJECTED",
        }

    score = compute_behaviour_score(features)

    if score >= 80:
        band = "A"
    elif score >= 60:
        band = "B"
    elif score >= 40:
        band = "C"
    else:
        band = "D"

    approved_amount = determine_limit(features, score, band)

    return {
        "eligible": True,
        "approved_amount": approved_amount,
        "reason": "APPROVED",
        "score": score,
        "band": band,
    }
