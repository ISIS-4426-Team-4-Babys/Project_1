import os
import sys
import types
import pathlib
import uuid
import datetime
import typing
import enum

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

ROOT = pathlib.Path(__file__).resolve().parent.parent  # backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DB_DIALECT", "postgresql")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRATION_MINUTES", "60")
os.environ.setdefault("JWT_REFRESH_EXPIRATION_MINUTES", "1440")

try:
    import config as _config
except ModuleNotFoundError:
    _config = types.ModuleType("config")
    _config.__path__ = [str(ROOT / "config")]
    sys.modules["config"] = _config

if "config.rabbitmq" not in sys.modules:
    rabbit_mod = types.ModuleType("config.rabbitmq")

    class DummyRabbitMQ:
        def __init__(self, *a, **k): ...
        def publish(self, *a, **k): ...
        def consume(self, *a, **k): ...
        def close(self): ...

    rabbit_mod.RabbitMQ = DummyRabbitMQ
    sys.modules["config.rabbitmq"] = rabbit_mod
    setattr(_config, "rabbitmq", rabbit_mod)

import passlib.context as _plctx

class _DummyCryptContext:
    def hash(self, password):  # pretend to hash
        return f"hashed:{password}"
    def verify(self, plain, hashed):
        return hashed in (f"hashed:{plain}", plain)

_plctx.CryptContext = lambda *a, **k: _DummyCryptContext()

from main import app

for modname in ("config.security", "services.user_service", "controllers.auth_controller"):
    try:
        mod = __import__(modname, fromlist=["*"])
        if hasattr(mod, "pwd_context"):
            setattr(mod, "pwd_context", _DummyCryptContext())
    except Exception:
        pass

class DummySession:
    def __init__(self):
        self._closed = False
    # ORM-like chainables
    def query(self, *a, **k): return self
    def filter(self, *a, **k): return self
    def filter_by(self, *a, **k): return self
    def join(self, *a, **k): return self
    def options(self, *a, **k): return self
    # terminals
    def all(self): return []
    def first(self): return None
    def one(self): raise Exception("No row")
    def one_or_none(self): return None
    def get(self, *a, **k): return None
    # uow
    def add(self, *a, **k): pass
    def add_all(self, *a, **k): pass
    def delete(self, *a, **k): pass
    def commit(self): pass
    def rollback(self): pass
    def refresh(self, *a, **k): pass
    # 1.4/2.x execute
    def execute(self, *a, **k):
        from unittest.mock import MagicMock
        m = MagicMock()
        m.scalars.return_value = []
        m.first.return_value = None
        return m
    def close(self): self._closed = True

def _fake_get_db():
    db = DummySession()
    try:
        yield db
    finally:
        db.close()

def _override_all_db_dependencies(app_, fake_dep_gen):
    seen = set()
    def visit(dependant):
        for dep in getattr(dependant, "dependencies", []) or []:
            fn = getattr(dep, "call", None)
            if fn and fn not in seen:
                name = getattr(fn, "__name__", "")
                mod = getattr(fn, "__module__", "")
                if name == "get_db" or mod.endswith("config.database"):
                    app_.dependency_overrides[fn] = fake_dep_gen
                seen.add(fn)
            if getattr(dep, "dependant", None):
                visit(dep.dependant)
    for route in app_.routes:
        dep = getattr(route, "dependant", None)
        if dep:
            visit(dep)

_override_all_db_dependencies(app, _fake_get_db)

def _noop_auth_dependency():
    return None

def _forbidden_auth_dependency():
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

def _unauthorized_auth_dependency():
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

def _override_all_role_dependencies(dep_func):
    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if not dependant:
            continue
        for dep in dependant.dependencies:
            fn = getattr(dep, "call", None)
            if not fn:
                continue
            name = getattr(fn, "__name__", "")
            mod = getattr(fn, "__module__", "") or ""
            if name == "get_db" or mod.endswith("config.database"):
                continue
            app.dependency_overrides[fn] = dep_func


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()
    _override_all_db_dependencies(app, _fake_get_db)

@pytest.fixture
def client_auth_ok():
    _override_all_role_dependencies(_noop_auth_dependency)
    _override_all_db_dependencies(app, _fake_get_db)
    with TestClient(app) as c:
        yield c

@pytest.fixture
def client_forbidden():
    _override_all_role_dependencies(_forbidden_auth_dependency)
    _override_all_db_dependencies(app, _fake_get_db)
    with TestClient(app) as c:
        yield c

@pytest.fixture
def client_unauthorized():
    _override_all_role_dependencies(_unauthorized_auth_dependency)
    _override_all_db_dependencies(app, _fake_get_db)
    with TestClient(app) as c:
        yield c

from schemas.course_schema import CourseCreate, CourseUpdate, CourseResponse
from schemas.user_schema import UserResponse
from schemas.agent_schema import AgentResponse

def jsonify(obj):
    """Convert UUID/datetime/date/Enum recursively to JSON-serializable values."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, enum.Enum):
        return obj.value if hasattr(obj, "value") else obj.name
    if isinstance(obj, list):
        return [jsonify(x) for x in obj]
    if isinstance(obj, dict):
        return {k: jsonify(v) for k, v in obj.items()}
    return obj

def _is_optional(ann):
    origin = typing.get_origin(ann)
    return origin is typing.Union and type(None) in typing.get_args(ann)

def _dummy_for_type(ann, name=""):
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)

    if _is_optional(ann):
        base = [a for a in args if a is not type(None)][0]
        return _dummy_for_type(base, name)

    # UUID-ish: uuid.UUID or pydantic UUID4/UUID1
    try:
        import uuid as _uuid
        from pydantic.types import UUID1 as _UUID1, UUID4 as _UUID4  # type: ignore
    except Exception:
        _UUID1 = _UUID4 = ()
        import uuid as _uuid
    if ann in (uuid.UUID,) or getattr(ann, "__name__", "").upper().startswith("UUID") or ann in (_UUID1, _UUID4):
        return str(uuid.uuid4())

    if ann in (str, typing.Any):
        if name.lower() == "id" or name.endswith("_id"):
            return str(uuid.uuid4())
        if name.lower() == "name": return "Algoritmos"
        if name.lower() == "code": return "ISIS-1105"
        if name.lower() in ("department", "faculty"): return "Ingeniería de Sistemas y Computación"
        if name.lower() == "description": return "desc"
        return "x"

    if ann in (int,):
        return 0
    if ann in (float,):
        return 0.0
    if ann in (bool,):
        return False

    if ann in (datetime.datetime,):
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    if ann in (datetime.date,):
        return datetime.date.today().isoformat()

    if origin in (list, typing.List, typing.Sequence, typing.MutableSequence):
        return []
    if origin in (dict, typing.Dict, typing.Mapping, typing.MutableMapping):
        return {}

    if isinstance(ann, type) and issubclass(ann, enum.Enum):
        members = list(ann.__members__.values())
        return members[0].value if hasattr(members[0], "value") else members[0].name

    # Nested Pydantic model
    if hasattr(ann, "model_fields") or hasattr(ann, "__fields__"):
        return _build_model_dict(ann)

    return None

def _pyd_fields(model_cls):
    fields = getattr(model_cls, "model_fields", None)
    if fields is not None:
        return fields, "v2"
    return getattr(model_cls, "__fields__", {}), "v1"

def _build_model_dict(model_cls):
    fields, mode = _pyd_fields(model_cls)
    data = {}
    for name, field in fields.items():
        if mode == "v1":
            required = field.required
            ann = field.type_
            default = field.default if field.default is not None else (field.default_factory() if field.default_factory else None)
        else:
            required = field.is_required()
            ann = field.annotation
            default = field.default if field.default is not None else (field.default_factory() if field.default_factory is not None else None)

        if not required:
            continue

        value = _dummy_for_type(ann, name)
        if value is None and default is not None:
            value = default
        if value is None:
            value = "x" if "id" not in name else str(uuid.uuid4())
        data[name] = value

    # Validate once via model, then dump to a plain dict
    try:
        inst = model_cls(**data)
        payload = inst.model_dump() if hasattr(inst, "model_dump") else inst.dict()
    except Exception:
        payload = data
    return payload

def build_from_model(model_cls, overrides=None, json_safe=False):
    base = _build_model_dict(model_cls)
    if overrides:
        base.update(overrides)
    return jsonify(base) if json_safe else base

# Convenience builders for responses (responses can safely contain UUIDs)
def build_course(overrides=None): return build_from_model(CourseResponse, overrides, json_safe=False)
def build_user(overrides=None):   return build_from_model(UserResponse, overrides, json_safe=False)
def build_agent(overrides=None):  return build_from_model(AgentResponse, overrides, json_safe=False)

# Request payloads MUST be JSON-serializable
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

def assert_subset(subset: dict, full: dict):
    for k, v in subset.items():
        if k in full:
            assert full[k] == v, f"Mismatch for key '{k}': {full[k]} != {v}"

CTRL = "controllers.course_controller"

# =======================================================
#                 CREATE  /courses/  (POST)
# =======================================================

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

# =======================================================
#                  GET  /courses/  (GET)
# =======================================================

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

# =======================================================
#              GET  /courses/{course_id}  (GET)
# =======================================================

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

# =======================================================
#             PUT  /courses/{course_id}  (PUT)
# =======================================================

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

# =======================================================
#            DELETE  /courses/{course_id}  (DELETE)
# =======================================================

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

# =======================================================
#   POST  /courses/{course_id}/students/{student_id}  (enroll)
# =======================================================

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

# =======================================================
#   DELETE  /courses/{course_id}/students/{student_id}  (unenroll)
# =======================================================

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

# =======================================================
#   GET  /courses/{course_id}/students  (list[UserResponse])
# =======================================================

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

# =======================================================
#   GET  /courses/{course_id}/agents  (list[AgentResponse])
# =======================================================

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
