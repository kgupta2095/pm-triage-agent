"""Minimal LLM client with a deterministic mock fallback.

Real mode: set ANTHROPIC_API_KEY or OPENAI_API_KEY.
Mock mode: no key set; keyword rules stand in for the model so the
pipeline runs anywhere (including CI) without network access.
"""

import json
import os
import re
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")
OPENAI_MODEL = os.environ.get("MODEL", "gpt-4o-mini")


def provider():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "mock"


def _post(url, headers, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def complete(system, user, max_tokens=800):
    p = provider()
    if p == "anthropic":
        out = _post(
            ANTHROPIC_URL,
            {
                "content-type": "application/json",
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
            },
            {
                "model": ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        return out["content"][0]["text"]
    if p == "openai":
        out = _post(
            OPENAI_URL,
            {
                "content-type": "application/json",
                "authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            },
            {
                "model": OPENAI_MODEL,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        return out["choices"][0]["message"]["content"]
    return _mock(system, user)


# ---------------- mock rules (no network) ----------------

BUG_WORDS = ("crash", "error", "broken", "fails", "failing", "wrong", "bug", "cannot", "can't", "500", "stuck")
BAU_WORDS = ("rename", "typo", "label", "wording", "permission", "config", "toggle", "colour", "color", "text change", "spelling")


def _title(text, limit=9):
    words = re.sub(r"\s+", " ", text.strip()).split(" ")
    t = " ".join(words[:limit]).strip(" .,:;")
    return t[0].upper() + t[1:] if t else "Untitled request"


def _mock(system, user):
    if "TASK:CLASSIFY" in system:
        req = user.split("REQUEST:\n", 1)[-1]
        low = req.lower()
        if any(w in low for w in BUG_WORDS):
            kind, priority = "bug", "high"
        elif any(w in low for w in BAU_WORDS):
            kind, priority = "bau", "low"
        else:
            kind, priority = "feature", "medium"
        return json.dumps({"type": kind, "priority": priority, "title": _title(req)})
    if "TASK:SPEC" in system:
        req = user.split("REQUEST:\n", 1)[-1].strip()
        return (
            "### Problem\n"
            f"{req}\n\n"
            "### Proposed scope\n"
            "- Reproduce or validate the request against current behaviour\n"
            "- Smallest change that resolves the stated problem\n"
            "- Out of scope: adjacent redesigns\n\n"
            "### Acceptance criteria\n"
            "- [ ] The behaviour described above is resolved or delivered\n"
            "- [ ] No regression in the surrounding flow\n"
            "- [ ] Copy and edge cases reviewed\n\n"
            "### Open questions\n"
            "- Which users or accounts are affected, and how many?\n"
            "- Is there a workaround today?"
        )
    return ""
