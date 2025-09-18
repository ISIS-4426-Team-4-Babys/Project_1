
import uuid
import typing
import enum
import datetime as _dt



def jsonify(obj):
    """Recursively convert UUID/datetime/date/Enum to JSON-serializable types."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()
    if isinstance(obj, enum.Enum):
        return getattr(obj, "value", obj.name)
    if isinstance(obj, list):
        return [jsonify(x) for x in obj]
    if isinstance(obj, dict):
        return {k: jsonify(v) for k, v in obj.items()}
    return obj

def _is_optional(ann):
    origin = typing.get_origin(ann)
    return origin is typing.Union and type(None) in typing.get_args(ann)

def _pyd_fields(model_cls):
    # pydantic v2 has model_fields; v1 has __fields__
    fields = getattr(model_cls, "model_fields", None)
    if fields is not None:
        return fields, "v2"
    return getattr(model_cls, "__fields__", {}), "v1"

def _dummy_for_type(ann, name=""):
    """Heuristic dummy value generator that works for pydantic v1/v2 annotations."""
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)
    lname = (name or "").lower()

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

    # Strings / Any with common field-name hints across your tests
    if ann in (str, typing.Any):
        if lname == "id" or lname.endswith("_id"):
            return str(uuid.uuid4())
        # common names across your suites
        if lname in ("email",):          return "alice@example.com"
        if lname in ("password",):       return "secret"
        if lname in ("name",):           return "Alice"
        if lname in ("profile_image",):  return ""
        if lname in ("code",):           return "ISIS-1105"
        if lname in ("department","faculty"):
            return "Ingeniería de Sistemas y Computación"
        if lname in ("description","summary"):
            return "desc"
        if lname in ("type","filetype"): return "application/octet-stream"
        if lname in ("url","path","filepath"):
            return "https://example.com/x"
        return "x"

    if ann in (int,):
        # special-cases used in resource_test
        if lname in ("size","total_docs"):
            return 1
        return 0

    if ann in (float,): return 0.0
    if ann in (bool,):  return False

    if ann in (_dt.datetime,):
        # ISO like the tests expect when serialized
        return _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=_dt.timezone.utc).isoformat()
    if ann in (_dt.date,):
        return _dt.date.today().isoformat()

    if origin in (list, typing.List, typing.Sequence, typing.MutableSequence): return []
    if origin in (dict, typing.Dict, typing.Mapping, typing.MutableMapping):  return {}

    if isinstance(ann, type) and issubclass(ann, enum.Enum):
        members = list(ann.__members__.values())
        m = members[0]
        return getattr(m, "value", m.name)

    # Nested Pydantic model
    if hasattr(ann, "model_fields") or hasattr(ann, "__fields__"):
        return _build_model_dict(ann)

    return None

def _build_model_dict(model_cls):
    """Build a dict that satisfies the required fields of a Pydantic model (v1/v2)."""
    fields, mode = _pyd_fields(model_cls)
    data = {}
    for name, field in fields.items():
        if mode == "v1":
            required = field.required
            ann = field.type_
            default = field.default if field.default is not None else (
                field.default_factory() if field.default_factory else None
            )
        else:
            required = field.is_required()
            ann = field.annotation
            default = field.default if field.default is not None else (
                field.default_factory() if field.default_factory is not None else None
            )

        if not required:
            continue

        val = _dummy_for_type(ann, name)
        if val is None and default is not None:
            val = default
        if val is None:
            val = "x" if "id" not in name.lower() else str(uuid.uuid4())
        data[name] = val

    # Validate once via model (if available), then return plain dict
    try:
        inst = model_cls(**data)
        return inst.model_dump() if hasattr(inst, "model_dump") else inst.dict()
    except Exception:
        return data

def build_from_model(model_cls, overrides=None, json_safe=False):
    base = _build_model_dict(model_cls)
    if overrides:
        base.update(overrides)
    return jsonify(base) if json_safe else base

def assert_subset(subset: dict, full: dict):
    """Assert every key/value in subset appears identical in full (when key exists)."""
    for k, v in subset.items():
        if k in full:
            assert full[k] == v, f"Mismatch for key '{k}': {full[k]} != {v}"


def build_course(overrides=None):
    try:
        from schemas.course_schema import CourseResponse
    except Exception:
        return {"id": str(uuid.uuid4()), **(overrides or {})}
    base = build_from_model(CourseResponse, overrides=overrides or {}, json_safe=False)
    # ensure invariants used in user_test
    teacher = base.get("teacher") or {}
    teacher.setdefault("id", str(uuid.uuid4()))
    teacher.setdefault("name", teacher.get("name") or "Prof. Ada")
    teacher.setdefault("email", teacher.get("email") or "ada@example.com")
    base["teacher"] = teacher
    base["taught_by"] = base.get("taught_by") or teacher["id"]
    return base

def build_agent(overrides=None):
    try:
        from schemas.agent_schema import AgentResponse
    except Exception:
        return {"id": str(uuid.uuid4()), **(overrides or {})}
    return build_from_model(AgentResponse, overrides=overrides or {}, json_safe=False)

def build_resource(overrides=None):
    try:
        from schemas.resource_schema import ResourceResponse
    except Exception:
        return {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", **(overrides or {})}
    return build_from_model(ResourceResponse, overrides=overrides or {}, json_safe=False)

def build_user_response(overrides=None):
    try:
        from schemas.user_schema import UserResponse
    except Exception:
        return {"id": str(uuid.uuid4()), **(overrides or {})}

    base = build_from_model(UserResponse, overrides=overrides or {}, json_safe=False)

    try:
        from models.user_model import UserRole
        if isinstance(base.get("role"), str):
            base["role"] = UserRole(base["role"])
    except Exception:
        pass

    return UserResponse(**base)

