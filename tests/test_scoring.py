import pytest
from credit_engine.scoring import v0_decision


def base_features(**overrides):
    features = {
        "vend_count_last_60_days": 12,
        "days_since_last_vend": 2,
        "vend_frequency": 3,
        "median_vend_amount": 4000,
        "vend_amount_volatility": 30,
        "inter_vend_variance": 25,
        "failed_vend_ratio": 5,
        "has_active_obligation": False,
    }
    features.update(overrides)
    return features


# --------------------------------------------------
# Hard decline tests (ONLY real declines)
# --------------------------------------------------

def test_user_with_active_obligation_is_declined():
    result = v0_decision(base_features(has_active_obligation=True))

    assert result["eligible"] is False
    assert result["reason"] == "ACTIVE_OUTSTANDING_OBLIGATION"
    assert result["approved_amount"] == 0


def test_high_failed_vend_ratio_triggers_decline():
    result = v0_decision(base_features(failed_vend_ratio=30))

    assert result["eligible"] is False
    assert result["reason"] == "HIGH_FAILED_ATTEMPTS"
    assert result["approved_amount"] == 0


def test_dormant_meter_is_declined():
    result = v0_decision(base_features(days_since_last_vend=45))

    assert result["eligible"] is False
    assert result["reason"] == "DORMANT_METER"
    assert result["approved_amount"] == 0


# --------------------------------------------------
# Starter / low history behaviour
# --------------------------------------------------

def test_low_history_user_gets_minimum_advance():
    result = v0_decision(base_features(vend_count_last_60_days=1))

    assert result["eligible"] is True
    assert result["approved_amount"] == 2000
    assert result["reason"] == "STARTER_MIN_LIMIT"


# --------------------------------------------------
# Behaviour scoring & bands
# --------------------------------------------------

def test_strong_behaviour_gets_band_a():
    result = v0_decision(
        base_features(
            vend_frequency=6,
            median_vend_amount=7000,
            vend_amount_volatility=20,
            inter_vend_variance=15,
            failed_vend_ratio=2,
        )
    )

    assert result["eligible"] is True
    assert result["band"] == "A"
    assert result["approved_amount"] > 2000


def test_good_behaviour_gets_band_b():
    result = v0_decision(
        base_features(
            vend_frequency=4,
            median_vend_amount=5000,
            vend_amount_volatility=35,
            inter_vend_variance=35,
            failed_vend_ratio=5,
        )
    )

    assert result["eligible"] is True
    assert result["band"] == "B"
    assert result["approved_amount"] >= 2000


def test_marginal_behaviour_gets_band_c_and_minimum():
    result = v0_decision(
        base_features(
            vend_frequency=2,
            median_vend_amount=3000,
            vend_amount_volatility=50,
            inter_vend_variance=50,
            failed_vend_ratio=8,
        )
    )

    assert result["eligible"] is True
    assert result["band"] == "C"
    assert result["approved_amount"] == 2000


def test_weak_behaviour_still_gets_minimum_not_zero():
    result = v0_decision(
        base_features(
            vend_frequency=1,
            median_vend_amount=1500,
            vend_amount_volatility=90,
            inter_vend_variance=70,
            failed_vend_ratio=20,
        )
    )

    assert result["eligible"] is True
    assert result["band"] == "D"
    assert result["approved_amount"] == 2000


# --------------------------------------------------
# Absolute invariant
# --------------------------------------------------

def test_eligible_users_never_receive_zero():
    result = v0_decision(base_features(vend_amount_volatility=95))

    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000
