#!/usr/bin/env python3
"""Leakage and integrity guard for the iter233 benchmark release.

A benchmark that ships its answers next to its inputs measures nothing. This scans the BUILT ARTIFACT rather
than trusting the builder, and fails closed if anything under ``inputs/`` could tell a gold-free detector the
answer.

Four leakage channels are checked, because each one alone is sufficient to void the benchmark:

1. **Gold patches.** The accepted fix for any benchmark instance must not appear, in whole or as a
   distinctive contiguous fragment, anywhere under ``inputs/``.
2. **Witness observables.** The gold/candidate divergence strings are what make a positive *confirmed*;
   seeing one identifies the row.
3. **Labels.** No ``certified_yet_wrong`` / ``certified_correct`` marker, and no field name that encodes one.
4. **Hidden tests.** ``PASS_TO_PASS`` names are not certification-time information and must not ship.

Integrity is checked alongside: the frozen sha, the 13/54 denominators, and every candidate patch hashing to
its committed value.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter233_natural_benchmark_release"
RELEASE = EXP / "release"
INPUTS = RELEASE / "inputs"
ANSWERS = RELEASE / "answers"
EVAL_SET = ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
LABELS = ROOT / "experiments/iter231_gold_free_execution_oracle/proof/raw/divergence_labels.json"
SNAPSHOT = ROOT / (
    "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/"
    "swebench_verified_rows_snapshot.json"
)
README = EXP / "release/README.md"

FROZEN_EVAL_SET_SHA256 = "10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"
POSITIVES, NEGATIVES = 13, 54
# Long enough that a coincidental match is implausible, short enough to catch a partial paste.
GOLD_FRAGMENT = 120
LABEL_MARKERS = ("certified_yet_wrong", "certified_correct", "divergence_type", "is_hack")


def leakage_errors() -> list[str]:
    errors: list[str] = []
    if not INPUTS.is_dir():
        return ["release inputs/ directory is missing"]

    corpus = {
        path: path.read_text(errors="replace")
        for path in sorted(INPUTS.rglob("*")) if path.is_file()
    }
    blob = "\n".join(corpus.values())

    sources = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    data = json.loads(EVAL_SET.read_bytes())
    instances = {r["instance_id"] for r in data["positives"] + data["negatives"]}

    # A candidate patch that IS the gold patch is not a packaging leak; it is a property of the
    # benchmark, since 29 of the 54 negatives certified by being gold-equivalent. That defect is
    # disclosed in the release README and checked separately below. What must not happen is gold text
    # appearing anywhere it is not the row's own candidate patch -- in a task.json, or under another
    # row's files -- which would hand a detector the answer for a row it is scoring.
    # Row ids are opaque, so "is this my own patch?" must be resolved through the index rather than
    # by looking for the instance id in the filename. The same SWE-bench instance legitimately appears
    # as several rows (different solver runs), and gold matching any of those rows' candidates is
    # inherent, not a packaging leak.
    index_rows = json.loads((RELEASE / "index.json").read_text())["index"]
    instance_of_row = {r["row_id"]: r["instance_id"] for r in index_rows}
    candidate_texts = {
        path.stem: text for path, text in corpus.items() if path.suffix == ".patch"
    }
    # The problem statement is legitimate certification-time input and cannot be redacted without
    # destroying the task. Some SWE-bench issues contain the fix because the reporter proposed it --
    # django-11951's issue literally writes out the accepted one-liner. A detector reading that is
    # doing what a human reviewer would. It is a disclosed property of the benchmark, counted below,
    # not a packaging leak, so gold matching inside a problem_statement is exempt.
    # Scan the PARSED task fields, excluding problem_statement, rather than raw JSON text: the raw
    # file escapes newlines and unicode, so a gold fragment would never match it literally and the
    # exemption would silently do nothing.
    non_candidate_parts = []
    for path, text in corpus.items():
        if path.suffix == ".patch":
            continue  # candidate patches are checked separately, by row ownership
        if path.suffix != ".json":
            non_candidate_parts.append(text)
            continue
        task = json.loads(text)
        task.pop("problem_statement", None)
        non_candidate_parts.append(json.dumps(task, sort_keys=True))
    non_candidate_blob = "\n".join(non_candidate_parts)

    for iid in sorted(instances):
        source = sources[iid]
        # Only the ADDED lines are the fix. Two patches to the same file share context and removed
        # lines, and matching on those reported two sphinx rows as leaking into each other when they
        # merely edit the same region. The answer is what the gold patch ADDS.
        gold = "\n".join(
            line for line in (source.get("patch") or "").splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ).strip()
        if len(gold) >= GOLD_FRAGMENT:
            for offset in (0, len(gold) // 2, max(0, len(gold) - GOLD_FRAGMENT)):
                fragment = gold[offset:offset + GOLD_FRAGMENT]
                if not fragment:
                    continue
                if fragment in non_candidate_blob:
                    errors.append(f"gold patch fragment for {iid} appears outside a candidate patch")
                    break
                foreign = [
                    row_id for row_id, text in candidate_texts.items()
                    if fragment in text and instance_of_row.get(row_id) != iid
                ]
                if foreign:
                    errors.append(
                        f"gold patch fragment for {iid} appears in another row's patch: {foreign[0]}"
                    )
                    break
        # Name boundaries matter: a hidden test name is frequently a strict PREFIX of a published one
        # (`::test_loc` of `::test_loc_dim_name_collision_...`, `::test_clone` of
        # `::test_clone_estimator_types`). Substring matching reported those as leaks; they are not.
        # A hidden name only leaks if it appears as a COMPLETE identifier.
        published = set(json.loads(source.get("FAIL_TO_PASS") or "[]"))
        for name in json.loads(source.get("PASS_TO_PASS") or "[]"):
            if not isinstance(name, str) or len(name) <= 12 or name in published:
                continue
            start = 0
            while True:
                position = blob.find(name, start)
                if position < 0:
                    break
                after = blob[position + len(name):position + len(name) + 1]
                if not (after.isalnum() or after in "_-."):
                    errors.append(
                        f"hidden PASS_TO_PASS test name for {iid} appears under inputs/"
                    )
                    break
                start = position + 1
            else:
                continue
            break

    for row in json.loads(LABELS.read_text())["labels"]:
        for field in ("gold_observable", "variant_observable"):
            value = (row.get(field) or "").strip()
            if len(value) >= 24 and value in blob:
                errors.append(
                    f"witness {field} for {row['instance_id']} appears under inputs/"
                )

    for marker in LABEL_MARKERS:
        for path, text in corpus.items():
            if marker in text:
                errors.append(f"label marker {marker!r} appears in inputs/{path.name}")
                break
    return errors


def disclosed_properties() -> dict:
    """Benchmark properties a user must know, computed rather than asserted.

    These are not defects in the packaging; they are facts about the underlying data that determine
    what the benchmark can and cannot support. They are surfaced here so the release README states
    measured numbers rather than adjectives.
    """

    sources = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    data = json.loads(EVAL_SET.read_bytes())
    gold_identical_negatives = 0
    gold_identical_positives = 0
    fix_in_issue = set()
    for label, group in (("neg", data["negatives"]), ("pos", data["positives"])):
        for row in group:
            source = sources[row["instance_id"]]
            candidate = (ROOT / row["model_patch_path"]).read_text().rstrip("\n")
            gold = (source.get("patch") or "").rstrip("\n")
            if candidate == gold:
                if label == "neg":
                    gold_identical_negatives += 1
                else:
                    gold_identical_positives += 1
            added = "\n".join(
                line for line in gold.splitlines()
                if line.startswith("+") and not line.startswith("+++")
            ).strip()
            issue = source.get("problem_statement") or ""
            if len(added) >= 60 and any(
                added[offset:offset + 60] and added[offset:offset + 60] in issue
                for offset in (0, len(added) // 2, max(0, len(added) - 60))
            ):
                fix_in_issue.add(row["instance_id"])
    return {
        "gold_identical_negatives": gold_identical_negatives,
        "gold_identical_positives": gold_identical_positives,
        "instances_with_fix_in_issue": len(fix_in_issue),
    }


def integrity_errors() -> list[str]:
    errors: list[str] = []
    raw = EVAL_SET.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_EVAL_SET_SHA256:
        return ["frozen benchmark sha changed"]
    data = json.loads(raw)
    rows = [dict(r, label="certified_yet_wrong") for r in data["positives"]]
    rows += [dict(r, label="certified_correct") for r in data["negatives"]]

    index_path = RELEASE / "index.json"
    if not index_path.is_file():
        return ["release index.json is missing"]
    index = json.loads(index_path.read_text())
    if index.get("positives") != POSITIVES or index.get("negatives") != NEGATIVES:
        errors.append("release index denominators are not the frozen 13/54")
    if index.get("rows") != len(rows):
        errors.append("release index row count does not match the benchmark")

    answers_path = ANSWERS / "answers.json"
    if not answers_path.is_file():
        errors.append("release answers.json is missing")
    else:
        answers = json.loads(answers_path.read_text())["answers"]
        if len(answers) != len(rows):
            errors.append("answers do not cover every benchmark row")
        positives = sum(1 for a in answers if a["label"] == "certified_yet_wrong")
        if positives != POSITIVES:
            errors.append(f"answers carry {positives} positives, expected {POSITIVES}")

    for row in rows:
        row_id = "row-" + hashlib.sha256(
            f"{row['run']}\0{row['instance_id']}".encode()
        ).hexdigest()[:12]
        patch = INPUTS / f"{row_id}.patch"
        task = INPUTS / f"{row_id}.task.json"
        if not patch.is_file() or not task.is_file():
            errors.append(f"release is missing input files for {row_id}")
            continue
        raw_patch = patch.read_bytes()
        payload = raw_patch[:-1] if raw_patch.endswith(b"\n") else raw_patch
        if hashlib.sha256(payload).hexdigest() != row["model_patch_sha256"]:
            errors.append(f"released candidate patch hash mismatch for {row_id}")
    return errors


def readme_errors() -> list[str]:
    """The release must carry its own limitations, not rely on the repository around it."""

    if not README.is_file():
        return ["release README.md is missing"]
    # Whitespace-normalised: a required phrase must not be defeatable by a Markdown line wrap. This
    # repository has already been bitten once by a required-phrase scanner that a line break could
    # slip past, and this README wraps at 110 columns.
    raw = README.read_text()
    text = " ".join(raw.split())
    errors = []
    for required in ("13", "Wilson", "contamination", "not a leaderboard"):
        if " ".join(required.lower().split()) not in text.lower():
            errors.append(f"release README does not state: {required}")
    for forbidden in ("state-of-the-art", "SOTA", "outperforms"):
        if forbidden.lower() in text.lower():
            errors.append(f"release README makes a forbidden claim: {forbidden}")
    return errors


def main() -> int:
    errors = leakage_errors() + integrity_errors() + readme_errors()
    if errors:
        for error in errors:
            print(f"iter233 release error: {error}", file=sys.stderr)
        return 1
    inputs = len(list(INPUTS.glob("*")))
    properties = disclosed_properties()
    print(
        f"iter233 release: {inputs} input files, zero leakage hits across gold patches, "
        "hidden tests, witnesses, and labels"
    )
    print(
        f"  disclosed: {properties['gold_identical_negatives']}/{NEGATIVES} negatives are "
        f"byte-identical to public gold ({properties['gold_identical_positives']}/{POSITIVES} "
        f"positives); {properties['instances_with_fix_in_issue']} instances have the fix in the issue"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
