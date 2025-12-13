"""
V0 Credit Decision Orchestrator
"""

from src.credit_engine.hard_gates import check_hard_gates
from src.credit_engine.behaviour_score import compute_behaviour_score
from src.credit_engine.limit_engine import determine_limit


def v0_decision(features: dict) -> dict:
    """
    End-to-end V0 decision.
    """

    eligible, gate_reason = check_hard_gates(
        vend_count_last_60_days=features["vend_count_last_60_days"],
        days_since_last_vend=features["days_since_last_vend"],
        failed_vend_ratio=features["failed_vend_ratio"],
        has_active_obligation=features["has_active_obligation"],
    )

    if not eligible:
        return {
            "eligible": False,
            "reason": gate_reason,
            "approved_amount": 0,
        }

    score = compute_behaviour_score(
        vend_frequency=features["vend_frequency"],
        inter_vend_variance=features["inter_vend_variance"],
        median_vend_amount=features["median_vend_amount"],
        vend_amount_volatility=features["vend_amount_volatility"],
        failed_vend_ratio=features["failed_vend_ratio"],
    )

    limit, band = determine_limit(
        score=score,
        median_vend_amount=features["median_vend_amount"],
        vend_frequency=features["vend_frequency"],
        vend_amount_volatility=features["vend_amount_volatility"],
    )

    return {
        "eligible": True,
        "score": score,
        "band": band,
        "approved_amount": limit,
    }
