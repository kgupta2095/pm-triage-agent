# pm-triage-agent

**An agentic workflow that turns messy feature requests into classified, spec-stubbed issues, with a human approval gate it cannot skip.**

Every PM inbox fills with raw requests: half bug report, half wish, no acceptance criteria. This repo automates the mechanical part of triage (classify, title, priority, spec stub) and deliberately refuses to automate the judgment part (what actually gets filed). It is a small public version of how I run request-to-backlog automation at work.

Built by [Karan Gupta](https://www.linkedin.com/in/guptakaran786/), AI Product Manager. Companion repo: [spec-to-ship](https://github.com/kgupta2095/spec-to-ship).

## What it does

1. Reads raw requests ([sample_requests.md](sample_requests.md), synthetic, separated by `---`).
2. For each request: classifies it (bug, feature, or bau), assigns a suggested priority, and drafts a spec stub with problem, smallest viable scope, acceptance criteria, and open questions.
3. Writes everything to `QUEUE.md` with every item marked **Status: PENDING**. See [QUEUE_EXAMPLE.md](QUEUE_EXAMPLE.md) for real output.
4. A human reviews the queue and flips items to APPROVED.
5. Only then, and only with an explicit `--post --yes` plus a `GITHUB_TOKEN`, does the tool create GitHub issues, and only for approved items.

## Quickstart

Python 3.10+, no dependencies.

```bash
# mock mode (no API key): rule-based triage, runs anywhere
python run.py sample_requests.md

# real mode: set one key first
export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY
python run.py sample_requests.md

# after editing QUEUE.md statuses to APPROVED:
python run.py --post --repo you/your-repo        # dry run, prints what it would file
python run.py --post --repo you/your-repo --yes  # actually files issues (needs GITHUB_TOKEN)
```

## Design decisions

- **The approval gate is structural, not polite.** The agent physically cannot file an issue from raw model output: posting reads only from the human-edited queue file, requires a separate command, a token, and an explicit `--yes`. Autonomy for the mechanical work, a hard stop before anything becomes a team commitment.
- **Dry run is the default even after approval.** `--post` without `--yes` prints what would be filed. Destructive-adjacent actions should need two deliberate steps.
- **Spec stubs invent nothing.** The prompt forces unknowns into Open questions instead of letting the model guess affected users or root causes. A wrong guess in a spec is worse than a visible gap.
- **Mock mode is a real baseline.** Keyword rules stand in for the model, so the pipeline and its output format are testable with no key and no network, and the model's lift over rules stays visible.

## What I would build next

Duplicate detection against existing issues, a confidence field that routes low-confidence classifications to the human first, and source links so each filed issue carries the original request thread.

## License

MIT
