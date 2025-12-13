"""
Credit limit sizing logic for V0 model.
"""

from typing import Tuple


def determine_limit(
    score: int,
    median_vend_amount: float,
    vend_frequency: float,
    vend_amount_volatility: float,
) -> Tuple[int, str]:
    """
    Returns:
        (approved_limit, band)
    """

    # Score bands
    if score >= 80:
        band = "A"
        cap = 10000
        k = 1.0
    elif score >= 65:
        band = "B"
        cap = 7500
        k = 0.8
    elif score >= 50:
        band = "C"
        cap = 5000
        k = 0.5
    else:
        return 0, "D"

    base_limit = min(cap, int(k * median_vend_amount))

    # Exposure adjustments
    if vend_frequency < 2:
        base_limit = int(base_limit * 0.7)

    if vend_amount_volatility > 60:
        base_limit = int(base_limit * 0.7)

    return max(base_limit, 2000), band
