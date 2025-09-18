import os
import sys
import types
import pathlib

import pytest
from fastapi.testclient import TestClient

# -----------------------------------------------------
# Paths
# -----------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parent.parent  # backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -----------------------------------------------------
# Environment defaults for testing
# -----------------------------------------------------
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

# -----------------------------------------------------
# Create a lightweight 'config' package & stub rabbitmq
# -----------------------------------------------------
try:
    import config as _config  # noqa: F401
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

# -----------------------------------------------------
# Stub passlib CryptContext BEFORE importing app
# -----------------------------------------------------
import passlib.context as _plctx  # type: ignore

class _DummyCryptContext:
    def hash(self, password):  # pretend to hash
        return f"hashed:{password}"
    def verify(self, plain, hashed):
        return hashed in (f"hashed:{plain}", plain)

_plctx.CryptContext = lambda *a, **k: _DummyCryptContext()

# -----------------------------------------------------
# Import app and patch modules that keep a global pwd_context
# -----------------------------------------------------
from main import app  # noqa: E402

for modname in ("config.security", "services.user_service", "controllers.auth_controller"):
    try:
        mod = __import__(modname, fromlist=["*"])
        if hasattr(mod, "pwd_context"):
            setattr(mod, "pwd_context", _DummyCryptContext())
    except Exception:
        pass

# -----------------------------------------------------
# DB dummy session + dependency override walker
# -----------------------------------------------------
class DummySession:
    def __init__(self):
        self._closed = False
    def query(self, *a, **k): return self
    def filter(self, *a, **k): return self
    def filter_by(self, *a, **k): return self
    def join(self, *a, **k): return self
    def options(self, *a, **k): return self
    def all(self): return []
    def first(self): return None
    def one(self): raise Exception("No row")
    def one_or_none(self): return None
    def get(self, *a, **k): return None
    def add(self, *a, **k): pass
    def add_all(self, *a, **k): pass
    def delete(self, *a, **k): pass
    def commit(self): pass
    def rollback(self): pass
    def refresh(self, *a, **k): pass
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

def override_all_db_dependencies(app_, fake_dep_gen):
    """Walk the dependency graph and override any get_db-like dep."""
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

override_all_db_dependencies(app, _fake_get_db)

# -----------------------------------------------------
# Auth role dependency helpers
# -----------------------------------------------------
from fastapi import HTTPException, status

def _noop_auth_dependency():
    return None

def _forbidden_auth_dependency():
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

def _unauthorized_auth_dependency():
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

def override_all_role_dependencies(dep_func):
    """Replace *non-DB* security/role dependencies across routes."""
    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if not dependant:
            continue
        for dep in getattr(dependant, "dependencies", []) or []:
            fn = getattr(dep, "call", None)
            if not fn:
                continue
            name = getattr(fn, "__name__", "")
            mod = getattr(fn, "__module__", "") or ""
            if name == "get_db" or mod.endswith("config.database"):
                continue
            app.dependency_overrides[fn] = dep_func

# -----------------------------------------------------
# Pytest fixtures available to all tests
# -----------------------------------------------------
@pytest.fixture(autouse=True)
def clear_overrides():
    """Ensure a clean overrides map per test and keep DB stubbed."""
    yield
    app.dependency_overrides.clear()
    override_all_db_dependencies(app, _fake_get_db)

@pytest.fixture
def client_ok():
    """DB stubbed; no role deps changed (useful for /auth/*)."""
    override_all_db_dependencies(app, _fake_get_db)
    with TestClient(app) as c:
        yield c

@pytest.fixture
def client_auth_ok():
    """DB stubbed; allow passing auth deps."""
    override_all_role_dependencies(_noop_auth_dependency)
    override_all_db_dependencies(app, _fake_get_db)
    with TestClient(app) as c:
        yield c

@pytest.fixture
def client_forbidden():
    override_all_role_dependencies(_forbidden_auth_dependency)
    override_all_db_dependencies(app, _fake_get_db)
    with TestClient(app) as c:
        yield c

@pytest.fixture
def client_unauthorized():
    override_all_role_dependencies(_unauthorized_auth_dependency)
    override_all_db_dependencies(app, _fake_get_db)
    with TestClient(app) as c:
        yield c
