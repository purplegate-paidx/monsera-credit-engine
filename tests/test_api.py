from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def base_payload(**overrides):
    payload = {
        "vend_count_last_60_days": 10,
        "days_since_last_vend": 5,
        "vend_frequency": 3,
        "median_vend_amount": 4000,
        "vend_amount_volatility": 30,
        "inter_vend_variance": 20,
        "failed_vend_ratio": 10,
        "has_active_obligation": False,
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------
# APPROVAL FLOWS
# --------------------------------------------------

def test_decision_endpoint_approves_normal_user():
    response = client.post("/decision", json=base_payload())
    data = response.json()

    assert response.status_code == 200
    assert data["eligible"] is True
    assert data["approved_amount"] >= 2000


def test_low_history_user_approved_minimum():
    response = client.post(
        "/decision",
        json=base_payload(vend_count_last_60_days=1),
    )

    data = response.json()

    assert data["eligible"] is True
    assert data["approved_amount"] == 2000


def test_high_friction_user_not_declined():
    response = client.post(
        "/decision",
        json=base_payload(failed_vend_ratio=45),
    )

    data = response.json()

    assert data["eligible"] is True
    assert data["approved_amount"] >= 2000


# --------------------------------------------------
# HARD DECLINES
# --------------------------------------------------

def test_api_declines_extreme_failed_attempts():
    response = client.post(
        "/decision",
        json=base_payload(failed_vend_ratio=80),
    )

    data = response.json()

    assert data["eligible"] is False
    assert data["approved_amount"] == 0
    assert data["reason"] == "EXTREME_FAILED_ATTEMPTS"


def test_api_declines_long_dormant_meter():
    response = client.post(
        "/decision",
        json=base_payload(days_since_last_vend=120),
    )

    data = response.json()

    assert data["eligible"] is False
    assert data["approved_amount"] == 0
    assert data["reason"] == "LONG_TERM_DORMANT_METER"
