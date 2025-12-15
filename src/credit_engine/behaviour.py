from .schema import MeterSnapshot, ScoreCard
from .config_v0 import COMPONENT_WEIGHTS, SCORE_LIMITS


def build_scorecard(snapshot: MeterSnapshot) -> ScoreCard:
    """
    Turn a MeterSnapshot into a decomposed ScoreCard
    using the V0 behavioural rules.
    """
    usage_intensity = _score_usage_intensity(
        snapshot.vend_frequency_60d,
        snapshot.days_since_last_vend,
    )
    usage_stability = _score_usage_stability(snapshot.spacing_variance)
    spending_capacity = _score_spending_capacity(
        snapshot.median_vend_value,
        snapshot.value_volatility,
    )
    operational_reliability = _score_operational_reliability(
        snapshot.failed_attempt_ratio,
        snapshot.channel_switch_index,
    )

    return ScoreCard(
        usage_intensity=usage_intensity,
        usage_stability=usage_stability,
        spending_capacity=spending_capacity,
        operational_reliability=operational_reliability,
    )


def _score_usage_intensity(freq: float, days_since_last: int) -> float:
    w = COMPONENT_WEIGHTS["usage_intensity"]
    t = SCORE_LIMITS

    if freq <= 0:
        base = 0.0
    elif freq >= t["freq_high"]:
        base = w
    elif freq >= t["freq_mid"]:
        base = 0.7 * w
    elif freq >= t["freq_low"]:
        base = 0.4 * w
    else:
        base = 0.1 * w

    # Adjust for recency
    if days_since_last <= t["recency_fresh"]:
        return base
    if days_since_last <= t["recency_stale"]:
        return max(base - 0.25 * w, 0.0)
    return max(base - 0.5 * w, 0.0)


def _score_usage_stability(spacing_var: float) -> float:
    w = COMPONENT_WEIGHTS["usage_stability"]
    t = SCORE_LIMITS

    if spacing_var <= 0:
        return w

    low = t["spacing_var_low"]
    high = t["spacing_var_high"]

    if spacing_var <= low:
        return w
    if spacing_var >= high:
        return 0.3 * w

    
    ratio = (spacing_var - low) / (high - low)
    return w * (1.0 - 0.7 * ratio)


def _score_spending_capacity(median_value: float, volatility: float) -> float:
    w = COMPONENT_WEIGHTS["spending_capacity"]
    t = SCORE_LIMITS

    if median_value <= 0:
        return 0.0

    reference = 15_000.0  # where we hit the full capacity score
    capped = min(median_value, reference)
    base = (capped / reference) * w

    # volatility penalty
    if volatility >= t["value_vol_high"]:
        base *= 0.5
    elif volatility >= t["value_vol_low"]:
        base *= 0.8

    return max(base, 0.0)


def _score_operational_reliability(
    failed_ratio: float,
    channel_switch_index: float,
) -> float:
    w = COMPONENT_WEIGHTS["operational_reliability"]
    t = SCORE_LIMITS

    score = w

    low = t["failed_low"]
    high = t["failed_high"]

    if failed_ratio <= low:
        pass
    elif failed_ratio >= high:
        score *= 0.3
    else:
        ratio = (failed_ratio - low) / (high - low)
        score *= (1.0 - 0.7 * ratio)

    if channel_switch_index > 0.8:
        score *= 0.8

    return max(score, 0.0)
