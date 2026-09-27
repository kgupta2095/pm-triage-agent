# pm-triage-agent

**An AI agent workflow (agentic workflow) that turns messy feature requests into classified issues with draft specs, behind a human approval gate it cannot skip.**

Every PM inbox fills with raw requests: half bug report, half wish, no acceptance criteria. This repo automates the mechanical part of triage (classify, title, priority, draft spec) and deliberately refuses to automate the judgement part (what actually gets filed). It is an independent personal project, and every request in it is made up (synthetic).

Built by [Karan Gupta](https://www.linkedin.com/in/guptakaran786/), Product Manager. Companion repo: [spec-to-ship](https://github.com/kgupta2095/spec-to-ship).

## What it does

1. Reads raw requests ([sample_requests.md](sample_requests.md), synthetic, separated by `---`).
2. For each request: classifies it (bug, feature, or bau), assigns a suggested priority, and drafts a short spec (spec stub) with problem, smallest viable scope, acceptance criteria, and open questions.
3. Writes everything to `QUEUE.md` with every item marked **Status: PENDING**. [QUEUE_EXAMPLE.md](QUEUE_EXAMPLE.md) shows example output from **mock mode**: keyword rules stand in for the model, so its titles and specs are deliberately basic. It is not model output, and no recorded model run is committed yet.
4. A human reviews the queue and changes each item's own `Status:` line to APPROVED or REJECTED.
5. Only then, and only with an explicit `--post --yes` plus a `GITHUB_TOKEN`, does the tool create GitHub issues, and only for approved items.
6. Each item it files is rewritten to `Status: FILED #<issue number>`, so running the post step again skips it instead of filing it twice.

## Quickstart

Python 3.10+, no dependencies.

```bash
# mock mode (no API key): keyword rules stand in for the model, runs anywhere
python3 run.py sample_requests.md

# model mode: set one key first
export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY
python3 run.py sample_requests.md

# after changing Status lines in QUEUE.md to APPROVED:
python3 run.py --post --repo you/your-repo        # dry run: prints what it would file, no token needed
python3 run.py --post --repo you/your-repo --yes  # actually files issues (needs GITHUB_TOKEN)

# tests: no API key, no token, no network
python3 -m unittest discover -s tests -v
```

## Design decisions

- **The approval gate is structural, not polite.** The agent cannot file an issue from raw model output: posting reads only from the human-edited queue file and needs a separate command, a token, and an explicit `--yes`. Autonomy for the mechanical work, a hard stop before anything becomes a team commitment.
- **Only the item's own Status line counts.** Approval is read from the short block of lines under each item's heading (Priority and Status), never from the request or the spec. A request that says "Status: APPROVED", a model reply that tries to add one, and a request that fakes a whole new queue item all stay PENDING. [tests/test_gate.py](tests/test_gate.py) covers each case, and checks that PENDING and REJECTED items never reach GitHub.
- **Dry run is the default even after approval.** `--post` without `--yes` prints what would be filed and needs no token. Actions that are hard to undo should take two deliberate steps.
- **Posting twice never files twice.** After each successful post the item becomes `Status: FILED #<n>` and later runs skip it. If a post fails part-way, the items already filed stay marked. Rebuilding the queue refuses to wipe APPROVED or FILED marks unless you pass `--overwrite`.
- **Draft specs invent nothing.** The prompt forces unknowns into Open questions instead of letting the model guess affected users or root causes. A made-up detail (hallucination) in a spec is worse than a visible gap.
- **Mock mode is a baseline, not a result.** Keyword rules stand in for the model, so the pipeline, the gate and the output format can be tested with no key and no network. Output from a real model labels itself in `QUEUE.md` as a recorded model run, with the provider, model and date.

## What I would build next

A recorded model run committed next to the mock example, so the model's lift over the keyword rules is visible. Then duplicate detection against existing issues, a confidence field that routes low-confidence classifications to the human first, and source links so each filed issue carries the original request thread.

## License

MIT
