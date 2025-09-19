import uuid

from fastapi import HTTPException, status

from schemas.agent_schema import AgentCreate, AgentUpdate

from _test_utils import (
    build_from_model,
    build_agent,
    build_resource,
    assert_subset
)

CTRL = "controllers.agent_controller"


AGENT_CREATE_PAYLOAD = build_from_model(
    AgentCreate,
    overrides={"name": "TA Bot", "description": "desc"},
    json_safe=True,
)
AGENT_UPDATE_PAYLOAD = build_from_model(
    AgentUpdate,
    overrides={"name": "TA Bot 2", "description": "desc2"},
    json_safe=True,
)



#def test_create_agent_success(client_auth_ok, monkeypatch):
#    expected = build_agent({"name": "TA Bot"})
#    def fake_create(db, data):
#        return expected
#    monkeypatch.setattr(f"{CTRL}.create_agent", fake_create, raising=False)
#
#    r = client_auth_ok.post("/agents/", json=AGENT_CREATE_PAYLOAD)
#    assert r.status_code == status.HTTP_201_CREATED
#    assert "id" in r.json()
#    assert r.json().get("name") == "TA Bot"

def test_create_agent_integrity_error(client_auth_ok, monkeypatch):
    def fake_create(db, data):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="db constraint")
    monkeypatch.setattr(f"{CTRL}.create_agent", fake_create, raising=False)

    r = client_auth_ok.post("/agents/", json=AGENT_CREATE_PAYLOAD)
    assert r.status_code == status.HTTP_409_CONFLICT
    assert "constraint" in r.json()["detail"]

def test_create_agent_forbidden(client_forbidden):
    r = client_forbidden.post("/agents/", json=AGENT_CREATE_PAYLOAD)
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_create_agent_unauthorized(client_unauthorized):
    r = client_unauthorized.post("/agents/", json=AGENT_CREATE_PAYLOAD)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_agents_success(client_auth_ok, monkeypatch):
    item = build_agent({"name": "TA Bot"})
    def fake_get_agents(db):
        return [item]
    monkeypatch.setattr(f"{CTRL}.get_agents", fake_get_agents, raising=False)

    r = client_auth_ok.get("/agents/")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1
    assert_subset({"name": "TA Bot"}, data[0])

def test_get_agents_forbidden(client_forbidden):
    r = client_forbidden.get("/agents/")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_agents_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/agents/")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_agent_by_id_success(client_auth_ok, monkeypatch):
    aid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    item = build_agent({"id": aid, "name": "TA Bot"})
    def fake_get(db, agent_id):
        assert agent_id == aid
        return item
    monkeypatch.setattr(f"{CTRL}.get_agent_by_id", fake_get, raising=False)

    r = client_auth_ok.get(f"/agents/{aid}")
    assert r.status_code == status.HTTP_200_OK
    assert_subset({"id": aid, "name": "TA Bot"}, r.json())

def test_get_agent_by_id_not_found(client_auth_ok, monkeypatch):
    def fake_get(db, agent_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.get_agent_by_id", fake_get, raising=False)

    r = client_auth_ok.get("/agents/ffffffff-ffff-ffff-ffff-ffffffffffff")
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_get_agent_by_id_forbidden(client_forbidden):
    r = client_forbidden.get("/agents/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_agent_by_id_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/agents/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_update_agent_success(client_auth_ok, monkeypatch):
    aid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    updated = build_agent({"id": aid, "name": "TA Bot 2"})
    def fake_update(db, agent_id, data):
        assert agent_id == aid
        return updated
    monkeypatch.setattr(f"{CTRL}.update_agent", fake_update, raising=False)

    r = client_auth_ok.put(f"/agents/{aid}", json=AGENT_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_200_OK
    assert_subset({"id": aid, "name": "TA Bot 2"}, r.json())

def test_update_agent_not_found(client_auth_ok, monkeypatch):
    def fake_update(db, agent_id, data):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    monkeypatch.setattr(f"{CTRL}.update_agent", fake_update, raising=False)

    r = client_auth_ok.put("/agents/ffffffff-ffff-ffff-ffff-ffffffffffff", json=AGENT_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_404_NOT_FOUND

def test_update_agent_integrity(client_auth_ok, monkeypatch):
    def fake_update(db, agent_id, data):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="constraint")
    monkeypatch.setattr(f"{CTRL}.update_agent", fake_update, raising=False)

    r = client_auth_ok.put("/agents/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", json=AGENT_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_409_CONFLICT

def test_update_agent_forbidden(client_forbidden):
    r = client_forbidden.put("/agents/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", json=AGENT_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_update_agent_unauthorized(client_unauthorized):
    r = client_unauthorized.put("/agents/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", json=AGENT_UPDATE_PAYLOAD)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_resources_for_agent_success(client_auth_ok, monkeypatch):
    rid1 = str(uuid.uuid4())
    rid2 = str(uuid.uuid4())
    def fake_get_resources(db, agent_id):
        return [
            build_resource({"id": rid1, "name": "Syllabus"}),
            build_resource({"id": rid2, "name": "Slides"}),
        ]
    monkeypatch.setattr(f"{CTRL}.get_resources_for_agent", fake_get_resources, raising=False)

    r = client_auth_ok.get("/agents/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/resources")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 2
    assert data[0].get("id") == rid1
    assert data[1].get("id") == rid2

def test_get_resources_for_agent_forbidden(client_forbidden):
    r = client_forbidden.get("/agents/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/resources")
    assert r.status_code == status.HTTP_403_FORBIDDEN

def test_get_resources_for_agent_unauthorized(client_unauthorized):
    r = client_unauthorized.get("/agents/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/resources")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
