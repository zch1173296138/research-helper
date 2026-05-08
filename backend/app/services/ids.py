import re
import uuid


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def slugify(value: str, fallback_prefix: str = "item") -> str:
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", value.strip().lower()).strip("_")
    if not slug:
        return new_id(fallback_prefix)
    return slug[:64]

