import sys
import requests

BASE = "http://127.0.0.1:8000"

# these tests require the backend server to be running

def test_register_and_login_user():
    # user registration
    payload = {
        "name": "Test User",
        "phone": "1234567890",
        "password": "pass123",
        "age": 30
    }
    r = requests.post(f"{BASE}/auth/register", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["success"]
    assert data["user"]["phone"] == "1234567890"

    # duplicate register should fail
    r2 = requests.post(f"{BASE}/auth/register", json=payload)
    assert r2.status_code == 200
    assert not r2.json()["success"]

    # login with correct credentials
    login_payload = {"phone": "1234567890", "password": "pass123"}
    r3 = requests.post(f"{BASE}/auth/login", json=login_payload)
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["success"]
    assert d3["user"]["phone"] == "1234567890"

    # login with bad password
    r4 = requests.post(f"{BASE}/auth/login", json={"phone": "1234567890", "password": "wrong"})
    assert r4.status_code == 200
    assert not r4.json()["success"]


def test_register_and_login_admin():
    payload = {
        "name": "Test Admin",
        "shop_id": "SHOP123",
        "password": "adminpass"
    }
    r = requests.post(f"{BASE}/auth/register", json=payload)
    assert r.status_code == 200
    assert r.json()["success"]
    assert r.json()["user"]["shop_id"] == "SHOP123"

    r2 = requests.post(f"{BASE}/auth/login", json={"shop_id": "SHOP123", "password": "adminpass"})
    assert r2.status_code == 200
    assert r2.json()["success"]
    assert r2.json()["user"]["shop_id"] == "SHOP123"
