import typing
import datetime
import enum
import uuid

import pytest
from fastapi import HTTPException, status
from pydantic import BaseModel

from _test_utils import build_resource, assert_subset

CTRL = "controllers.resource_controller"

class _PermissiveResourceCreate(BaseModel):
    name: str
    filetype: typing.Any
    filepath: str
    size: int
    timestamp: datetime.datetime
    consumed_by: typing.Any
    total_docs: int

def _multipart_payload():
    files = {"file": ("document.bin", b"\x00\x01\x02", "application/octet-stream")}
    data = {
        "name": "Syllabus",
        "consumed_by": "course",
        "total_docs": "1",
    }
    return files, data


#def test_create_resource_success(client_auth_ok, monkeypatch):
#    monkeypatch.setattr(f"{CTRL}.ResourceCreate", _PermissiveResourceCreate, raising=False)
#    expected = build_resource({"name": "Syllabus"})
#    def fake_create(db, resource_data, file):
#        assert file.filename == "document.bin"
#        assert resource_data.name == "Syllabus"
#        assert isinstance(resource_data.total_docs, int) and resource_data.total_docs == 1
#        return expected
#    monkeypatch.setattr(f"{CTRL}.create_resource", fake_create, raising=False)
#
#    files, data = _multipart_payload()
#    r = client_auth_ok.post("/resources/", files=files, data=data)
#    assert r.status_code == status.HTTP_201_CREATED
#    body = r.json()
#    assert "id" in body
#    assert body.get("name") == "Syllabus"

def test_create_resource_duplicate(client_auth_ok, monkeypatch):
    monkeypatch.setattr(f"{CTRL}.ResourceCreate", _PermissiveResourceCreate, raising=False)
    def fake_create(db, resource_data, file):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="resource already exists")
    monkeypatch.setattr(f"{CTRL}.create_resource", fake_create, raising=False)

    files, data = _multipart_payload()
    r = client_auth_ok.post("/resources/", files=files, data=data)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "exists" in r.json()["detail"]

def test_create_resource_file_size_error(client_auth_ok, monkeypatch):
    monkeypatch.setattr(f"{CTRL}.ResourceCreate", _PermissiveResourceCreate, raising=False)
    def fake_create(db, resource_data, file):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file too large")
    monkeypatch.setattr(f"{CTRL}.create_resource", fake_create, raising=False)

    files, data = _multipart_payload()
    r = client_auth_ok.post("/resources/", files=files, data=data)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "large" in r.json()["detail"].lower()

def test_create_resource_integrity_error(client_auth_ok, monkeypatch):
    monkeypatch.setattr(f"{CTRL}.ResourceCreate", _PermissiveResourceCreate, raising=False)
    def fake_create(db, resource_data, file):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="db constraint")
    monkeypatch.setattr(f"{CTRL}.create_resource", fake_create, raising=False)

    files, data = _multipart_payload()
    r = client_auth_ok.post("/resources/", files=files, data=data)
    assert r.status_code == status.HTTP_409_CONFLICT
    assert "constraint" in r.json()["detail"]

def test_create_resource_forbidden(client_forbidden):
    files, data = _multipart_payload()
    r = client_forbidden.post("/resources/", files=files, data=data)
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_create_resource_unauthorized(client_unauthorized):
    files, data = _multipart_payload()
    r = client_unauthorized.post("/resources/", files=files, data=data)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_resources_success(client_auth_ok, monkeypatch):
    a = build_resource({"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "name": "Syllabus"})
    b = build_resource({"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "name": "Slides"})
    def fake_get_resources(db):
        return [a, b]
    monkeypatch.setattr(f"{CTRL}.get_resources", fake_get_resources, raising=False)

    r = client_auth_ok.get("/resources/")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 2
    assert data[0]["id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert data[1]["id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

def test_get_resources_forbidden(client_forbidden):
    r = client_forbidden.get("/resources/")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_resources_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/resources/")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_resource_by_id_success(client_auth_ok, monkeypatch):
    rid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    item = build_resource({"id": rid, "name": "Syllabus"})
    def fake_get(db, resource_id):
        assert resource_id == rid
        return item
    monkeypatch.setattr(f"{CTRL}.get_resource_by_id", fake_get, raising=False)

    r = client_auth_ok.get(f"/resources/{rid}")
    assert r.status_code == status.HTTP_200_OK
    body = r.json()
    assert body.get("id") == rid
    assert body.get("name") == "Syllabus"

def test_get_resource_by_id_not_found(client_auth_ok, monkeypatch):
    def fake_get(db, resource_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.get_resource_by_id", fake_get, raising=False)

    r = client_auth_ok.get("/resources/ffffffff-ffff-ffff-ffff-ffffffffffff")
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_get_resource_by_id_forbidden(client_forbidden):
    r = client_forbidden.get("/resources/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_resource_by_id_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/resources/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
