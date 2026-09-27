"""Classify a raw request and draft a spec stub for it."""

import json

from llm import complete

CLASSIFY_SYSTEM = (
    "TASK:CLASSIFY You triage product requests. Classify the request as one of: "
    "bug (something is broken), feature (new capability), bau (small change: copy, "
    "config, permissions, labels). Suggest a priority: high, medium, or low. "
    'Return only JSON: {"type": "...", "priority": "...", "title": "short imperative title"}'
)

SPEC_SYSTEM = (
    "TASK:SPEC You are a product manager writing a spec stub from a raw request. "
    "Write markdown with exactly these sections: '### Problem' (restate the request "
    "plainly), '### Proposed scope' (bullet the smallest viable change and one "
    "explicit out-of-scope line), '### Acceptance criteria' (3 checkboxes), "
    "'### Open questions' (2 bullets). Invent nothing the request does not say; "
    "put unknowns under Open questions."
)


TYPES = ("bug", "feature", "bau")
PRIORITIES = ("high", "medium", "low")


def _pick(value, allowed, default):
    """Keep a model-supplied field only if it is one of the allowed words."""
    v = str(value).strip().lower()
    return v if v in allowed else default


def classify(request: str) -> dict:
    raw = complete(CLASSIFY_SYSTEM, f"REQUEST:\n{request}", max_tokens=200)
    try:
        start, end = raw.index("{"), raw.rindex("}") + 1
        data = json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    title = " ".join(str(data.get("title") or request.strip().split("\n")[0][:70]).split())
    return {
        "type": _pick(data.get("type", "feature"), TYPES, "feature"),
        "priority": _pick(data.get("priority", "medium"), PRIORITIES, "medium"),
        "title": title or "Untitled request",
    }


def draft_spec(request: str) -> str:
    return complete(SPEC_SYSTEM, f"REQUEST:\n{request}").strip()
