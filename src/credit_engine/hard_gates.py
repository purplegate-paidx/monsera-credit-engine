"""
Hard eligibility gates for V0 credit model.

These rules are enforced BEFORE scoring.
If any gate fails, the meter is ineligible.
"""

from typing import Tuple


def check_hard_gates(
    failed_vend_ratio: float,
    days_since_last_vend: int,
    has_active_obligation: bool,
) -> Tuple[bool, str | None]:
    """
    HARD gates for V0.

    Philosophy:
    - V0 is a learning model, not a bank
    - Only extreme cases should be declined
    """

    if has_active_obligation:
        return False, "ACTIVE_OUTSTANDING_OBLIGATION"

    # Extreme friction / abuse only
    if failed_vend_ratio >= 70:
        return False, "EXTREME_FAILED_ATTEMPTS"

    # Truly inactive meter
    if days_since_last_vend > 90:
        return False, "LONG_TERM_DORMANT_METER"

    return True, None
