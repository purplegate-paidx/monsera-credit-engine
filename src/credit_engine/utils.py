"""
Utility helper functions shared across the credit engine.
"""

from altair import value


def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    """
    Clamp a numeric value between min_value and max_value.

    Used to ensure credit scores remain within valid bounds.
    """
    return max(min_value, min(value, max_value))


APPROVED_BANDS = [
    2000,
    3000,
    5000,
    7500,
    10000,
    15000,
    20000,
]


def round_to_nearest_band(amount: int) -> int:
    """
    Rounds a raw approved amount to the nearest permitted band.
    """
    return min(APPROVED_BANDS, key=lambda x: abs(x - amount))


def round_to_step(amount: int, step: int = 500) -> int:
    """
    Rounds amount to the nearest step (e.g. ₦500).
    """
    return int(round(amount / step) * step)

