from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def base_payload(**overrides):
    payload = {
        "vend_count_last_60_days": 12,
        "days_since_last_vend": 2,
        "vend_frequency": 3,
        "median_vend_amount": 4000,
        "vend_amount_volatility": 30,
        "inter_vend_variance": 25,
        "failed_vend_ratio": 5,
        "has_active_obligation": False,
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------
# Successful decision scenarios
# --------------------------------------------------

def test_decision_endpoint_returns_approval():
    response = client.post("/decision", json=base_payload())
    data = response.json()

    assert response.status_code == 200
    assert data["eligible"] is True
    assert data["approved_amount"] >= 2000


def test_low_history_user_gets_minimum_via_api():
    response = client.post(
        "/decision",
        json=base_payload(vend_count_last_60_days=1),
    )

    data = response.json()

    assert data["eligible"] is True
    assert data["approved_amount"] == 2000
    assert data["reason"] == "STARTER_MIN_LIMIT"


def test_high_volatility_user_still_gets_minimum_via_api():
    response = client.post(
        "/decision",
        json=base_payload(vend_amount_volatility=95),
    )

    data = response.json()

    assert data["eligible"] is True
    assert data["approved_amount"] == 2000


# --------------------------------------------------
# Hard declines
# --------------------------------------------------

def test_api_rejects_active_obligation():
    response = client.post(
        "/decision",
        json=base_payload(has_active_obligation=True),
    )

    data = response.json()

    assert data["eligible"] is False
    assert data["approved_amount"] == 0
    assert data["reason"] == "ACTIVE_OUTSTANDING_OBLIGATION"


def test_api_rejects_high_failed_attempts():
    response = client.post(
        "/decision",
        json=base_payload(failed_vend_ratio=35),
    )

    data = response.json()

    assert data["eligible"] is False
    assert data["approved_amount"] == 0
    assert data["reason"] == "HIGH_FAILED_ATTEMPTS"
