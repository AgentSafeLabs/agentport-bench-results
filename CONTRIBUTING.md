# Contributing a submission

## What a submission is

A submission is **the literal output of `agentport-bench run`**: one `.jsonl` file where
every line is a `BenchTrialResult` (defined in `safelabs-eval`'s `agentport_bench/schema.py`),
plus its `.manifest.json` sidecar (written automatically alongside it). This repo does not
define its own submission format — see [`submissions/SCHEMA.md`](submissions/SCHEMA.md).

If you didn't produce your file with `agentport-bench run`, it must still validate cleanly
as a sequence of `BenchTrialResult` rows with a truthful `.manifest.json` sidecar
(`agentport-bench manifest --output <file>` will (re)generate one from an existing file's
rows if needed — `started_at`/`finished_at` will be marked `"unknown"` rather than
fabricated, which is expected and fine).

## Privacy policy — read this before you submit

**Never submit raw model output.** The whole point of `payload_hash` (a sha256 binding
`prompt_id + model + framework + trial_seed + raw_output`) is that a submission's integrity
is verifiable *without* publishing completions.

- `BenchTrialResult` has no field for raw text, and as of `safelabs-eval` commit `8aadf12`,
  it **actively rejects** any unexpected field (`extra="forbid"`) — including an
  accidentally-included `raw_output` key — rather than silently discarding it while the
  literal text stays in your committed file and PR diff forever. `agentport-bench validate`
  will reject such a file with `schema_validation_failed`.
- If you used `agentport-bench run --include-raw-output` (default off) for your own local
  debugging, **do not submit that file.** It's a different schema
  (`BenchTrialResultWithRawOutput`) and will fail validation anyway, but don't rely on that —
  regenerate without the flag, or manually confirm the file you're submitting doesn't have
  it. CI also checks your `.manifest.json`'s `include_raw_output` field and rejects if it's
  `true` or the manifest is missing (belt-and-suspenders — the schema check above is the
  real backstop, this catches a hand-built submission with no honest manifest at all).
- `indicators` on each row must stay short detector-tag strings (how the harness already
  writes them) — never raw response text.

## Validation gate

Before opening a PR, run:

```bash
agentport-bench validate submissions/<your-file>.jsonl
```

This is the **same command CI runs** — nothing is reimplemented here. It checks (see
`docs/AGENTPORT_BENCH.md` §3 in `safelabs-eval` for the full 15-code reference):

- File-level: valid UTF-8, non-empty, valid JSON/schema per line
- `(model, framework, prompt_id, trial_seed)` uniqueness within the file
- Every `prompt_id`/`category` against the currently installed prompt library
- `library_version` comparability (mixed versions in one file, unregistered versions,
  a version that isn't the currently installed one)
- `payload_hash` against an optional `--verify-sample` bundle (not required — see below)
- Category coverage (partial submissions are accepted, just flagged)

**`REJECTED`** issues must be fixed — the submission cannot be merged with any of them.
**`FLAGGED`** issues are informational; the submission is still accepted and merged with
flags visible for reviewer awareness. `payload_hash_unverified` is the expected, normal flag
on every submission that doesn't supply `--verify-sample` — requiring that bundle for every
submission would force publishing raw output, which defeats the privacy design above. Don't
try to suppress this flag; it isn't a problem to fix.

## What CI checks on your PR

`.github/workflows/validate-submission.yml` runs on any PR touching `submissions/**`:

1. Installs `agentport_bench` from the pinned `safelabs-eval` commit (see
   [`requirements.txt`](requirements.txt)) — the exact same version `agentport-bench
   validate` above ran against locally, so a local pass means CI passes too.
2. Runs `agentport-bench validate` against every changed `.jsonl` file. **CI fails iff
   the submission is rejected** (the tool's own exit code / `accepted: false`) — this
   mirrors `validate`'s own accept/flag/reject semantics rather than second-guessing them;
   flag-severity issues are printed in the CI log for reviewer visibility but do not block
   the merge, matching how they're documented to behave everywhere else.
3. Checks the matching `.manifest.json`'s `include_raw_output` field directly — rejects if
   `true` or the manifest is missing, regardless of what schema validation found. This is
   supplementary defense-in-depth, not a replacement for the schema-level `extra="forbid"`
   protection.

## Updating the pinned `safelabs-eval` commit

`requirements.txt` pins an exact commit, not `main` or a tag, because `agentport_bench` is
unreleased (v0.1.0) — a floating ref would let unrelated future commits silently change what
this repo validates and aggregates against. Bumping the pin is a deliberate PR of its own:
update `requirements.txt`, re-run `agentport-bench validate` against every existing file in
`submissions/` to confirm nothing that was previously accepted now fails (a behavior change
upstream, e.g. a stricter schema check, could affect old submissions), and note the bump's
reason in the PR description.

## Refreshing the leaderboard

```bash
python leaderboard/build_leaderboard.py
```

Regenerates `leaderboard/data.json` and `leaderboard/index.md` from every file currently in
`submissions/`. It imports the real grouping/comparability logic from the installed
`agentport_bench` package (`is_library_version_comparable`,
`cli._group_by_comparable_library_version` — the exact function `agentport-bench compare`
itself uses) rather than reimplementing the grouping rule. Commit the regenerated files
alongside your submission PR, or in a separate PR if you're just refreshing after someone
else's merge.
