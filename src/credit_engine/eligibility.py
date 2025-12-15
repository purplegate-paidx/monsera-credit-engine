from typing import List, Tuple

from .schema import MeterSnapshot
from .config_v0 import GATE_LIMITS


def run_gate_checks(snapshot: MeterSnapshot) -> Tuple[bool, List[str]]:
    """
    Apply the non-negotiable V0 eligibility checks
    before we even bother to compute a behaviour score.
    """
    reasons: List[str] = []

    if snapshot.has_open_obligation:
        reasons.append("existing_unsettled_advance")

    if snapshot.vend_count_60d < GATE_LIMITS["min_vends_60d"]:
        reasons.append("insufficient_activity_window")

    if snapshot.days_since_last_vend > GATE_LIMITS["max_idle_days"]:
        reasons.append("inactive_or_dormant_meter")

    if snapshot.failed_attempt_ratio > GATE_LIMITS["max_failed_ratio"]:
        reasons.append("too_many_failed_vend_attempts")

    if snapshot.channel_switch_index > GATE_LIMITS["max_channel_switch"]:
        reasons.append("extreme_channel_instability")

    return (len(reasons) == 0), reasons
