# app/json_utils.py
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

def to_plain_json(obj):
    """Recursively convert objects to JSON-serializable primitives."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        # choose float or str; float is fine for analytics, str for exactness
        return float(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, dict):
        return {k: to_plain_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_plain_json(v) for v in obj]
    # Fallback: best-effort string
    return str(obj)