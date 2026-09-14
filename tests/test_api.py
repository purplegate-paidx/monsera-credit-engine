from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def base_payload(**overrides):
    payload = {
        "vend_count_last_60_days": 8,
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


def test_api_approves_normal_user():
    response = client.post("/decision", json=base_payload())
    data = response.json()

    assert response.status_code == 200
    assert data["eligible"] is True
    assert data["approved_amount"] >= 2000


def test_api_low_history_user_gets_minimum():
    response = client.post(
        "/decision",
        json=base_payload(vend_count_last_60_days=1),
    )
    data = response.json()

    assert data["eligible"] is True
    assert data["approved_amount"] == 2000


def test_api_high_volatility_not_declined():
    response = client.post(
        "/decision",
        json=base_payload(vend_amount_volatility=95),
    )
    data = response.json()

    assert data["eligible"] is True
    assert data["approved_amount"] >= 2000


def test_api_band_c_never_exceeds_cap():
    response = client.post(
        "/decision",
        json=base_payload(
            vend_count_last_60_days=4,
            failed_vend_ratio=30,   # likely Band C
            median_vend_amount=20000,
        ),
    )
    data = response.json()

    assert data["band"] == "C"
    assert data["approved_amount"] <= 5000
