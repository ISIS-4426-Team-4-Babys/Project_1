import uuid

import pytest
from fastapi import HTTPException, status

from schemas.course_schema import CourseCreate, CourseUpdate
from _test_utils import (
    build_from_model,
    build_course,
    build_user_response as _build_user,
    build_agent,
    assert_subset
)


CTRL = "controllers.course_controller"

def build_user(overrides=None):
    return _build_user(overrides)

COURSE_CREATE_PAYLOAD = build_from_model(
    CourseCreate,
    overrides={"name": "Algoritmos", "code": "ISIS-1105"},
    json_safe=True
)
COURSE_UPDATE_PAYLOAD = build_from_model(
    CourseUpdate,
    overrides={"name": "Algoritmos II", "code": "ISIS-2107"},
    json_safe=True
)


def test_create_course_success(client_auth_ok, monkeypatch):
    expected = build_course({"name": "Algoritmos", "code": "ISIS-1105"})
    def fake_create(db, data):
        return expected
    monkeypatch.setattr(f"{CTRL}.create_course", fake_create, raising=False)

    r = client_auth_ok.post("/courses/", json=COURSE_CREATE_PAYLOAD)
    assert r.status_code == status.HTTP_201_CREATED
    resp = r.json()
    assert isinstance(resp, dict)
    assert_subset({"name": "Algoritmos", "code": "ISIS-1105"}, resp)

def test_create_course_duplicate_error(client_auth_ok, monkeypatch):
    def fake_create(db, data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="course already exists")
    monkeypatch.setattr(f"{CTRL}.create_course", fake_create, raising=False)

    r = client_auth_ok.post("/courses/", json=COURSE_CREATE_PAYLOAD)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "exists" in r.json()["detail"]

def test_create_course_integrity_error(client_auth_ok, monkeypatch):
    def fake_create(db, data):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="db constraint")
    monkeypatch.setattr(f"{CTRL}.create_course", fake_create, raising=False)

    r = client_auth_ok.post("/courses/", json=COURSE_CREATE_PAYLOAD)
    assert r.status_code == status.HTTP_409_CONFLICT
    assert "constraint" in r.json()["detail"]

def test_create_course_forbidden(client_forbidden):
    r = client_forbidden.post("/courses/", json=COURSE_CREATE_PAYLOAD)
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_create_course_unauthorized(client_unauthorized):
    r = client_unauthorized.post("/courses/", json=COURSE_CREATE_PAYLOAD)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_courses_success(client_auth_ok, monkeypatch):
    item = build_course({"name": "Algoritmos", "code": "ISIS-1105"})
    def fake_get_courses(db):
        return [item]
    monkeypatch.setattr(f"{CTRL}.get_courses", fake_get_courses, raising=False)

    r = client_auth_ok.get("/courses/")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1
    assert_subset({"name": "Algoritmos", "code": "ISIS-1105"}, data[0])

def test_get_courses_forbidden(client_forbidden):
    r = client_forbidden.get("/courses/")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_courses_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/courses/")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_course_by_id_success(client_auth_ok, monkeypatch):
    cid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    item = build_course({"id": cid, "name": "Algoritmos"})
    def fake_get(db, course_id):
        assert course_id == cid
        return item
    monkeypatch.setattr(f"{CTRL}.get_course_by_id", fake_get, raising=False)

    r = client_auth_ok.get(f"/courses/{cid}")
    assert r.status_code == status.HTTP_200_OK
    assert_subset({"id": cid, "name": "Algoritmos"}, r.json())

def test_get_course_by_id_not_found(client_auth_ok, monkeypatch):
    def fake_get(db, course_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.get_course_by_id", fake_get, raising=False)

    r = client_auth_ok.get("/courses/ffffffff-ffff-ffff-ffff-ffffffffffff")
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_get_course_by_id_forbidden(client_forbidden):
    r = client_forbidden.get("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_course_by_id_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_update_course_success(client_auth_ok, monkeypatch):
    cid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    updated = build_course({"id": cid, "name": "Algoritmos II", "code": "ISIS-2107"})
    def fake_update(db, course_id, data):
        assert course_id == cid
        return updated
    monkeypatch.setattr(f"{CTRL}.update_course", fake_update, raising=False)

    r = client_auth_ok.put(f"/courses/{cid}", json=COURSE_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_200_OK
    assert_subset({"id": cid, "name": "Algoritmos II", "code": "ISIS-2107"}, r.json())

def test_update_course_not_found(client_auth_ok, monkeypatch):
    def fake_update(db, course_id, data):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.update_course", fake_update, raising=False)

    r = client_auth_ok.put("/courses/ffffffff-ffff-ffff-ffff-ffffffffffff", json=COURSE_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_update_course_duplicate(client_auth_ok, monkeypatch):
    def fake_update(db, course_id, data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="duplicate code")
    monkeypatch.setattr(f"{CTRL}.update_course", fake_update, raising=False)

    r = client_auth_ok.put("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", json=COURSE_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_400_BAD_REQUEST

def test_update_course_integrity(client_auth_ok, monkeypatch):
    def fake_update(db, course_id, data):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="constraint")
    monkeypatch.setattr(f"{CTRL}.update_course", fake_update, raising=False)

    r = client_auth_ok.put("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", json=COURSE_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_409_CONFLICT

def test_update_course_forbidden(client_forbidden):
    r = client_forbidden.put("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", json=COURSE_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_update_course_unauthorized(client_unauthorized):
    r = client_unauthorized.put("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", json=COURSE_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_delete_course_success(client_auth_ok, monkeypatch):
    cid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    item = build_course({"id": cid, "name": "Algoritmos"})
    def fake_delete(db, course_id):
        assert course_id == cid
        return item
    monkeypatch.setattr(f"{CTRL}.delete_course", fake_delete, raising=False)

    r = client_auth_ok.delete(f"/courses/{cid}")
    assert r.status_code == status.HTTP_200_OK
    assert_subset({"id": cid, "name": "Algoritmos"}, r.json())

def test_delete_course_not_found(client_auth_ok, monkeypatch):
    def fake_delete(db, course_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.delete_course", fake_delete, raising=False)

    r = client_auth_ok.delete("/courses/ffffffff-ffff-ffff-ffff-ffffffffffff")
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_delete_course_forbidden(client_forbidden):
    r = client_forbidden.delete("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_delete_course_unauthorized(client_unauthorized):
    r = client_unauthorized.delete("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_enroll_student_success(client_auth_ok, monkeypatch):
    cid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    sid = "11111111-1111-1111-1111-111111111111"
    item = build_course({"id": cid})
    def fake_enroll(db, course_id, student_id):
        assert course_id == cid and student_id == sid
        return item
    monkeypatch.setattr(f"{CTRL}.enroll_student", fake_enroll, raising=False)

    r = client_auth_ok.post(f"/courses/{cid}/students/{sid}")
    assert r.status_code == status.HTTP_200_OK
    assert r.json().get("id") == cid

def test_enroll_student_invalid_role(client_auth_ok, monkeypatch):
    def fake_enroll(db, course_id, student_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user is not student")
    monkeypatch.setattr(f"{CTRL}.enroll_student", fake_enroll, raising=False)

    r = client_auth_ok.post("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "not student" in r.json()["detail"]

def test_enroll_student_forbidden(client_forbidden):
    r = client_forbidden.post("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_enroll_student_unauthorized(client_unauthorized):
    r = client_unauthorized.post("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_unenroll_student_success(client_auth_ok, monkeypatch):
    cid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    sid = "11111111-1111-1111-1111-111111111111"
    item = build_course({"id": cid})
    def fake_unenroll(db, course_id, student_id):
        assert course_id == cid and student_id == sid
        return item
    monkeypatch.setattr(f"{CTRL}.unenroll_student", fake_unenroll, raising=False)

    r = client_auth_ok.delete(f"/courses/{cid}/students/{sid}")
    assert r.status_code == status.HTTP_200_OK
    assert r.json().get("id") == cid

def test_unenroll_student_invalid_role(client_auth_ok, monkeypatch):
    def fake_unenroll(db, course_id, student_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user is not student")
    monkeypatch.setattr(f"{CTRL}.unenroll_student", fake_unenroll, raising=False)

    r = client_auth_ok.delete("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "not student" in r.json()["detail"]

def test_unenroll_student_forbidden(client_forbidden):
    r = client_forbidden.delete("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_unenroll_student_unauthorized(client_unauthorized):
    r = client_unauthorized.delete("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students/11111111-1111-1111-1111-111111111111")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_students_in_course_success(client_auth_ok, monkeypatch):
    u1 = str(uuid.uuid4())
    u2 = str(uuid.uuid4())
    def fake_get_students(db, course_id):
        return [build_user({"id": u1}), build_user({"id": u2})]
    monkeypatch.setattr(f"{CTRL}.get_students_in_course", fake_get_students, raising=False)

    r = client_auth_ok.get("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 2
    assert data[0].get("id") == u1
    assert data[1].get("id") == u2

def test_get_students_in_course_forbidden(client_forbidden):
    r = client_forbidden.get("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_students_in_course_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/students")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_agents_in_course_success(client_auth_ok, monkeypatch):
    a1 = str(uuid.uuid4())
    a2 = str(uuid.uuid4())
    def fake_get_agents(db, course_id):
        return [build_agent({"id": a1}), build_agent({"id": a2})]
    monkeypatch.setattr(f"{CTRL}.get_agents_in_course", fake_get_agents, raising=False)

    r = client_auth_ok.get("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/agents")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 2
    assert data[0].get("id") == a1
    assert data[1].get("id") == a2

def test_get_agents_in_course_forbidden(client_forbidden):
    r = client_forbidden.get("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/agents")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_agents_in_course_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/courses/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/agents")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
