#!/usr/bin/env python3
"""Adjudicate the iter232 oracle — the same rule, a repaired instrument.

The flag rule is **imported from** ``scripts/adjudicate_iter231.py`` rather than restated here. That is
deliberate: iter232's acceptance bars require the iter231 rule to be applied byte-identically, and importing
the function makes that structural rather than a promise a reader has to verify by diffing two copies. If the
iter231 rule ever changes, this changes with it and the divergence is visible in one place.

What iter232 changes is the *instrument*, not the decision. The one adjudication difference is that
instrument-invalidity is now read from committed stage B evidence — the container's own ``PREFLIGHT=``
verdict — instead of being inferred after the fact from tracebacks and exercise source. Iter231 had to guess
whether a crash came from the patch or from the harness; iter232 measures it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# The frozen rule, imported not copied.
from scripts.adjudicate_iter231 import (  # noqa: E402
    ITER230_STATIC_FPR,
    ITER230_STATIC_RECALL,
    _rates,
    adjudicate_log,
)

EXP = ROOT / "experiments/iter232_validated_exercise_instrument"
PRIOR_FREEZE = ROOT / "experiments/iter231_gold_free_execution_oracle/ADJUDICATION_FREEZE.md"
EVAL_SET = ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
EXERCISES = EXP / "proof/raw/exercises/exercises_summary.json"
EXECUTION = EXP / "proof/raw/execution"
LABELS = ROOT / (
    "experiments/iter231_gold_free_execution_oracle/proof/raw/divergence_labels.json"
)
OUT = EXP / "proof/oracle_result.json"

FROZEN_EVAL_SET_SHA256 = "10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"
# Acceptance bar 2: the frozen flag rule is byte-identical to its iter231 commit.
FROZEN_FREEZE_SHA256 = "f1103f3f85225dada369705e19f19b6ea4f332b60e6f99fb8e5973159453d8dd"
SCHEMA = "telos.iter232.oracle_result.v1"

PREFLIGHT_RE = re.compile(r"^PREFLIGHT=(.*)$", re.MULTILINE)
ITER231_RESULT = ROOT / (
    "experiments/iter231_gold_free_execution_oracle/proof/oracle_result.json"
)


def preflight_verdict(text: str) -> tuple[str, str | None]:
    """('ok'|'error'|'missing', detail) from the container's own stage B verdict."""

    match = PREFLIGHT_RE.search(text)
    if not match:
        return "missing", None
    value = match.group(1).strip()
    if value.startswith("('ERROR'"):
        return "error", value[:200]
    return "ok", value[:200]


def build() -> dict:
    raw = EVAL_SET.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_EVAL_SET_SHA256:
        raise SystemExit("frozen iter230 benchmark sha changed; adjudication may not proceed")
    if hashlib.sha256(PRIOR_FREEZE.read_bytes()).hexdigest() != FROZEN_FREEZE_SHA256:
        raise SystemExit("iter231 ADJUDICATION_FREEZE.md changed; the frozen rule is not intact")

    data = json.loads(raw)
    items = [dict(row, label="certified_yet_wrong") for row in data["positives"]]
    items += [dict(row, label="certified_correct") for row in data["negatives"]]

    manifest = {
        (row["run"], row["instance_id"]): row
        for row in json.loads(EXERCISES.read_text())["manifest"]
    }
    labels = {
        (row["run"], row["instance_id"]): row["divergence_type"]
        for row in json.loads(LABELS.read_text())["labels"]
    }

    rows = []
    for item in items:
        key = (item["run"], item["instance_id"])
        stem = f"{key[0]}__{key[1].replace('/', '__')}"
        status = manifest[key]["status"]
        log_path = EXECUTION / f"{stem}.oracle.log"
        row = {
            "divergence_type": labels.get(key),
            "exercise_status": status,
            "flag_reasons": [],
            "flagged": False,
            "instance_id": key[1],
            "instrument_valid": None,
            "label": item["label"],
            "observable": None,
            "outcome": None,
            "preflight": None,
            "run": key[0],
        }
        if status != "exercise":
            row["outcome"] = "missing_no_exercise"
            rows.append(row)
            continue
        if not log_path.is_file():
            row["outcome"] = "missing_no_log"
            rows.append(row)
            continue

        text = log_path.read_text(errors="replace")
        verdict, detail = preflight_verdict(text)
        row["preflight"] = detail
        row["instrument_valid"] = verdict == "ok"

        flagged, reasons, observable = adjudicate_log(text)
        if observable is None and not reasons:
            row["outcome"] = "missing_no_result"
        else:
            row["outcome"] = "observed"
            row["flagged"] = flagged
            row["flag_reasons"] = reasons
            row["observable"] = observable[:400] if observable is not None else None
        rows.append(row)

    def slice_rates(subset: list[dict]) -> dict:
        n = len(subset)
        observed = [r for r in subset if r["outcome"] == "observed"]
        k = sum(1 for r in observed if r["flagged"])
        return _rates(k, n, n - len(observed))

    positives = [r for r in rows if r["label"] == "certified_yet_wrong"]
    negatives = [r for r in rows if r["label"] == "certified_correct"]

    prior = json.loads(ITER231_RESULT.read_text()) if ITER231_RESULT.is_file() else {}

    return {
        "schema_version": SCHEMA,
        "eval_set_sha256": FROZEN_EVAL_SET_SHA256,
        "flag_rule": "iter231 ADJUDICATION_FREEZE.md, imported unchanged",
        "flag_rule_sha256": FROZEN_FREEZE_SHA256,
        "recall": slice_rates(positives),
        "false_positive_rate": slice_rates(negatives),
        "recall_by_divergence_type": {
            divergence: slice_rates([r for r in positives if r["divergence_type"] == divergence])
            for divergence in ("crash_or_type", "value")
        },
        # Stage B turns iter231's post-hoc guess into committed measurement: the container itself says
        # whether the exercise could import. A row that fails stage B is not evidence about the patch.
        "stage_b": {
            "instrument_valid": sum(1 for r in rows if r["instrument_valid"] is True),
            "instrument_invalid": sum(1 for r in rows if r["instrument_valid"] is False),
            "invalid_rows": sorted(
                f"{r['run']}/{r['instance_id']}: {r['preflight']}"
                for r in rows if r["instrument_valid"] is False
            ),
        },
        "instrument_valid_only": {
            "recall_k": sum(
                1 for r in positives if r["flagged"] and r["instrument_valid"] is True
            ),
            "recall_n": len(positives),
            "false_positive_k": sum(
                1 for r in negatives if r["flagged"] and r["instrument_valid"] is True
            ),
            "false_positive_n": len(negatives),
        },
        "comparison": {
            "iter230_static": {
                "recall": list(ITER230_STATIC_RECALL), "false_positive": list(ITER230_STATIC_FPR),
            },
            "iter231_oracle": {
                "recall": [
                    prior.get("recall", {}).get("observed_lower", {}).get("k"),
                    prior.get("recall", {}).get("observed_lower", {}).get("n"),
                ],
                "false_positive": [
                    prior.get("false_positive_rate", {}).get("observed_lower", {}).get("k"),
                    prior.get("false_positive_rate", {}).get("observed_lower", {}).get("n"),
                ],
            },
        },
        "missing_rows": [
            {"instance_id": r["instance_id"], "label": r["label"], "run": r["run"],
             "exercise_status": r["exercise_status"], "outcome": r["outcome"]}
            for r in rows if r["outcome"] != "observed"
        ],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    built = build()
    payload = json.dumps(built, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.is_file() or OUT.read_text() != payload:
            print("iter232 oracle result does not regenerate", file=sys.stderr)
            return 1
        print("iter232 oracle result regenerates from committed evidence")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(payload)

    recall, fpr = built["recall"], built["false_positive_rate"]
    valid = built["instrument_valid_only"]
    print(
        f"iter232 recall {recall['observed_lower']['k']}/{recall['observed_lower']['n']} "
        f"(upper {recall['worst_case_missing_upper']['k']}/{recall['worst_case_missing_upper']['n']}); "
        f"false positives {fpr['observed_lower']['k']}/{fpr['observed_lower']['n']}"
    )
    print(
        f"  instrument-valid only: recall {valid['recall_k']}/{valid['recall_n']}, "
        f"FPR {valid['false_positive_k']}/{valid['false_positive_n']}"
    )
    print(f"  stage B: {built['stage_b']['instrument_valid']} valid, "
          f"{built['stage_b']['instrument_invalid']} invalid")
    for divergence, rates in built["recall_by_divergence_type"].items():
        print(f"  {divergence}: {rates['observed_lower']['k']}/{rates['observed_lower']['n']} "
              f"(missing {rates['missing_outcomes']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
