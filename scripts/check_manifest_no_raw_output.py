"""
scripts/check_manifest_no_raw_output.py

CI belt-and-suspenders privacy check: a submission's .manifest.json must
have include_raw_output == false. Supplementary to BenchTrialResult's
schema-level extra="forbid" protection (safelabs-eval commit 8aadf12),
not a replacement -- this catches a hand-built submission with a
missing or dishonest manifest, which schema validation alone can't see.

Exits 0 (silent) if the manifest exists and include_raw_output is
exactly False. Exits 1 with a message on stderr otherwise -- missing
file, unparseable JSON, missing key, or a true/non-False value.

Usage: python3 scripts/check_manifest_no_raw_output.py <manifest.json>
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_manifest_no_raw_output.py <manifest.json>", file=sys.stderr)
        return 1

    manifest_path = sys.argv[1]
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"REJECT: {manifest_path} does not exist -- every submission needs a "
              f".manifest.json sidecar.", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"REJECT: {manifest_path} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    include_raw_output = manifest.get("include_raw_output")
    if include_raw_output is not False:
        print(
            f"REJECT: {manifest_path} include_raw_output={include_raw_output!r}, "
            f"expected False -- this submission may have been produced with "
            f"--include-raw-output and cannot be accepted. See CONTRIBUTING.md's "
            f"privacy policy.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {manifest_path} include_raw_output=False")
    return 0


if __name__ == "__main__":
    sys.exit(main())
