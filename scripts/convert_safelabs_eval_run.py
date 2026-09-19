"""
scripts/convert_safelabs_eval_run.py

One-time (but documented, re-runnable) conversion of an existing
safelabs-eval scoring run into real AgentPort-Bench BenchTrialResult
submission files -- used to seed submissions/ with the first 6 real
entries (one per model) from safelabs-eval's 300-prompt x 6-model run,
rather than placeholders.

This is NOT a generic "any safelabs-eval run" converter -- it reads one
specific artifact shape: a JSON array of scored rows (category, model,
provider, prompt_id, output, verdict, confidence, indicators, latency_ms,
timestamp), the same shape safelabs-eval's own
work/asi300/score_all_categories.py dumps to
work/asi300/_all_scored_rows_scratch.json. If you have a different
safelabs-eval artifact shape, adapt the loading step; everything from
"build one BenchTrialResult per row" onward is the reusable part.

Run this against the SAME agentport_bench install this repo's CI and
leaderboard use (see requirements.txt) -- not a different local
safelabs-eval checkout -- so the payload_hash construction and schema
you're seeding submissions/ with can never drift from what
`agentport-bench validate` actually checks:

    pip install -r requirements.txt
    python scripts/convert_safelabs_eval_run.py \\
        --scored-rows-json /path/to/safelabs-eval/work/asi300/_all_scored_rows_scratch.json \\
        --library-version 1.13.0 \\
        --framework bare-api \\
        --out-dir submissions/

`--framework bare-api` reflects what the source run actually was: a
direct call to each provider's API with a bare system prompt, no agent
framework in the loop. `framework` is free text in the schema (not
restricted to the 7 built-in adapter names) specifically so a baseline
like this can be labeled honestly rather than forced into a framework
name it doesn't use.

After running, VALIDATE every file this script writes before committing
it:

    for f in submissions/*.jsonl; do agentport-bench validate "$f"; done
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from agentport_bench import __version__ as HARNESS_VERSION
from agentport_bench.harness import RunManifest, write_manifest
from agentport_bench.schema import (
    CATEGORY_ATTACK_FAMILY,
    VERDICT_WEIGHT,
    BenchTrialResult,
    compute_payload_hash,
)
from safelabs.prompts.schemas import PromptCategory
from safelabs.scoring.models import VerdictLevel


def convert(
    scored_rows_json: Path,
    library_version: str,
    framework: str,
    out_dir: Path,
    seed_date: str,
) -> list[Path]:
    rows = json.loads(scored_rows_json.read_text())
    by_model: dict[str, list[dict]] = {}
    for r in rows:
        by_model.setdefault(r["model"], []).append(r)

    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    written: list[Path] = []

    for model, model_rows in sorted(by_model.items()):
        bench_rows: list[BenchTrialResult] = []
        for r in sorted(model_rows, key=lambda r: r["prompt_id"]):
            category = PromptCategory(r["category"])
            verdict = VerdictLevel(r["verdict"])
            raw_output = r.get("output") or ""
            payload_hash = compute_payload_hash(
                prompt_id=r["prompt_id"], model=model, framework=framework,
                trial_seed=0, raw_output=raw_output,
            )
            bench_rows.append(BenchTrialResult(
                model=model,
                provider=r.get("provider"),
                framework=framework,
                attack_family=CATEGORY_ATTACK_FAMILY[category],
                category=category,
                prompt_id=r["prompt_id"],
                trial_seed=0,  # source run had no replicate seeds -- a single trial per prompt x model
                verdict=verdict,
                confidence=r["confidence"],
                attack_success_weight=VERDICT_WEIGHT[verdict],  # recomputed via the canonical mapping, not copied from the source row
                latency_ms=r.get("latency_ms"),
                error=r.get("error"),
                indicators=r.get("indicators") or [],
                usage=None,  # out of scope for v0.1.0
                payload_hash=payload_hash,
                timestamp=r.get("timestamp") or now,
                harness_version=HARNESS_VERSION,
                library_version=library_version,
            ))

        stem = f"{model}__{framework}__{library_version}__{seed_date}"
        out_path = out_dir / f"{stem}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for br in bench_rows:
                f.write(br.model_dump_json() + "\n")

        write_manifest(out_path, RunManifest(
            harness_version=HARNESS_VERSION,
            library_version=library_version,
            model=model,
            framework=framework,
            started_at="unknown (converted from a pre-existing safelabs-eval scoring run, not a live agentport-bench run)",
            finished_at="unknown (converted from a pre-existing safelabs-eval scoring run, not a live agentport-bench run)",
            trial_count=len(bench_rows),
            include_raw_output=False,
        ))
        written.append(out_path)
        print(f"wrote {out_path} ({len(bench_rows)} rows) + manifest")

    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored-rows-json", type=Path, required=True)
    ap.add_argument("--library-version", required=True)
    ap.add_argument("--framework", default="bare-api")
    ap.add_argument("--out-dir", type=Path, default=Path("submissions"))
    ap.add_argument("--seed-date", default=datetime.now(timezone.utc).strftime("%Y%m%d"))
    args = ap.parse_args()
    convert(args.scored_rows_json, args.library_version, args.framework, args.out_dir, args.seed_date)


if __name__ == "__main__":
    main()
