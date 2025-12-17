"""
Credit limit sizing logic for V0 model.
"""

def determine_limit(
    score: int,
    median_vend_amount: float,
    vend_count_last_60_days: int,
    exposure_multiplier: float = 1.0,
) -> int:
    """
    Continuous limit sizing for V0.

    Goals:
    - No discrete tiers
    - No ₦0 approvals
    - Wide distribution for learning
    """

    MIN_ADVANCE = 2000
    MAX_ADVANCE = 20000

    # Starter / low-history users
    if vend_count_last_60_days < 3:
        return MIN_ADVANCE

    # Confidence factor from score (0.1 → 0.6)
    confidence = 0.1 + (score / 100) * 0.5

    raw_limit = confidence * median_vend_amount

    # Apply scenario aggressiveness
    raw_limit = raw_limit * exposure_multiplier

    approved = int(raw_limit)

    # Enforce absolute bounds
    approved = max(approved, MIN_ADVANCE)
    approved = min(approved, MAX_ADVANCE)

    return approved
