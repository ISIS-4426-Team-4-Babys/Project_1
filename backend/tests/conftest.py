import os, sys, types, pathlib
from unittest.mock import MagicMock

ROOT = pathlib.Path(__file__).resolve().parent.parent
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
    import config as _config  # use real package if present
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

from main import app
from config.database import get_db

class DummySession:
    def __init__(self):
        self._closed = False

    # ORM-style chainables
    def query(self, *args, **kwargs): return self
    def filter(self, *args, **kwargs): return self
    def filter_by(self, *args, **kwargs): return self
    def join(self, *args, **kwargs): return self
    def options(self, *args, **kwargs): return self

    # Common terminal operations
    def all(self): return []
    def first(self): return None
    def one(self): raise Exception("No row")
    def one_or_none(self): return None
    def get(self, *args, **kwargs): return None

    # Unit-of-work ops
    def add(self, *args, **kwargs): pass
    def add_all(self, *args, **kwargs): pass
    def delete(self, *args, **kwargs): pass
    def commit(self): pass
    def rollback(self): pass
    def refresh(self, *args, **kwargs): pass

    # SQLAlchemy 1.4/2.x execution path
    def execute(self, *args, **kwargs):
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

app.dependency_overrides[get_db] = _fake_get_db
