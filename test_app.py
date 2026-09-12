import os
import time
import pytest
import pandas as pd
import numpy as np
from app import app
from extract_features import extract_raw, extract
from authenticate import compute_risk

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess.clear()
        yield client

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
    # Test non-list payload
    resp = client.post("/collect", json={"t": 1000, "x": 10, "y": 20})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Test empty list
    resp = client.post("/collect", json=[])
    assert resp.status_code == 400

    # Test missing keys
    resp = client.post("/collect", json=[{"t": 1000, "x": 10}])
    assert resp.status_code == 400

    # Test non-numeric coordinates
    resp = client.post("/collect", json=[{"t": "invalid", "x": 10, "y": 20}])
    assert resp.status_code == 400

def test_debounce_logic(client, monkeypatch):
    """Stage 1: Test 3-window debounce logic for medium risk."""
    client.post("/start-session")

    # Mock compute_risk to return medium risk (70%)
    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": 70.0, "confidence": 30.0})

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

    # 2 medium risk windows
    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": 70.0, "confidence": 30.0})
    client.post("/collect", json=[{"t": 1000, "x": 10, "y": 20}])
    client.post("/collect", json=[{"t": 2000, "x": 12, "y": 22}])

    # 1 low risk window -> should reset count
    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": 20.0, "confidence": 80.0})
    res_low = client.post("/collect", json=[{"t": 3000, "x": 14, "y": 24}]).get_json()
    assert res_low["status"] == "AUTHENTICATED"

    # Next medium risk window -> count starts at 1, so still AUTHENTICATED
    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": 70.0, "confidence": 30.0})
    res_med = client.post("/collect", json=[{"t": 4000, "x": 16, "y": 26}]).get_json()
    assert res_med["status"] == "AUTHENTICATED"

def test_high_risk_immediate_lock(client, monkeypatch):
    """Stage 1: Test that High Risk (>=90%) immediately locks regardless of debounce count."""
    client.post("/start-session")

    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": 95.0, "confidence": 5.0})
    res = client.post("/collect", json=[{"t": 1000, "x": 10, "y": 20}]).get_json()
    assert res["status"] == "HIGH_RISK_WARNING"

def test_otp_verification_flow(client, monkeypatch):
    """Stage 4: Test OTP verification, wrong OTP, and OTP reuse prevention."""
    client.post("/start-session")

    # Trigger OTP state (3 windows)
    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": 70.0, "confidence": 30.0})
    for i in range(3):
        client.post("/collect", json=[{"t": (i+1)*1000, "x": 10, "y": 20}])

    # Retrieve generated OTP from session
    with client.session_transaction() as sess:
        otp_code = sess.get("otp_code")
        assert otp_code is not None

    # Test wrong OTP
    resp_wrong = client.post("/verify-otp", json={"otp": "000000"})
    assert resp_wrong.status_code == 400
    assert resp_wrong.get_json()["result"] == "OTP_INVALID"

    # Test correct OTP
    resp_correct = client.post("/verify-otp", json={"otp": otp_code})
    assert resp_correct.status_code == 200
    assert resp_correct.get_json()["result"] == "OTP_VERIFIED"

    # Test OTP reuse attempt (should fail as code was cleared)
    resp_reuse = client.post("/verify-otp", json={"otp": otp_code})
    assert resp_reuse.status_code == 400
    assert resp_reuse.get_json()["result"] == "OTP_INVALID"

def test_credentials_reauth_flow(client, monkeypatch):
    """Stage 4 & 6: Test re-authentication with password check and specified reason."""
    client.post("/start-session")

    # Trigger High Risk
    monkeypatch.setattr("app.compute_risk", lambda path: {"risk": 92.0, "confidence": 8.0})
    client.post("/collect", json=[{"t": 1000, "x": 10, "y": 20}])

    # Test wrong password
    resp_bad = client.post("/verify-credentials", json={
        "username": "user_01",
        "password": "wrongpassword",
        "reason": "Using external trackpad / touchpad"
    })
    assert resp_bad.status_code == 400
    assert resp_bad.get_json()["result"] == "INVALID_CREDENTIALS"

    # Test correct password + reason
    resp_ok = client.post("/verify-credentials", json={
        "username": "user_01",
        "password": "password123",
        "reason": "Using external trackpad / touchpad"
    })
    assert resp_ok.status_code == 200
    assert resp_ok.get_json()["result"] == "CREDENTIALS_VERIFIED"
