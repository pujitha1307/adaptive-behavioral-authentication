import os
import time
import pytest
import pandas as pd
import numpy as np
from app import app
from extract_features import extract_raw, extract
from authenticate import compute_risk, get_thresholds

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess.clear()
        yield client

def get_test_thresholds():
    thresholds = get_thresholds()
    med = thresholds.get("medium_risk_threshold", 60.0)
    high = thresholds.get("high_risk_threshold", 90.0)
    return med, high

def test_feature_extraction_columns():
    """Stage 4: Test that feature extraction produces speed, acc, and jerk columns."""
    t = [1000, 1050, 1100, 1150, 1200]
    x = [100, 105, 115, 130, 150]
    y = [200, 202, 207, 215, 225]
    df = pd.DataFrame({"t": t, "x": x, "y": y})

    features = extract_raw(df)
    assert set(features.columns) == {"speed", "acc", "jerk"}
    assert len(features) == 5

def test_collect_input_validation(client):
    """Stage 3: Test that malformed JSON payloads return HTTP 400."""
    resp = client.post("/collect", json={"t": 1000, "x": 10, "y": 20})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    resp = client.post("/collect", json=[])
    assert resp.status_code == 400

    resp = client.post("/collect", json=[{"t": 1000, "x": 10}])
    assert resp.status_code == 400

    resp = client.post("/collect", json=[{"t": "invalid", "x": 10, "y": 20}])
    assert resp.status_code == 400

def test_debounce_logic(client, monkeypatch):
    """Stage 1: Test 3-window debounce logic for medium risk."""
    client.post("/start-session")
    med, high = get_test_thresholds()
    target_risk = med + 1.0

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": target_risk, "confidence": 100.0 - target_risk})

    # Window 1: Should stay AUTHENTICATED
    res1 = client.post("/collect", json=[{"t": 1000, "x": 10, "y": 20}]).get_json()
    assert res1["status"] == "AUTHENTICATED"

    # Window 2: Should stay AUTHENTICATED
    res2 = client.post("/collect", json=[{"t": 2000, "x": 12, "y": 22}]).get_json()
    assert res2["status"] == "AUTHENTICATED"

    # Window 3: Sustained medium risk -> Should transition to OTP_REQUIRED
    res3 = client.post("/collect", json=[{"t": 3000, "x": 15, "y": 25}]).get_json()
    assert res3["status"] == "OTP_REQUIRED"

def test_debounce_reset_on_low_risk(client, monkeypatch):
    """Stage 1: Test that low risk resets the suspicious_count debounce counter."""
    client.post("/start-session")
    med, high = get_test_thresholds()
    med_risk = med + 1.0
    low_risk = med - 10.0

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": med_risk, "confidence": 100.0 - med_risk})
    client.post("/collect", json=[{"t": 1000, "x": 10, "y": 20}])
    client.post("/collect", json=[{"t": 2000, "x": 12, "y": 22}])

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": low_risk, "confidence": 100.0 - low_risk})
    res_low = client.post("/collect", json=[{"t": 3000, "x": 14, "y": 24}]).get_json()
    assert res_low["status"] == "AUTHENTICATED"

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": med_risk, "confidence": 100.0 - med_risk})
    res_med = client.post("/collect", json=[{"t": 4000, "x": 16, "y": 26}]).get_json()
    assert res_med["status"] == "AUTHENTICATED"

def test_high_risk_immediate_lock(client, monkeypatch):
    """Stage 1: Test that High Risk immediately locks regardless of debounce count."""
    client.post("/start-session")
    med, high = get_test_thresholds()
    target_risk = min(99.9, high + 0.1)

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": target_risk, "confidence": 100.0 - target_risk})
    res = client.post("/collect", json=[{"t": 1000, "x": 10, "y": 20}]).get_json()
    assert res["status"] == "HIGH_RISK_WARNING"

def test_otp_verification_flow(client, monkeypatch):
    """Stage 4: Test OTP verification, wrong OTP, and OTP reuse prevention."""
    client.post("/start-session")
    med, high = get_test_thresholds()
    target_risk = med + 1.0

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": target_risk, "confidence": 100.0 - target_risk})
    for i in range(3):
        client.post("/collect", json=[{"t": (i+1)*1000, "x": 10, "y": 20}])

    with client.session_transaction() as sess:
        otp_code = sess.get("otp_code")
        assert otp_code is not None

    resp_wrong = client.post("/verify-otp", json={"otp": "000000"})
    assert resp_wrong.status_code == 400
    assert resp_wrong.get_json()["result"] == "OTP_INVALID"

    resp_correct = client.post("/verify-otp", json={"otp": otp_code})
    assert resp_correct.status_code == 200
    assert resp_correct.get_json()["result"] == "OTP_VERIFIED"

    resp_reuse = client.post("/verify-otp", json={"otp": otp_code})
    assert resp_reuse.status_code == 400
    assert resp_reuse.get_json()["result"] == "OTP_INVALID"

def test_otp_max_attempts_lockout(client, monkeypatch):
    """Task 3: Test 5-attempt max lockout invalidating OTP."""
    client.post("/start-session")
    med, high = get_test_thresholds()
    target_risk = med + 1.0

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": target_risk, "confidence": 100.0 - target_risk})
    for i in range(3):
        client.post("/collect", json=[{"t": (i+1)*1000, "x": 10, "y": 20}])

    for attempt in range(1, 5):
        resp = client.post("/verify-otp", json={"otp": "000000"})
        assert resp.status_code == 400
        assert resp.get_json()["result"] == "OTP_INVALID"
        assert resp.get_json()["attempts_remaining"] == 5 - attempt

    resp_5 = client.post("/verify-otp", json={"otp": "000000"})
    assert resp_5.status_code == 400
    assert resp_5.get_json()["result"] == "OTP_LOCKED"

    with client.session_transaction() as sess:
        assert sess.get("otp_code") is None

def test_data_derived_thresholds_loader():
    """Task 5: Test loading data-derived risk thresholds from model/thresholds.json."""
    thresholds = get_thresholds()
    assert "medium_risk_threshold" in thresholds
    assert "high_risk_threshold" in thresholds
    assert isinstance(thresholds["medium_risk_threshold"], (int, float))
    assert isinstance(thresholds["high_risk_threshold"], (int, float))
    assert thresholds["medium_risk_threshold"] < thresholds["high_risk_threshold"]

def test_credentials_reauth_flow(client, monkeypatch):
    """Stage 4 & 6: Test re-authentication with password check and specified reason."""
    client.post("/start-session")
    med, high = get_test_thresholds()
    target_risk = min(99.9, high + 0.1)

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": target_risk, "confidence": 100.0 - target_risk})
    client.post("/collect", json=[{"t": 1000, "x": 10, "y": 20}])

    resp_bad = client.post("/verify-credentials", json={
        "username": "user_01",
        "password": "wrongpassword",
        "reason": "Using external trackpad / touchpad"
    })
    assert resp_bad.status_code == 400
    assert resp_bad.get_json()["result"] == "INVALID_CREDENTIALS"

    resp_ok = client.post("/verify-credentials", json={
        "username": "user_01",
        "password": "password123",
        "reason": "Using external trackpad / touchpad"
    })
    assert resp_ok.status_code == 200
    assert resp_ok.get_json()["result"] == "CREDENTIALS_VERIFIED"
