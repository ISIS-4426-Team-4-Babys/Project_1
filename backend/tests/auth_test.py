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

from schemas.user_schema import LoginRequest, TokenResponse, UserCreate, UserResponse, LoginResponse
from models.user_model import UserRole

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

    # UUID-ish (uuid.UUID or Pydantic UUID types)
    try:
        from pydantic.types import UUID1 as _UUID1, UUID4 as _UUID4  # type: ignore
    except Exception:
        _UUID1 = _UUID4 = ()
    if ann in (uuid.UUID,) or getattr(ann, "__name__", "").upper().startswith("UUID") or ann in (_UUID1, _UUID4):
        return str(uuid.uuid4())

    if ann in (str, typing.Any):
        if name.lower() == "id" or name.endswith("_id"):
            return str(uuid.uuid4())
        if name.lower() == "email":
            return "alice@example.com"
        if name.lower() == "password":
            return "secret"
        if name.lower() == "name":
            return "Alice"
        if name.lower() == "profile_image":
            return ""
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
        # Return a valid enum value
        members = list(ann.__members__.values())
        return members[0]

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

# Request payloads (must be JSON-serializable)
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

def build_user_response(overrides=None):
    base = build_from_model(UserResponse, overrides=overrides or {}, json_safe=False)
    # Ensure role is an Enum (controller accesses user.role.value)
    if isinstance(base.get("role"), str):
        base["role"] = UserRole(base["role"])
    # Construct a Pydantic instance so attribute access works (user.id, user.role.value)
    return UserResponse(**base)

def assert_subset(subset: dict, full: dict):
    for k, v in subset.items():
        if k in full:
            assert full[k] == v, f"Mismatch for key '{k}': {full[k]} != {v}"

@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()
    _override_all_db_dependencies(app, _fake_get_db)

@pytest.fixture
def client_ok():
    # No role deps on /auth/*, but keep DB override
    _override_all_db_dependencies(app, _fake_get_db)
    with TestClient(app) as c:
        yield c

CTRL = "controllers.auth_controller"

# =======================================================
#                 POST /auth/register
# =======================================================

def test_register_success(client_ok, monkeypatch):
    user_out = build_user_response(
        {"id": "11111111-1111-1111-1111-111111111111", "email": "alice@example.com", "name": "Alice", "role": UserRole.student, "profile_image": ""}
    )
    # controller imported name: create_user
    def fake_create_user(db, data):
        # Return dict or model; FastAPI can serialize model. We'll return dict via .model_dump()
        try:
            return user_out.model_dump()
        except Exception:
            return user_out.dict()
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

# =======================================================
#                 POST /auth/login
# =======================================================

def test_login_success(client_ok, monkeypatch):
    # Build a valid user object with Enum role and UUID-ish id
    uid = "11111111-1111-1111-1111-111111111111"
    user_out_model = build_user_response(
        {"id": uid, "email": "alice@example.com", "name": "Alice", "role": UserRole.student, "profile_image": ""}
    )

    def fake_authenticate_user(db, email, password):
        assert email == "alice@example.com"
        assert password == "secret"
        return user_out_model

    def fake_create_access_token(subject: str, extra_claims: dict | None = None):
        # Controller calls with subject=str(user.id) and extra_claims={"role": user.role.value}
        assert subject == uid
        assert extra_claims and extra_claims.get("role") == UserRole.student.value
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
