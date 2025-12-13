"""
Hard eligibility gates for V0 credit model.

These rules are enforced BEFORE scoring.
If any gate fails, the meter is ineligible.
"""

from typing import Tuple


def check_hard_gates(
    vend_count_last_60_days: int,
    days_since_last_vend: int,
    failed_vend_ratio: float,
    has_active_obligation: bool,
) -> Tuple[bool, str | None]:
    """
    Returns:
        (is_eligible, reason_code)
    """

    if has_active_obligation:
        return False, "ACTIVE_OUTSTANDING_OBLIGATION"

    if vend_count_last_60_days < 6:
        return False, "INSUFFICIENT_HISTORY"

    if days_since_last_vend > 30:
        return False, "DORMANT_METER"

    if failed_vend_ratio >= 25:
        return False, "HIGH_FAILED_ATTEMPTS"

    return True, None
