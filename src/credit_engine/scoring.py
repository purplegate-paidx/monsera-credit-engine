"""
V0 Credit Decision Orchestrator
"""

from src.credit_engine.hard_gates import check_hard_gates
from src.credit_engine.behaviour_score import compute_behaviour_score
from src.credit_engine.limit_engine import determine_limit


def v0_decision(features: dict) -> dict:
    eligible, reason = check_hard_gates(
        failed_vend_ratio=features["failed_vend_ratio"],
        days_since_last_vend=features["days_since_last_vend"],
        has_active_obligation=features["has_active_obligation"],
    )

    if not eligible:
        return {
            "eligible": False,
            "approved_amount": 0,
            "reason": reason,
        }

    score = compute_behaviour_score(
        vend_count_last_60_days=features["vend_count_last_60_days"],
        vend_frequency=features["vend_frequency"],
        median_vend_amount=features["median_vend_amount"],
        vend_amount_volatility=features["vend_amount_volatility"],
        failed_vend_ratio=features["failed_vend_ratio"],
        days_since_last_vend=features["days_since_last_vend"],
    )

    limit = determine_limit(
        score=score,
        median_vend_amount=features["median_vend_amount"],
        vend_count_last_60_days=features["vend_count_last_60_days"],
    )

    return {
        "eligible": True,
        "score": score,
        "approved_amount": limit,
    }
