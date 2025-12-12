"""
Utility helper functions shared across the credit engine.
"""

def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    """
    Clamp a numeric value between min_value and max_value.

    Used to ensure credit scores remain within valid bounds.
    """
    return max(min_value, min(value, max_value))
