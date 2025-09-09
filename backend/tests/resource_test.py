# tests/resource_test.py

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

# ------------------------------------------------------------------------------
# 0) Ensure project root import & env vars
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 1) Stub ONLY config.rabbitmq (so imports don't fail)
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 1.5) Stub passlib CryptContext (avoid bcrypt backend)
# ------------------------------------------------------------------------------
import passlib.context as _plctx

class _DummyCryptContext:
    def hash(self, password):  # pretend to hash
        return f"hashed:{password}"
    def verify(self, plain, hashed):
        return hashed in (f"hashed:{plain}", plain)

_plctx.CryptContext = lambda *a, **k: _DummyCryptContext()

# ------------------------------------------------------------------------------
# 2) Import app (and replace any module-level pwd_context if present)
# ------------------------------------------------------------------------------
from main import app

for modname in ("config.security", "services.user_service", "controllers.auth_controller"):
    try:
        mod = __import__(modname, fromlist=["*"])
        if hasattr(mod, "pwd_context"):
            setattr(mod, "pwd_context", _DummyCryptContext())
    except Exception:
        pass

# ------------------------------------------------------------------------------
# 3) Override ANY Depends(get_db) with a safe DummySession
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 4) Role/auth dependency overrides (skip DB deps)
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 5) Schema-aware builders for responses (ResourceResponse)
# ------------------------------------------------------------------------------
from schemas.resource_schema import ResourceResponse

def _pyd_fields(model_cls):
    fields = getattr(model_cls, "model_fields", None)
    if fields is not None:
        return fields, "v2"
    return getattr(model_cls, "__fields__", {}), "v1"

def _choose_for_annotation(ann, name=""):
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)

    # Optional[T]
    if origin is typing.Union and type(None) in args:
        base = [a for a in args if a is not type(None)][0]
        return _choose_for_annotation(base, name)

    # Literal[...] -> first choice
    if origin is typing.Literal:
        return args[0] if args else None

    # Enum -> first member (value if present)
    if isinstance(ann, type) and issubclass(ann, enum.Enum):
        members = list(ann.__members__.values())
        if members:
            m = members[0]
            return m.value if hasattr(m, "value") else m.name

    # UUID / Pydantic UUID types
    try:
        from pydantic.types import UUID1 as _UUID1, UUID4 as _UUID4  # type: ignore
    except Exception:
        _UUID1 = _UUID4 = ()
    if ann in (uuid.UUID,) or getattr(ann, "__name__", "").upper().startswith("UUID") or ann in (_UUID1, _UUID4):
        return "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    # Common primitives
    if ann in (str, typing.Any):
        if name.lower() == "id" or name.endswith("_id"):
            return "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        if name.lower() == "name":
            return "Syllabus"
        if name.lower() == "filepath":
            return "/tmp/upload"
        if name.lower() == "filetype":
            # default; if Enum/Literal it would have matched above
            return "application/octet-stream"
        return "x"

    if ann in (int,):
        if name.lower() in ("size", "total_docs"):
            return 1
        return 0

    if ann in (float,):
        return 0.0

    if ann in (bool,):
        return False

    if ann in (datetime.datetime,):
        # prefer aware datetime
        return datetime.datetime.now(datetime.timezone.utc)

    if ann in (datetime.date,):
        return datetime.date.today()

    # Collections
    if origin in (list, typing.List, typing.Sequence, typing.MutableSequence):
        return []
    if origin in (dict, typing.Dict, typing.Mapping, typing.MutableMapping):
        return {}

    # Nested model: build recursively
    if hasattr(ann, "model_fields") or hasattr(ann, "__fields__"):
        return _build_model_payload(ann)

    # Fallback
    return None

def _build_model_payload(model_cls):
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

        value = _choose_for_annotation(ann, name)
        if value is None and default is not None:
            value = default
        if value is None:
            value = "x" if "id" not in name else "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        data[name] = value

    # Validate via Pydantic then dump
    try:
        inst = model_cls(**data)
        return inst.model_dump() if hasattr(inst, "model_dump") else inst.dict()
    except Exception:
        return data

def build_resource(overrides=None):
    base = _build_model_payload(ResourceResponse)
    if overrides:
        base.update(overrides)
    # Validate after overrides
    try:
        inst = ResourceResponse(**base)
        return inst.model_dump() if hasattr(inst, "model_dump") else inst.dict()
    except Exception:
        return base

def assert_subset(subset: dict, full: dict):
    for k, v in subset.items():
        if k in full:
            assert full[k] == v, f"Mismatch for key '{k}': {full[k]} != {v}"

# ------------------------------------------------------------------------------
# 6) Fixtures
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 7) Patch controller-level symbols the routes actually call
# ------------------------------------------------------------------------------
CTRL = "controllers.resource_controller"

# =======================================================
#   Helper: permissive ResourceCreate for POST tests only
# =======================================================
from pydantic import BaseModel

class _PermissiveResourceCreate(BaseModel):
    name: str
    filetype: typing.Any  # accept anything
    filepath: str
    size: int
    timestamp: datetime.datetime
    consumed_by: typing.Any  # accept anything
    total_docs: int

def _multipart_payload():
    # Send a small binary; content_type can be anything since we patch ResourceCreate
    files = {"file": ("document.bin", b"\x00\x01\x02", "application/octet-stream")}
    data = {
        "name": "Syllabus",
        "consumed_by": "course",  # permissive model will accept this
        "total_docs": "1",        # form-data string; controller casts to int
    }
    return files, data

# =======================================================
#                 POST  /resources/  (create)
# =======================================================

def test_create_resource_success(client_auth_ok, monkeypatch):
    # Patch the ResourceCreate used by the controller to our permissive one
    monkeypatch.setattr(f"{CTRL}.ResourceCreate", _PermissiveResourceCreate, raising=False)

    expected = build_resource({"name": "Syllabus"})
    def fake_create(db, resource_data, file):
        assert file.filename == "document.bin"
        assert resource_data.name == "Syllabus"
        assert isinstance(resource_data.total_docs, int) and resource_data.total_docs == 1
        return expected
    monkeypatch.setattr(f"{CTRL}.create_resource", fake_create, raising=False)

    files, data = _multipart_payload()
    r = client_auth_ok.post("/resources/", files=files, data=data)
    assert r.status_code == status.HTTP_201_CREATED
    body = r.json()
    assert "id" in body
    assert body.get("name") == "Syllabus"

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

# =======================================================
#                  GET  /resources/  (list)
# =======================================================

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

# =======================================================
#              GET  /resources/{resource_id}
# =======================================================

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
