import pytest
from credit_engine.scoring import v0_decision


def base_features(**overrides):
    features = {
        "vend_count_last_60_days": 10,
        "days_since_last_vend": 5,
        "vend_frequency": 3,
        "median_vend_amount": 4000,
        "vend_amount_volatility": 30,
        "inter_vend_variance": 20,
        "failed_vend_ratio": 10,
        "has_active_obligation": False,
    }
    features.update(overrides)
    return features


# --------------------------------------------------
# HARD DECLINES (VERY RARE)
# --------------------------------------------------

def test_active_obligation_is_declined():
    result = v0_decision(base_features(has_active_obligation=True))

    assert result["eligible"] is False
    assert result["approved_amount"] == 0
    assert result["reason"] == "ACTIVE_OUTSTANDING_OBLIGATION"


def test_extreme_failed_attempts_are_declined():
    result = v0_decision(base_features(failed_vend_ratio=75))

    assert result["eligible"] is False
    assert result["approved_amount"] == 0
    assert result["reason"] == "EXTREME_FAILED_ATTEMPTS"


def test_long_term_dormant_meter_is_declined():
    result = v0_decision(base_features(days_since_last_vend=120))

    assert result["eligible"] is False
    assert result["approved_amount"] == 0
    assert result["reason"] == "LONG_TERM_DORMANT_METER"


# --------------------------------------------------
# STARTER / LOW HISTORY USERS
# --------------------------------------------------

def test_low_history_user_gets_minimum_advance():
    result = v0_decision(base_features(vend_count_last_60_days=1))

    assert result["eligible"] is True
    assert result["approved_amount"] == 2000


# --------------------------------------------------
# FRICTION & VOLATILITY (SOFT EFFECTS)
# --------------------------------------------------

def test_high_failed_ratio_reduces_limit_not_decline():
    result = v0_decision(base_features(failed_vend_ratio=45))

    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000


def test_high_volatility_reduces_limit_not_zero():
    result = v0_decision(base_features(vend_amount_volatility=90))

    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000


def test_recent_dormancy_reduces_limit_not_decline():
    result = v0_decision(base_features(days_since_last_vend=45))

    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000


# --------------------------------------------------
# CONTINUOUS LIMIT DISTRIBUTION
# --------------------------------------------------

def test_higher_median_vend_gets_higher_limit():
    low = v0_decision(base_features(median_vend_amount=2500))
    high = v0_decision(base_features(median_vend_amount=8000))

    assert high["approved_amount"] > low["approved_amount"]


def test_score_affects_limit_continuously_when_scaling_is_possible():
    weak = v0_decision(
        base_features(
            vend_count_last_60_days=3,
            median_vend_amount=3000,
        )
    )

    strong = v0_decision(
        base_features(
            vend_count_last_60_days=15,
            median_vend_amount=10000,
        )
    )

    assert strong["approved_amount"] > weak["approved_amount"]


# --------------------------------------------------
# ABSOLUTE INVARIANT
# --------------------------------------------------

def test_eligible_users_never_receive_zero():
    result = v0_decision(base_features(vend_amount_volatility=95))

    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000
