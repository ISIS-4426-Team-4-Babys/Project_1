import os
import sys
import types
import pathlib
import uuid
import datetime
import typing

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
import pydantic

PYDANTIC_V2 = hasattr(pydantic.BaseModel, "model_validate") 

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

def assert_subset(subset: dict, full: dict):
    """Assert every key/value in subset appears identical in full."""
    for k, v in subset.items():
        assert k in full, f"Missing key '{k}' in response"
        assert full[k] == v, f"Mismatch for key '{k}': {full[k]} != {v}"

try:
    from schemas.course_schema import CourseResponse  
except Exception:
    CourseResponse = None  
    
def _is_optional(ann):
    origin = typing.get_origin(ann)
    if origin is typing.Union:
        args = typing.get_args(ann)
        return type(None) in args
    return False

def _dummy_for_type(ann, name=""):
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)

    # Optionals -> base type
    if _is_optional(ann):
        base = [a for a in args if a is not type(None)][0]
        return _dummy_for_type(base, name)

    # Simple builtins / pydantic-friendly types
    if ann in (str, typing.Any):
        if name.lower() in ("id",) or name.endswith("_id"):
            return str(uuid.uuid4())
        return "x"
    if ann in (int,):
        return 0
    if ann in (float,):
        return 0.0
    if ann in (bool,):
        return False

    # UUID-like
    try:
        import uuid as _uuid
        if ann in (_uuid.UUID,):
            return str(uuid.uuid4())
    except Exception:
        pass

    # datetime-like
    try:
        import datetime as _dt
        if ann in (_dt.datetime,):
            return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        if ann in (_dt.date,):
            return datetime.date.today().isoformat()
    except Exception:
        pass

    # List[...] / Sequence[...]
    if origin in (list, typing.List, typing.Sequence, typing.MutableSequence):
        return []

    # Dict[...] / Mapping[...]
    if origin in (dict, typing.Dict, typing.Mapping, typing.MutableMapping):
        return {}

    # Enum -> pick first member
    try:
        import enum
        if isinstance(ann, type) and issubclass(ann, enum.Enum):
            return list(ann.__members__.values())[0]
    except Exception:
        pass

    # Nested Pydantic model
    try:
        if (not PYDANTIC_V2 and hasattr(ann, "__fields__")) or hasattr(ann, "model_fields"):
            return _build_model_dict(ann)
    except Exception:
        pass

    # Fallback
    return None

def _build_model_dict(model_cls):
    """Create a dict satisfying required fields of a Pydantic model (v1/v2)."""
    fields = getattr(model_cls, "model_fields", None)  # pydantic v2
    v1 = False
    if fields is None:
        fields = getattr(model_cls, "__fields__", {})
        v1 = True

    data = {}
    for name, field in fields.items():
        # Determine "required"
        if v1:
            required = field.required
            ann = field.type_
            default = field.default if field.default is not None else field.default_factory() if field.default_factory else None
        else:
            required = field.is_required()
            ann = field.annotation
            default = field.default if field.default is not None else (field.default_factory() if field.default_factory is not None else None)

        if not required:
            # if has default, skip; pydantic will fill it
            continue

        data[name] = _dummy_for_type(ann, name=name)
        # If dummy is None but default exists, use default
        if data[name] is None and default is not None:
            data[name] = default

        # Last resort: simple string
        if data[name] is None:
            data[name] = "x" if "id" not in name else str(uuid.uuid4())

    # Validate by constructing the model and dumping to primitive dict
    try:
        inst = model_cls(**data)
        try:
            return inst.model_dump()
        except Exception:
            return inst.dict()
    except Exception:
        # If construction fails due to hidden requireds, try forgiving dump
        try:
            inst = model_cls.construct(**data)  # type: ignore[attr-defined]
            try:
                return inst.model_dump()
            except Exception:
                return inst.dict()
        except Exception:
            return data  # best effort

def build_course(overrides: dict | None = None) -> dict:
    """Return a dict that satisfies CourseResponse, with optional overrides."""
    base = _build_model_dict(CourseResponse) if CourseResponse else {}
    # Provide sensible common defaults if the schema has these fields
    sensible = {
        "id": str(uuid.uuid4()),
        "name": "Algoritmos",
        "code": "ISIS-1105",
        "department": "Ingeniería de Sistemas y Computación",
        "description": "desc",
    }
    for k, v in sensible.items():
        if k in getattr(CourseResponse, "model_fields", {}) or k in getattr(CourseResponse, "__fields__", {}):
            base.setdefault(k, v)
    if overrides:
        base.update(overrides)
    return base

CTRL = "controllers.user_controller"

# =======================================================
#                 CREATE  /users/  (POST)
# =======================================================

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

# =======================================================
#                  GET  /users/  (GET)
# =======================================================

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

# =======================================================
#              GET  /users/{user_id}  (GET)
# =======================================================

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

# =======================================================
#           GET  /users/email/{email}  (GET)
# =======================================================

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

# =======================================================
#             PUT  /users/{user_id}  (PUT)
# =======================================================

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

# =======================================================
#            DELETE  /users/{user_id}  (DELETE)
# =======================================================

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

# =======================================================
#   GET  /users/student/{student_id}  (GET)
# =======================================================

def test_get_courses_for_student_success(client_auth_ok, monkeypatch):
    def fake_get_courses(db, sid):
        assert isinstance(sid, str) and len(sid) > 0
        return [build_course({"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "name": "Algoritmos"}),
                build_course({"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "name": "Estructuras"})]
    monkeypatch.setattr(f"{CTRL}.get_courses_for_student", fake_get_courses, raising=False)

    r = client_auth_ok.get("/users/student/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 2
    # spot-check minimal fields likely present
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

# =======================================================
#   GET  /users/professor/{professor_id}  (GET)
# =======================================================

def test_get_courses_for_professor_success(client_auth_ok, monkeypatch):
    def fake_get_courses(db, pid):
        assert isinstance(pid, str) and len(pid) > 0
        return [build_course({"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "name": "Algoritmos"}),
                build_course({"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "name": "Estructuras"})]
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
