
import uuid
import datetime
import typing

import pytest
from fastapi import HTTPException, status

from _test_utils import assert_subset, build_course

EXAMPLE_USER_CREATE = {
    "email": "alice@example.com",
    "password": "secret",
    "name": "Alice",
    "role": "student",
    "profile_image": ""
}

EXAMPLE_USER_UPDATE = {
    "email": "alice2@example.com",
    "name": "Alice 2",
    "role": "student",
    "profile_image": ""
}

EXAMPLE_USER_MINIMUM = {
    "id": "11111111-1111-1111-1111-111111111111",
    "email": "alice@example.com",
    "name": "Alice",
    "role": "student",
    "profile_image": ""
}

EXAMPLE_USER_MINIMUM_UPDATED = {
    "id": "11111111-1111-1111-1111-111111111111",
    "email": "alice2@example.com",
    "name": "Alice 2",
    "role": "student",
    "profile_image": ""
}


CTRL = "controllers.user_controller"


def test_create_user_success(client_auth_ok, monkeypatch):
    def fake_create(db, data):
        return EXAMPLE_USER_MINIMUM
    monkeypatch.setattr(f"{CTRL}.create_user", fake_create, raising=False)

    r = client_auth_ok.post("/users/", json=EXAMPLE_USER_CREATE)
    assert r.status_code == status.HTTP_201_CREATED
    resp = r.json()
    assert_subset(EXAMPLE_USER_MINIMUM, resp)

def test_create_user_duplicate_error(client_auth_ok, monkeypatch):
    def fake_create(db, data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
    monkeypatch.setattr(f"{CTRL}.create_user", fake_create, raising=False)

    r = client_auth_ok.post("/users/", json=EXAMPLE_USER_CREATE)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "exists" in r.json()["detail"]

def test_create_user_integrity_error(client_auth_ok, monkeypatch):
    def fake_create(db, data):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="db constraint")
    monkeypatch.setattr(f"{CTRL}.create_user", fake_create, raising=False)

    r = client_auth_ok.post("/users/", json=EXAMPLE_USER_CREATE)
    assert r.status_code == status.HTTP_409_CONFLICT
    assert "constraint" in r.json()["detail"]

def test_create_user_forbidden(client_forbidden):
    r = client_forbidden.post("/users/", json=EXAMPLE_USER_CREATE)
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_create_user_unauthorized(client_unauthorized):
    r = client_unauthorized.post("/users/", json=EXAMPLE_USER_CREATE)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    

def test_get_users_success(client_auth_ok, monkeypatch):
    def fake_get_users(db):
        return [EXAMPLE_USER_MINIMUM]
    monkeypatch.setattr(f"{CTRL}.get_users", fake_get_users, raising=False)

    r = client_auth_ok.get("/users/")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1
    assert_subset(EXAMPLE_USER_MINIMUM, data[0])

def test_get_users_forbidden(client_forbidden):
    r = client_forbidden.get("/users/")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_users_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/users/")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_by_id_success(client_auth_ok, monkeypatch):
    def fake_get(db, uid):
        assert uid == "11111111-1111-1111-1111-111111111111"
        return EXAMPLE_USER_MINIMUM
    monkeypatch.setattr(f"{CTRL}.get_user_by_id", fake_get, raising=False)

    r = client_auth_ok.get("/users/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_200_OK
    assert_subset(EXAMPLE_USER_MINIMUM, r.json())

def test_get_user_by_id_not_found(client_auth_ok, monkeypatch):
    def fake_get(db, uid):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.get_user_by_id", fake_get, raising=False)

    r = client_auth_ok.get("/users/99999999-9999-9999-9999-999999999999")
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_get_user_by_id_forbidden(client_forbidden):
    r = client_forbidden.get("/users/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_user_by_id_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/users/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_by_email_success(client_auth_ok, monkeypatch):
    def fake_get(db, email):
        assert email == "alice@example.com"
        return EXAMPLE_USER_MINIMUM
    monkeypatch.setattr(f"{CTRL}.get_user_by_email", fake_get, raising=False)

    r = client_auth_ok.get("/users/email/alice@example.com")
    assert r.status_code == status.HTTP_200_OK
    assert_subset(EXAMPLE_USER_MINIMUM, r.json())

def test_get_user_by_email_not_found(client_auth_ok, monkeypatch):
    def fake_get(db, email):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.get_user_by_email", fake_get, raising=False)

    r = client_auth_ok.get("/users/email/missing@example.com")
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_get_user_by_email_forbidden(client_forbidden):
    r = client_forbidden.get("/users/email/alice@example.com")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_user_by_email_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/users/email/alice@example.com")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_user_success(client_auth_ok, monkeypatch):
    def fake_update(db, uid, data):
        assert uid == "11111111-1111-1111-1111-111111111111"
        return EXAMPLE_USER_MINIMUM_UPDATED
    monkeypatch.setattr(f"{CTRL}.update_user", fake_update, raising=False)

    r = client_auth_ok.put("/users/11111111-1111-1111-1111-111111111111", json=EXAMPLE_USER_UPDATE)
    assert r.status_code == status.HTTP_200_OK
    assert_subset(EXAMPLE_USER_MINIMUM_UPDATED, r.json())

def test_update_user_not_found(client_auth_ok, monkeypatch):
    def fake_update(db, uid, data):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.update_user", fake_update, raising=False)

    r = client_auth_ok.put("/users/99999999-9999-9999-9999-999999999999", json=EXAMPLE_USER_UPDATE)
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_update_user_duplicate(client_auth_ok, monkeypatch):
    def fake_update(db, uid, data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="duplicate email")
    monkeypatch.setattr(f"{CTRL}.update_user", fake_update, raising=False)

    r = client_auth_ok.put("/users/11111111-1111-1111-1111-111111111111", json=EXAMPLE_USER_UPDATE)
    assert r.status_code == status.HTTP_400_BAD_REQUEST

def test_update_user_integrity(client_auth_ok, monkeypatch):
    def fake_update(db, uid, data):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="constraint")
    monkeypatch.setattr(f"{CTRL}.update_user", fake_update, raising=False)

    r = client_auth_ok.put("/users/11111111-1111-1111-1111-111111111111", json=EXAMPLE_USER_UPDATE)
    assert r.status_code == status.HTTP_409_CONFLICT

def test_update_user_forbidden(client_forbidden):
    r = client_forbidden.put("/users/11111111-1111-1111-1111-111111111111", json=EXAMPLE_USER_UPDATE)
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_update_user_unauthorized(client_unauthorized):
    r = client_unauthorized.put("/users/11111111-1111-1111-1111-111111111111", json=EXAMPLE_USER_UPDATE)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_delete_user_success(client_auth_ok, monkeypatch):
    def fake_delete(db, uid):
        assert uid == "11111111-1111-1111-1111-111111111111"
        return EXAMPLE_USER_MINIMUM
    monkeypatch.setattr(f"{CTRL}.delete_user", fake_delete, raising=False)

    r = client_auth_ok.delete("/users/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_200_OK
    assert_subset(EXAMPLE_USER_MINIMUM, r.json())

def test_delete_user_not_found(client_auth_ok, monkeypatch):
    def fake_delete(db, uid):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.delete_user", fake_delete, raising=False)

    r = client_auth_ok.delete("/users/99999999-9999-9999-9999-999999999999")
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_delete_user_forbidden(client_forbidden):
    r = client_forbidden.delete("/users/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_delete_user_unauthorized(client_unauthorized):
    r = client_unauthorized.delete("/users/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_courses_for_student_success(client_auth_ok, monkeypatch):
    def fake_get_courses(db, sid):
        assert isinstance(sid, str) and sid
        return [
            build_course({
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "name": "Algoritmos",
                # force fields FastAPI validates
                "taught_by": "11111111-1111-1111-1111-111111111111",
                "teacher": {"id": "22222222-2222-2222-2222-222222222222"},
            }),
            build_course({
                "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "name": "Estructuras",
                "taught_by": "33333333-3333-3333-3333-333333333333",
                "teacher": {"id": "44444444-4444-4444-4444-444444444444"},
            }),
        ]
    monkeypatch.setattr(f"{CTRL}.get_courses_for_student", fake_get_courses, raising=False)

    r = client_auth_ok.get("/users/student/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 2
    assert data[0]["id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert data[1]["id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    assert "name" in data[0] and "code" in data[0]

def test_get_courses_for_student_invalid_role_error(client_auth_ok, monkeypatch):
    def fake_get_courses(db, sid):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user is not student")
    monkeypatch.setattr(f"{CTRL}.get_courses_for_student", fake_get_courses, raising=False)

    r = client_auth_ok.get("/users/student/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "not student" in r.json()["detail"]

def test_get_courses_for_student_forbidden(client_forbidden):
    r = client_forbidden.get("/users/student/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_courses_for_student_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/users/student/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_courses_for_professor_success(client_auth_ok, monkeypatch):
    def fake_get_courses(db, pid):
        assert isinstance(pid, str) and pid
        return [
            build_course({
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "name": "Algoritmos",
                "taught_by": "55555555-5555-5555-5555-555555555555",
                "teacher": {"id": "66666666-6666-6666-6666-666666666666"},
            }),
            build_course({
                "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "name": "Estructuras",
                "taught_by": "77777777-7777-7777-7777-777777777777",
                "teacher": {"id": "88888888-8888-8888-8888-888888888888"},
            }),
        ]
    monkeypatch.setattr(f"{CTRL}.get_courses_for_professor", fake_get_courses, raising=False)

    r = client_auth_ok.get("/users/professor/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 2
    assert data[0]["id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert data[1]["id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    assert "name" in data[0] and "code" in data[0]

def test_get_courses_for_professor_invalid_role_error(client_auth_ok, monkeypatch):
    def fake_get_courses(db, pid):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user is not professor")
    monkeypatch.setattr(f"{CTRL}.get_courses_for_professor", fake_get_courses, raising=False)

    r = client_auth_ok.get("/users/professor/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "not professor" in r.json()["detail"]

def test_get_courses_for_professor_forbidden(client_forbidden):
    r = client_forbidden.get("/users/professor/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_courses_for_professor_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/users/professor/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
