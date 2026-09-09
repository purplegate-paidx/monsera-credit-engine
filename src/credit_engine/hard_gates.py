"""
Hard gates are ONLY for extreme, system-abusive cases.
They should be rare.
"""

from src.credit_engine.config import (
    MAX_FAILED_VEND_RATIO,
    MAX_DORMANCY_DAYS,
)


def check_hard_gates(features: dict) -> tuple[bool, str | None]:
    """
    Returns (blocked, reason)
    """

    if features.get("has_active_obligation"):
        return True, "ACTIVE_OBLIGATION"

    if features["failed_vend_ratio"] >= MAX_FAILED_VEND_RATIO:
        return True, "EXTREME_FAILED_ATTEMPTS"

    if features["days_since_last_vend"] > MAX_DORMANCY_DAYS:
        return True, "LONG_DORMANCY"

    return False, None
