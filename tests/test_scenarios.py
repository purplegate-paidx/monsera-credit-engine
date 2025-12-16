from credit_engine.scoring import v0_decision


def base_features(**overrides):
    features = {
        "vend_count_last_60_days": 8,
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


# ==================================================
# SCENARIO A — Conservative but learning-safe
# ==================================================

def test_scenario_a_conservative_still_approves_normal_users():
    result = v0_decision(base_features())

    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000


def test_scenario_a_extreme_failure_is_declined():
    result = v0_decision(base_features(failed_vend_ratio=80))

    assert result["eligible"] is False
    assert result["approved_amount"] == 0


# ==================================================
# SCENARIO B — Balanced (expected default)
# ==================================================

def test_scenario_b_high_friction_not_declined():
    result = v0_decision(base_features(failed_vend_ratio=45))

    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000


def test_scenario_b_dormant_user_gets_minimum():
    result = v0_decision(base_features(days_since_last_vend=50))

    assert result["eligible"] is True
    assert result["approved_amount"] == 2000


def test_scenario_b_limits_scale_with_capacity():
    low = v0_decision(base_features(median_vend_amount=3000))
    high = v0_decision(base_features(median_vend_amount=12000))

    assert high["approved_amount"] > low["approved_amount"]


# ==================================================
# SCENARIO C — Learning-heavy rollout
# ==================================================

def test_scenario_c_very_low_history_still_approved():
    result = v0_decision(base_features(vend_count_last_60_days=1))

    assert result["eligible"] is True
    assert result["approved_amount"] == 2000


def test_scenario_c_high_volatility_not_declined():
    result = v0_decision(base_features(vend_amount_volatility=95))

    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000


def test_scenario_c_declines_only_extreme_abuse():
    result = v0_decision(
        base_features(
            failed_vend_ratio=85,
            days_since_last_vend=120,
        )
    )

    assert result["eligible"] is False
    assert result["approved_amount"] == 0
