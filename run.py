"""Triage raw requests into a review queue, then (only after human approval) post issues.

Usage:
  python run.py sample_requests.md          # writes QUEUE.md, posts nothing
  python run.py --post --repo owner/name    # posts APPROVED items only; needs GITHUB_TOKEN and --yes

The agent never ships its own output: everything lands in QUEUE.md as
PENDING first. A human flips PENDING to APPROVED, and only then, with an
explicit --post --yes, do issues get created.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

import llm
from triage import classify, draft_spec

QUEUE = "QUEUE.md"


def load_requests(path):
    text = open(path, encoding="utf-8").read()
    out = []
    for part in text.split("\n---\n"):
        lines = [l for l in part.strip().splitlines() if not l.startswith("# ")]
        body = "\n".join(lines).strip()
        if body:
            out.append(body)
    return out


def build_queue(path):
    mode = llm.provider()
    items = []
    for i, req in enumerate(load_requests(path), 1):
        meta = classify(req)
        spec = draft_spec(req)
        items.append((i, meta, spec))
    lines = [
        "# Triage queue",
        "",
        f"Mode: {mode}. Every item starts as Status: PENDING. Review each spec,",
        "change Status to APPROVED (or REJECTED), then run:",
        "`python run.py --post --repo owner/name --yes`",
        "",
    ]
    for i, meta, spec in items:
        lines += [
            f"## {i}. [{meta['type'].upper()}] {meta['title']}",
            "",
            f"Priority: {meta['priority']}  ",
            "Status: PENDING",
            "",
            spec,
            "",
        ]
    open(QUEUE, "w", encoding="utf-8").write("\n".join(lines))
    print(f"Wrote {QUEUE} with {len(items)} proposed issues (mode: {mode}). Nothing was posted.")


def parse_queue():
    text = open(QUEUE, encoding="utf-8").read()
    blocks = re.split(r"\n## ", text)[1:]
    for b in blocks:
        header = b.split("\n", 1)[0]
        m = re.match(r"\d+\. \[(\w+)\] (.+)", header)
        status = "APPROVED" if re.search(r"Status: APPROVED", b) else "PENDING"
        body = b.split("\n", 2)[-1]
        if m:
            yield {"type": m.group(1).lower(), "title": m.group(2).strip(), "status": status, "body": body}


def post_issues(repo, dry):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is not set. Refusing to post.")
    approved = [it for it in parse_queue() if it["status"] == "APPROVED"]
    if not approved:
        sys.exit("No APPROVED items in QUEUE.md. Nothing to post.")
    for it in approved:
        if dry:
            print(f"[dry run] would create issue: [{it['type']}] {it['title']}")
            continue
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues",
            data=json.dumps({
                "title": it["title"],
                "body": it["body"],
                "labels": [it["type"]],
            }).encode(),
            headers={
                "authorization": f"Bearer {token}",
                "accept": "application/vnd.github+json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.loads(r.read().decode())
        print(f"Created issue #{out['number']}: {it['title']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("requests", nargs="?", default="sample_requests.md")
    ap.add_argument("--post", action="store_true", help="post APPROVED queue items as GitHub issues")
    ap.add_argument("--repo", help="owner/name for --post")
    ap.add_argument("--yes", action="store_true", help="actually post (without this, --post is a dry run)")
    args = ap.parse_args()
    if args.post:
        if not args.repo:
            sys.exit("--post needs --repo owner/name")
        post_issues(args.repo, dry=not args.yes)
    else:
        build_queue(args.requests)


if __name__ == "__main__":
    main()
