# Submission schema

This directory does **not** define its own format. Every file here is a `.jsonl` submission
whose rows validate against `agentport_bench.schema.BenchTrialResult`, defined in
[`safelabs-eval`](https://github.com/AgentSafeLabs/safelabs-eval)'s
`agentport_bench/schema.py`, at the commit this repo's [`requirements.txt`](../requirements.txt)
pins.

Restating the schema here would let this repo's documentation silently drift out of sync
with what `agentport-bench validate` actually checks. If you need the field list, read
`agentport_bench/schema.py` directly, or `docs/AGENTPORT_BENCH.md` §4 for a human-readable
summary — both in the pinned `safelabs-eval` commit, not this repo.

## Filenames

```
<model>__<framework>__<library_version>__<yyyymmdd>.jsonl
<model>__<framework>__<library_version>__<yyyymmdd>.manifest.json
```

Double-underscore-delimited so model/framework names containing `-` or `.` stay unambiguous.
The `.manifest.json` sidecar is written automatically by `agentport-bench run`/`manifest`
(`<jsonl path>.with_suffix(".manifest.json")`) — don't rename it independently of its
`.jsonl` file, `build_leaderboard.py` and CI both expect the stems to match.

## The one rule this repo *does* enforce beyond the schema

**No raw model output, ever.** See [`../CONTRIBUTING.md`](../CONTRIBUTING.md)'s privacy
policy section for the full reasoning and what's checked (schema-level `extra="forbid"`,
plus a CI-side manifest `include_raw_output` check).
