"""Triage raw requests into a review queue, then (only after human approval) post issues.

Usage:
  python3 run.py sample_requests.md                 # writes QUEUE.md, posts nothing
  python3 run.py --post --repo owner/name           # dry run: prints what it would file, no token needed
  python3 run.py --post --repo owner/name --yes     # files APPROVED items; needs GITHUB_TOKEN

The agent never ships its own output: everything lands in QUEUE.md as
PENDING first. A human flips PENDING to APPROVED, and only then, with an
explicit --post --yes, do issues get created.

Rules the gate enforces:
  * Approval is read ONLY from the item's own metadata block (the lines
    directly under its "## N." heading). Text inside the request or the
    spec can never approve an item, even if it says "Status: APPROVED".
  * PENDING, REJECTED and anything unrecognised are never posted.
  * After a successful post the item is rewritten to "Status: FILED #<n>",
    so running --post --yes again does not file it twice.
"""

import argparse
import datetime
import json
import os
import re
import stat
import sys
import tempfile
import urllib.error
import urllib.request

import llm
from triage import classify, draft_spec

QUEUE = "QUEUE.md"
ITEM_SEP = "\n## "

# A status line must be a whole line inside the item's metadata block.
STATUS_LINE = re.compile(r"^Status:")
# [ \t] rather than \s so a match never runs across a line break.
APPROVED = re.compile(r"^Status:[ \t]*APPROVED[ \t]*(?=\r?$)", re.M)
FILED = re.compile(r"^Status:[ \t]*FILED[ \t]+#(\d+)[ \t]*(?=\r?$)", re.M)
PENDING = re.compile(r"^Status:[ \t]*PENDING[ \t]*(?=\r?$)", re.M)
REJECTED = re.compile(r"^Status:[ \t]*REJECTED[ \t]*(?=\r?$)", re.M)
HEADING = re.compile(r"(\d+)\. \[(\w+)\] (.+)")
# Lines in request or model text that would open a new queue item (or a
# top-level heading) if written as-is. They are escaped before writing.
HEADING_LINE = re.compile(r"^(#{1,2})(?=\s|$)", re.M)


# ---------------- building the queue ----------------

def load_requests(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    out = []
    for part in text.split("\n---\n"):
        lines = [l for l in part.strip().splitlines() if not l.startswith("# ")]
        body = "\n".join(lines).strip()
        if body:
            out.append(body)
    return out


def _one_line(value):
    """Collapse text to a single line so it cannot add lines to an item's metadata block."""
    return " ".join(str(value).split())


def _escape_headings(text):
    """Stop request or model text from opening a new '## ' queue item."""
    return HEADING_LINE.sub(r"\\\1", text)


def build_queue(path, queue_path=QUEUE, overwrite=False):
    if os.path.exists(queue_path) and not overwrite:
        reviewed = [it for it in parse_queue_text(_read(queue_path))
                    if it["status"] in ("APPROVED", "FILED")]
        if reviewed:
            sys.exit(f"{queue_path} already has {len(reviewed)} APPROVED or FILED item(s). "
                     "Rebuilding would wipe those marks. Move it aside, or pass --overwrite.")
    mode = llm.provider()
    items = []
    for i, req in enumerate(load_requests(path), 1):
        meta = classify(req)
        spec = draft_spec(req)
        items.append((i, meta, spec))
    if mode == "mock":
        mode_line = "Mode: mock (keyword rules stand in for the model; no model was called)."
    else:
        today = datetime.date.today().isoformat()
        mode_line = f"Mode: recorded model run ({mode}, {llm.model_name()}, {today})."
    lines = [
        "# Triage queue",
        "",
        mode_line,
        "Every item starts as Status: PENDING. Review each spec,",
        "change Status to APPROVED (or REJECTED), then run:",
        "`python3 run.py --post --repo owner/name --yes`",
        "",
    ]
    for i, meta, spec in items:
        lines += [
            f"## {i}. [{_one_line(meta['type']).upper()}] {_one_line(meta['title'])}",
            "",
            f"Priority: {_one_line(meta['priority'])}  ",
            "Status: PENDING",
            "",
            _escape_headings(spec),
            "",
        ]
    _write(queue_path, "\n".join(lines))
    print(f"Wrote {queue_path} with {len(items)} proposed issues (mode: {mode}). Nothing was posted.")


# ---------------- reading the queue ----------------

def _meta_span(block):
    """Character span (start, end) of an item's metadata block.

    The metadata block is the first paragraph under the heading line: the
    non-blank lines up to the first blank line (or the first '#' line). In a
    queue written by build_queue that is exactly the Priority and Status
    lines. The spec always sits below a blank line, so nothing in the
    request or the spec can land here.
    """
    lines = block.split("\n")
    offsets, pos = [], 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1
    i = 1
    while i < len(lines) and not lines[i].strip():  # blank lines after the heading
        i += 1
    start = offsets[i] if i < len(lines) else len(block)
    j = i
    while j < len(lines) and lines[j].strip() and not lines[j].lstrip().startswith("#"):
        j += 1
    end = offsets[j] if j < len(lines) else len(block)
    return start, end


def _status(meta):
    """Return (status, issue_number), read from an item's metadata block only."""
    status_lines = [l for l in meta.splitlines() if STATUS_LINE.match(l)]
    if len(status_lines) != 1:
        return "INVALID", None  # no status line, or more than one: never post
    line = status_lines[0]
    if APPROVED.match(line):
        return "APPROVED", None
    m = FILED.match(line)
    if m:
        return "FILED", int(m.group(1))
    if PENDING.match(line):
        return "PENDING", None
    if REJECTED.match(line):
        return "REJECTED", None
    return "INVALID", None


def parse_queue_text(text):
    blocks = text.split(ITEM_SEP)[1:]
    for index, b in enumerate(blocks):
        heading = b.split("\n", 1)[0]
        m = HEADING.match(heading)
        if not m:
            continue
        start, end = _meta_span(b)
        meta = b[start:end]
        status, issue = _status(meta)
        priority = re.search(r"^Priority:\s*(\S+)", meta, re.M)
        spec = b[end:].strip()
        body = f"Suggested priority: {priority.group(1)}\n\n{spec}" if priority else spec
        yield {
            "index": index,
            "heading": heading,
            "number": int(m.group(1)),
            "type": m.group(2).lower(),
            "title": m.group(3).strip(),
            "status": status,
            "issue": issue,
            "body": body,
        }


def parse_queue(queue_path=QUEUE):
    if not os.path.exists(queue_path):
        sys.exit(f"{queue_path} not found. Run `python3 run.py sample_requests.md` first.")
    return list(parse_queue_text(_read(queue_path)))


# ---------------- marking filed items ----------------

def _read(path):
    # newline="" keeps line endings exactly as they are on disk, so a rewrite
    # changes only the Status line (also for files saved with CRLF endings).
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _write(path, text):
    """Write atomically so a crash never leaves a half-written queue."""
    folder = os.path.dirname(os.path.abspath(path))
    mode = stat.S_IMODE(os.stat(path).st_mode) if os.path.exists(path) else 0o644
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".queue-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def mark_filed(queue_path, item, issue_number):
    """Rewrite one APPROVED item's Status line to 'Status: FILED #<n>'."""
    parts = _read(queue_path).split(ITEM_SEP)
    k = item["index"] + 1
    if k >= len(parts) or parts[k].split("\n", 1)[0] != item["heading"]:
        raise RuntimeError(f"{queue_path} changed while posting; could not find '{item['heading']}'")
    block = parts[k]
    start, end = _meta_span(block)
    meta = block[start:end]
    if _status(meta)[0] != "APPROVED":
        raise RuntimeError(f"'{item['heading']}' is no longer APPROVED in {queue_path}")
    new_meta = APPROVED.sub(f"Status: FILED #{int(issue_number)}", meta, count=1)
    parts[k] = block[:start] + new_meta + block[end:]
    _write(queue_path, ITEM_SEP.join(parts))


# ---------------- posting ----------------

def github_poster(repo, token):
    """Return a function that files one item as a GitHub issue and returns its number."""
    def post(item):
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues",
            data=json.dumps({
                "title": item["title"],
                "body": item["body"],
                "labels": [item["type"]],
            }).encode(),
            headers={
                "authorization": f"Bearer {token}",
                "accept": "application/vnd.github+json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return int(json.loads(r.read().decode())["number"])
    return post


def post_issues(repo, dry, queue_path=QUEUE, poster=None):
    """Post APPROVED items only. Dry run needs no token; real posting does.

    `poster` is a function item -> issue number. It defaults to the GitHub
    API and is swapped for a fake in tests.
    """
    items = parse_queue(queue_path)
    approved = [it for it in items if it["status"] == "APPROVED"]
    held = [it for it in items if it["status"] in ("PENDING", "REJECTED")]

    for it in items:
        if it["status"] == "FILED":
            print(f"Skipping (already filed as #{it['issue']}): {it['title']}")
        elif it["status"] == "INVALID":
            print(f"Skipping (Status line not recognised, fix it by hand): {it['title']}")
    if held:
        print(f"Not posting {len(held)} PENDING or REJECTED item(s).")
    if not approved:
        print(f"No APPROVED items in {queue_path}. Nothing to post.")
        return 0

    if dry:
        for it in approved:
            print(f"[dry run] would create issue: [{it['type']}] {it['title']}")
        print("Dry run only, nothing was posted. Add --yes to file these (needs GITHUB_TOKEN).")
        return 0

    if poster is None:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("GITHUB_TOKEN is not set. Refusing to post.")
        poster = github_poster(repo, token)

    for it in approved:
        try:
            number = poster(it)
        except urllib.error.URLError as e:  # HTTPError is a subclass
            reason = getattr(e, "code", None) or e.reason
            sys.exit(f"Stopped: posting '{it['title']}' failed ({reason}). "
                     "Items filed before this one are marked FILED; rerun after fixing.")
        try:
            mark_filed(queue_path, it, number)
        except Exception as e:  # the issue now exists, so say so loudly
            sys.exit(f"Created issue #{number} for '{it['title']}' but could not mark it FILED ({e}). "
                     f"Change its line to 'Status: FILED #{number}' by hand before rerunning.")
        print(f"Created issue #{number}: {it['title']} (marked FILED in {queue_path})")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("requests", nargs="?", default="sample_requests.md")
    ap.add_argument("--post", action="store_true", help="post APPROVED queue items as GitHub issues")
    ap.add_argument("--repo", help="owner/name for --post")
    ap.add_argument("--yes", action="store_true", help="actually post (without this, --post is a dry run)")
    ap.add_argument("--overwrite", action="store_true",
                    help="rebuild QUEUE.md even if it has APPROVED or FILED items")
    args = ap.parse_args(argv)
    if args.post:
        if not args.repo:
            sys.exit("--post needs --repo owner/name")
        return post_issues(args.repo, dry=not args.yes)
    build_queue(args.requests, overwrite=args.overwrite)
    return 0


if __name__ == "__main__":
    sys.exit(main())
