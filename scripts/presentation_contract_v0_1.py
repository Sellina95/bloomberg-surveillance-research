"""Strict presentation values: never stringify research containers."""


def scalar_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        raise ValueError("Unsupported structured presentation value")
    return str(value)


def list_item_text(value):
    if isinstance(value, dict):
        if not set(value) <= {"view", "evidence_basis"}:
            raise ValueError("Unsupported presentation item keys")
        if not isinstance(value.get("view"), str) or not value["view"].strip():
            raise ValueError("Presentation view must be nonempty prose")
        if "evidence_basis" in value and not isinstance(value["evidence_basis"], str):
            raise ValueError("Invalid evidence_basis type")
        # Render public prose only, not the evidence container. Keep JSON intact.
        return value["view"]
    return scalar_text(value)
