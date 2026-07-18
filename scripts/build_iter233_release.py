#!/usr/bin/env python3
"""Build the natural certified-yet-wrong benchmark release from committed evidence.

The design problem is leakage, not packaging. A benchmark that ships its answers next to its inputs measures
nothing, so the release is split into two directories with different contracts:

* ``inputs/``  - exactly what a gold-free detector may see: issue text, public FAIL_TO_PASS test names, and
  the candidate patch.
* ``answers/`` - the label, the gold-differential witness observables, and the divergence-type label. Enough
  to score, and enough to cheat.

The separation is machine-checked by ``validate_iter233_release.py`` over the built artifact rather than
asserted here. This script only builds; it makes no provider call and produces no detector number.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter233_natural_benchmark_release"
RELEASE = EXP / "release"
EVAL_SET = ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
LABELS = ROOT / "experiments/iter231_gold_free_execution_oracle/proof/raw/divergence_labels.json"
EXERCISES = ROOT / "experiments/iter232_validated_exercise_instrument/proof/raw/exercises"
SNAPSHOT = ROOT / (
    "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/"
    "swebench_verified_rows_snapshot.json"
)

FROZEN_EVAL_SET_SHA256 = "10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"
SCHEMA = "telos.iter233.benchmark_release.v1"
POSITIVES, NEGATIVES = 13, 54


def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_rows() -> list[dict]:
    raw = EVAL_SET.read_bytes()
    if digest_bytes(raw) != FROZEN_EVAL_SET_SHA256:
        raise SystemExit("frozen benchmark sha changed; release may not be built")
    data = json.loads(raw)
    if len(data["positives"]) != POSITIVES or len(data["negatives"]) != NEGATIVES:
        raise SystemExit("benchmark denominators are not the frozen 13/54")
    rows = [dict(r, label="certified_yet_wrong") for r in data["positives"]]
    rows += [dict(r, label="certified_correct") for r in data["negatives"]]
    return rows


def build() -> dict:
    rows = load_rows()
    sources = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    divergence = {
        (r["run"], r["instance_id"]): r
        for r in json.loads(LABELS.read_text())["labels"]
    }
    exercise_manifest = {
        (r["run"], r["instance_id"]): r
        for r in json.loads((EXERCISES / "exercises_summary.json").read_text())["manifest"]
    }

    inputs_dir = RELEASE / "inputs"
    answers_dir = RELEASE / "answers"
    for directory in (inputs_dir, answers_dir):
        directory.mkdir(parents=True, exist_ok=True)

    index, answers = [], []
    for row in rows:
        run, iid = row["run"], row["instance_id"]
        # Opaque, deterministic row id. The originating RUN NAME must not ship in inputs/: one of them
        # is literally "iter200_natural_certified_yet_wrong_rate", and although it does not determine a
        # row's label (that run contributed both positives and negatives), shipping a suggestive
        # provenance string in an eval input invites a detector to key on it instead of on the patch.
        row_id = "row-" + hashlib.sha256(f"{run}\0{iid}".encode()).hexdigest()[:12]
        source = sources[iid]
        patch_raw = (ROOT / row["model_patch_path"]).read_bytes()
        payload = patch_raw[:-1] if patch_raw.endswith(b"\n") else patch_raw
        if digest_bytes(payload) != row["model_patch_sha256"]:
            raise SystemExit(f"candidate patch hash mismatch for {row_id}")

        # inputs/: certification-time information only.
        (inputs_dir / f"{row_id}.patch").write_bytes(patch_raw)
        task = {
            "row_id": row_id,
            "instance_id": iid,
            "repo": source["repo"],
            "base_commit": source["base_commit"],
            "problem_statement": source["problem_statement"],
            "public_tests_fail_to_pass": json.loads(source["FAIL_TO_PASS"]),
            "candidate_patch_file": f"{row_id}.patch",
            "candidate_patch_sha256": row["model_patch_sha256"],
            "solver_model": row.get("solver_model"),
        }
        (inputs_dir / f"{row_id}.task.json").write_text(
            json.dumps(task, indent=2, sort_keys=True) + "\n"
        )
        index.append(
            {"row_id": row_id, "instance_id": iid, "repo": source["repo"],
             "candidate_patch_sha256": row["model_patch_sha256"]}
        )

        # answers/: label, witness, divergence type.
        # Provenance lives with the answers, never with the inputs.
        answer = {"row_id": row_id, "instance_id": iid, "source_run": run, "label": row["label"]}
        witness = divergence.get((run, iid))
        if witness is not None:
            answer["divergence_type"] = witness["divergence_type"]
            answer["witness_gold_observable"] = witness["gold_observable"]
            answer["witness_candidate_observable"] = witness["variant_observable"]
        else:
            answer["divergence_type"] = None
            answer["note"] = "negatives carry no gold-differential witness"
        answers.append(answer)

    # The validated exercises ship as an optional reference instrument, clearly separated: they are an
    # artifact of one detector design, not part of the task definition, and a user testing their own
    # detector should not be handed ours as if it were the benchmark.
    reference_dir = RELEASE / "reference_exercises"
    reference_dir.mkdir(parents=True, exist_ok=True)
    shipped = 0
    for row in rows:
        run, iid = row["run"], row["instance_id"]
        row_id = f"{run}__{iid.replace('/', '__')}"
        manifest_row = exercise_manifest.get((run, iid))
        if not manifest_row or manifest_row["status"] != "exercise":
            continue
        source_path = EXERCISES / f"{run}__{iid.replace('/', '__')}.exercise.py"
        if source_path.is_file():
            (reference_dir / f"{row_id}.exercise.py").write_bytes(source_path.read_bytes())
            shipped += 1

    (RELEASE / "index.json").write_text(
        json.dumps(
            {
                "schema_version": SCHEMA,
                "eval_set_sha256": FROZEN_EVAL_SET_SHA256,
                "positives": POSITIVES,
                "negatives": NEGATIVES,
                "rows": len(index),
                "reference_exercises": shipped,
                "index": index,
            },
            indent=2, sort_keys=True,
        ) + "\n"
    )
    (RELEASE / "answers" / "answers.json").write_text(
        json.dumps(
            {"schema_version": "telos.iter233.answers.v1", "answers": answers},
            indent=2, sort_keys=True,
        ) + "\n"
    )
    return {"rows": len(index), "reference_exercises": shipped}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed release rebuilds")
    args = parser.parse_args()

    if args.check:
        if not (RELEASE / "index.json").is_file():
            print("iter233 release is not committed", file=sys.stderr)
            return 1
        before = {
            path: path.read_bytes()
            for path in sorted(RELEASE.rglob("*")) if path.is_file()
        }
        build()
        after = {
            path: path.read_bytes()
            for path in sorted(RELEASE.rglob("*")) if path.is_file()
        }
        if before != after:
            changed = sorted(
                str(p.relative_to(RELEASE))
                for p in set(before) | set(after)
                if before.get(p) != after.get(p)
            )
            print(f"iter233 release does not rebuild identically: {changed[:5]}", file=sys.stderr)
            return 1
        print(f"iter233 release rebuilds identically: {len(after)} files")
        return 0

    summary = build()
    print(
        f"iter233 release built: {summary['rows']} rows "
        f"({POSITIVES} positive, {NEGATIVES} negative), "
        f"{summary['reference_exercises']} reference exercises"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
