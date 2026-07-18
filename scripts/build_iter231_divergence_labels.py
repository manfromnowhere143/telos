#!/usr/bin/env python3
"""Derive the frozen divergence-type label for each of the 13 confirmed certified-yet-wrong patches.

The iter231 pre-registration requires recall split by divergence type: the crash/wrong-type subset a
gold-free execution oracle can reach, versus the plausible-but-wrong-value majority it cannot. That
split is ground truth about the patches, so it is derived from the committed gold-differential
witness logs of the originating runs -- NOT from any iter231 oracle output.

The separation that matters:

* the FLAG decision (``scripts/adjudicate_iter231.py``) is gold-free and reads only the iter231
  exercise ``RESULT=`` line. It never sees a witness.
* the divergence LABEL (this script) is gold-derived and is used only to stratify reporting.

Mixing them would let gold leak into the detector. Keeping them apart is what makes the split
meaningful: it says how the oracle did on a class defined independently of the oracle.

Labelling rule, fixed before any iter231 oracle output was inspected:

``crash_or_type``
    The variant witness observable is an error marker -- its repr's leading element names an
    exception, error, or failure. A gold-free exercise driving this code path sees the failure
    itself, with no reference needed.

``value``
    The variant witness returns a well-formed, plausible observable that differs from gold only
    under comparison against gold. No gold-free instrument can flag it, because recognizing it as
    wrong requires already knowing the right answer.

The boundary case is deliberate and is recorded rather than smoothed over. Where a variant returns a
different *type* but that type is itself a plausible return (for example ``matplotlib-25332`` under
iter229, where the accepted fix returns a dict and the patch returns a list), the label is ``value``.
"Wrong type" only counts as ``crash_or_type`` when the wrongness is visible without a reference; a
list where a dict belongs is invisible gold-free, so counting it as reachable would overstate the
oracle's ceiling -- the exact direction of error this experiment exists to avoid.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter231_gold_free_execution_oracle"
EVAL_SET = ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
OUT = EXP / "proof/raw/divergence_labels.json"

FROZEN_EVAL_SET_SHA256 = "10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"
SCHEMA = "telos.iter231.divergence_labels.v1"

# An error marker in the leading element of the witness repr. Matched against the first quoted token
# so that a value merely *containing* the word "error" is not miscounted as a failure.
LEADING_TOKEN_RE = re.compile(r"^\(?\s*['\"]([^'\"]+)['\"]")
ERROR_TOKEN_RE = re.compile(
    r"^(error|exception|timeout|traceback|failed|failure)$|(Error|Exception)$", re.IGNORECASE
)


def result_line(path: Path) -> str | None:
    if not path.is_file():
        return None
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("RESULT="):
            return line[len("RESULT="):]
    return None


def classify(variant_repr: str) -> str:
    match = LEADING_TOKEN_RE.match(variant_repr.strip())
    if match and ERROR_TOKEN_RE.search(match.group(1)):
        return "crash_or_type"
    return "value"


def build() -> dict:
    raw = EVAL_SET.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_EVAL_SET_SHA256:
        raise SystemExit("frozen iter230 benchmark sha changed; labels may not be rebuilt")
    positives = json.loads(raw)["positives"]
    if len(positives) != 13:
        raise SystemExit("benchmark positive denominator is not the frozen 13")

    rows = []
    for item in positives:
        run, iid = item["run"], item["instance_id"]
        execution = ROOT / f"experiments/{run}/proof/raw/execution"
        gold = result_line(execution / f"{iid}.gold.log")
        variant = result_line(execution / f"{iid}.variant.log")
        if gold is None or variant is None:
            raise SystemExit(f"missing gold-differential witness observable for {run}/{iid}")
        rows.append(
            {
                "divergence_type": classify(variant),
                "gold_observable": gold[:400],
                "instance_id": iid,
                "run": run,
                "variant_observable": variant[:400],
            }
        )

    crash = sum(1 for row in rows if row["divergence_type"] == "crash_or_type")
    return {
        "schema_version": SCHEMA,
        "source": "gold-differential witness logs of the originating runs",
        "eval_set_sha256": FROZEN_EVAL_SET_SHA256,
        "positives": len(rows),
        "crash_or_type": crash,
        "value": len(rows) - crash,
        "labels": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed labels regenerate")
    args = parser.parse_args()

    built = build()
    payload = json.dumps(built, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.is_file():
            print("iter231 divergence labels are not committed", file=sys.stderr)
            return 1
        if OUT.read_text() != payload:
            print("iter231 divergence labels do not regenerate from committed witness evidence",
                  file=sys.stderr)
            return 1
        print(
            f"iter231 divergence labels regenerate: {built['crash_or_type']} crash_or_type, "
            f"{built['value']} value, of {built['positives']}"
        )
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(payload)
    print(
        f"iter231 divergence labels: {built['crash_or_type']} crash_or_type, "
        f"{built['value']} value, of {built['positives']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
