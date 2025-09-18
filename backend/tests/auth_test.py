import uuid

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from schemas.user_schema import LoginRequest, TokenResponse, UserCreate, LoginResponse
from models.user_model import UserRole
from _test_utils import build_from_model, build_user_response, assert_subset

CTRL = "controllers.auth_controller"

REGISTER_PAYLOAD = build_from_model(
    UserCreate,
    overrides={"email": "alice@example.com", "password": "secret", "name": "Alice", "profile_image": "" , "role": UserRole.student},
    json_safe=True,
)
LOGIN_PAYLOAD = build_from_model(
    LoginRequest,
    overrides={"email": "alice@example.com", "password": "secret"},
    json_safe=True,
)



def test_register_success(client_ok, monkeypatch):
    user_out = build_user_response(
        {"id": "11111111-1111-1111-1111-111111111111", "email": "alice@example.com", "name": "Alice", "role": UserRole.student, "profile_image": ""}
    )
    def fake_create_user(db, data):
        try:
            return user_out.model_dump()
        except Exception:
            return user_out
    monkeypatch.setattr(f"{CTRL}.create_user", fake_create_user, raising=False)

    r = client_ok.post("/auth/register", json=REGISTER_PAYLOAD)
    assert r.status_code == status.HTTP_201_CREATED
    resp = r.json()
    assert_subset({"id": "11111111-1111-1111-1111-111111111111", "email": "alice@example.com", "name": "Alice"}, resp)

def test_register_duplicate_error(client_ok, monkeypatch):
    def fake_create_user(db, data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
    monkeypatch.setattr(f"{CTRL}.create_user", fake_create_user, raising=False)

    r = client_ok.post("/auth/register", json=REGISTER_PAYLOAD)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "exists" in r.json()["detail"]

def test_register_integrity_error(client_ok, monkeypatch):
    def fake_create_user(db, data):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="db constraint")
    monkeypatch.setattr(f"{CTRL}.create_user", fake_create_user, raising=False)

    r = client_ok.post("/auth/register", json=REGISTER_PAYLOAD)
    assert r.status_code == status.HTTP_409_CONFLICT
    assert "constraint" in r.json()["detail"]

def test_login_success(client_ok, monkeypatch):
    uid = "11111111-1111-1111-1111-111111111111"
    user_out_model = build_user_response(
        {"id": uid, "email": "alice@example.com", "name": "Alice", "role": UserRole.student, "profile_image": ""}
    )

    def fake_authenticate_user(db, email, password):
        assert email == "alice@example.com"
        assert password == "secret"
        return user_out_model

    def fake_create_access_token(subject: str, extra_claims: dict | None = None):
        assert subject == uid
        from models.user_model import UserRole as _R
        assert extra_claims and extra_claims.get("role") == _R.student.value
        return "fake-token"

    monkeypatch.setattr(f"{CTRL}.authenticate_user", fake_authenticate_user, raising=False)
    monkeypatch.setattr(f"{CTRL}.create_access_token", fake_create_access_token, raising=False)

    r = client_ok.post("/auth/login", json=LOGIN_PAYLOAD)
    assert r.status_code == status.HTTP_200_OK
    body = r.json()
    assert body.get("access_token") == "fake-token"
    assert body.get("user", {}).get("id") == uid
    assert body.get("user", {}).get("email") == "alice@example.com"

def test_login_invalid_credentials(client_ok, monkeypatch):
    def fake_authenticate_user(db, email, password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    monkeypatch.setattr(f"{CTRL}.authenticate_user", fake_authenticate_user, raising=False)

    r = client_ok.post("/auth/login", json=LOGIN_PAYLOAD)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid" in r.json()["detail"].lower()