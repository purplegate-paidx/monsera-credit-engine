from typing import List, Tuple

from .schema import MeterSnapshot, CreditInquiry, RiskEnvelope
from .config_v0 import (
    BUCKET_LIMIT_POLICY,
    GLOBAL_MAX_ADVANCE,
    GLOBAL_MIN_ADVANCE,
)


def map_score_to_bucket(score: float) -> str:
    from .config_v0 import RISK_BUCKETS

    for name, lower, upper in RISK_BUCKETS:
        if lower <= score <= upper:
            return name
    return "HIGH_RISK"


def compute_limit(
    score_bucket: str,
    snapshot: MeterSnapshot,
    inquiry: CreditInquiry,
    envelope: RiskEnvelope | None = None,
) -> Tuple[float, List[str]]:
    """
    Translate a risk bucket + meter behaviour into a NGN advance limit,
    with adjustments for volatility and portfolio controls.
    """
    reasons: List[str] = []
    policy = BUCKET_LIMIT_POLICY.get(score_bucket, BUCKET_LIMIT_POLICY["HIGH_RISK"])

    if policy["cap"] <= 0:
        reasons.append("bucket_not_eligible_for_credit")
        return 0.0, reasons

    median_val = max(snapshot.median_vend_value, 0.0)
    base_behaviour_limit = policy["median_multiplier"] * median_val

    # Hard ceiling by bucket + global
    base_limit = min(base_behaviour_limit, policy["cap"], GLOBAL_MAX_ADVANCE)

    # Behaviour-based downscaling
    scale = 1.0
    if snapshot.vend_frequency_60d < 2.0:
        scale *= 0.7
        reasons.append("low_usage_limit_reduction")

    if snapshot.value_volatility > 0.75:
        scale *= 0.7
        reasons.append("high_value_volatility_limit_reduction")

    if snapshot.failed_attempt_ratio > 0.30:
        scale *= 0.5
        reasons.append("high_failure_ratio_limit_reduction")

    adjusted_limit = base_limit * scale

    # Portfolio / float constraints
    if envelope is not None:
        if envelope.float_available is not None and envelope.float_available < adjusted_limit:
            adjusted_limit = envelope.float_available
            reasons.append("float_constraint_limit")

        if (
            envelope.daily_exposure_room is not None
            and envelope.daily_exposure_room < adjusted_limit
        ):
            adjusted_limit = envelope.daily_exposure_room
            reasons.append("daily_portfolio_cap_limit")

        if (
            envelope.channel_exposure_room is not None
            and envelope.channel_exposure_room < adjusted_limit
        ):
            adjusted_limit = envelope.channel_exposure_room
            reasons.append("channel_exposure_cap_limit")

    
    final_amount = min(inquiry.requested_value, adjusted_limit)

    if final_amount < GLOBAL_MIN_ADVANCE:
        reasons.append("below_minimum_advance")
        final_amount = 0.0

    return final_amount, reasons
