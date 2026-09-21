# AgentPort-Bench Results

Public results repository for **AgentPort-Bench**: a multi-contributor, cross-framework
agent-safety benchmark built on [safelabs-eval](https://github.com/AgentSafeLabs/safelabs-eval)'s
ASI-category prompt library (ASI01–ASI10) and scoring pipeline. See
[`docs/AGENTPORT_BENCH.md`](https://github.com/AgentSafeLabs/safelabs-eval/blob/main/docs/AGENTPORT_BENCH.md)
in that repo for the full design.

**Taxonomy note.** The prompt library's ASI01–ASI10 categories are an independently
structured category set that differs from OWASP's official
[Top 10 for Agentic Applications 2026](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/)
(published Dec 9, 2025). The official list also numbers its categories `ASI01`–`ASI10`,
so an ID here does not refer to the same category as OWASP's identically-numbered one.
This corpus is not currently mapped to the official taxonomy.

**This repo hosts submissions and the leaderboard. It does not define its own submission
format or validation logic** — both come from the `agentport_bench` package in
`safelabs-eval`, pinned to a specific commit (see [`requirements.txt`](requirements.txt)).

## Leaderboard

See [`leaderboard/index.md`](leaderboard/index.md) (Markdown table, generated) or
[`leaderboard/data.json`](leaderboard/data.json) (structured, generated).

Submissions are grouped by `library_version` — the `safelabs-eval` prompt-library version
a submission was scored against. **Groups are never merged or ranked against each other.**
A submission scored against the original 30-prompt library (`1.0.0`/`1.1.0`) and one scored
against the current 300-prompt library (`1.13.0`) are structurally different benchmarks; see
`agentport_bench.schema.is_library_version_comparable()` for the exact rule.

## Submitting

1. Run the benchmark against your model/framework using the `agentport-bench` CLI (installed
   from `safelabs-eval`):
   ```bash
   pip install "git+https://github.com/AgentSafeLabs/safelabs-eval.git@<commit>"
   agentport-bench run --adapter http --target <your-endpoint> --model <your-model-id> \
     --output submissions/<model>__<framework>__<library_version>__<yyyymmdd>.jsonl
   ```
   This writes your results file **and** a `.manifest.json` sidecar. Submit both.
2. Validate locally before opening a PR:
   ```bash
   agentport-bench validate submissions/<your-file>.jsonl
   ```
   Fix anything reported as `REJECTED`. `FLAGGED` items are informational — CI surfaces them
   for reviewer visibility but does not block on them (see [`CONTRIBUTING.md`](CONTRIBUTING.md)).
3. Open a PR adding your `.jsonl` + `.manifest.json` under `submissions/`. CI re-runs
   `agentport-bench validate` and a manifest privacy check automatically.
4. Once merged, run `python leaderboard/build_leaderboard.py` (or wait for the next
   scheduled regeneration, if one is set up) to refresh the leaderboard.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full requirements, including the
**privacy policy — no raw model completions are ever submitted here.**

## What this repo does *not* do

- **Reimplement validation or comparison logic.** Every check comes from
  `agentport_bench.validate` / `agentport_bench.schema`, imported from the pinned
  `safelabs-eval` install. If validation behavior needs to change, that change belongs in
  `safelabs-eval`, not here.
- **Store raw model completions.** `BenchTrialResult` (the schema every submission is
  validated against) has no field for one — integrity is verified via `payload_hash`
  instead. `BenchTrialResult` now also **rejects any unexpected field outright**
  (`extra="forbid"`, `safelabs-eval` commit `8aadf12`), so a submission accidentally
  carrying a stray `raw_output` key fails validation rather than silently stripping it
  while the text stays committed in the file.
- **Capture token usage.** Out of scope for `agentport_bench` v0.1.0; `usage` is always
  `null` in every submission.
- **Reconstruct historical prompt-library snapshots.** `safelabs-eval` only ships its
  current library content — a submission's `prompt_id`/`category` can only be checked
  against the *currently installed* library, not whatever it looked like at an older
  claimed `library_version`. See `docs/AGENTPORT_BENCH.md` §3 for the exact caveat.
