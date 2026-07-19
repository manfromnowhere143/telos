#!/usr/bin/env python3
"""Adjudicate the iter231 gold-free execution oracle against the frozen iter230 benchmark.

Implements the flag rule frozen in ``ADJUDICATION_FREEZE.md`` before any oracle output existed. The
rule is gold-free by construction: it reads only the exercise's own ``RESULT=`` line and exit code,
and never compares an observable to gold, to another row, or to any expectation of the right answer.

The divergence-type labels used to stratify reporting are gold-derived and come from a separate
committed artifact. They classify the patches; they never touch the flag decision.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from telos.json_compare import compare_json  # noqa: E402

EXP = ROOT / "experiments/iter231_gold_free_execution_oracle"
EVAL_SET = ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
EXERCISES = EXP / "proof/raw/exercises/exercises_summary.json"
EXECUTION = EXP / "proof/raw/execution"
LABELS = EXP / "proof/raw/divergence_labels.json"
OUT = EXP / "proof/oracle_result.json"

FROZEN_EVAL_SET_SHA256 = "10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"
SCHEMA = "telos.iter231.oracle_result.v1"

# Iter230's static gold-free panel, for the side-by-side the pre-registration requires.
ITER230_STATIC_RECALL = (2, 13)
ITER230_STATIC_FPR = (5, 54)

LEADING_TOKEN_RE = re.compile(r"^\(?\s*['\"]([^'\"]+)['\"]")
ERROR_TOKEN_RE = re.compile(
    r"^(error|exception|timeout|traceback|failed|failure)$|(Error|Exception)$", re.IGNORECASE
)
EXIT_RE = re.compile(r"^EXERCISE_EXIT=(\d+)$", re.MULTILINE)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval; defined at k=0 and k=n, unlike the normal approximation."""

    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def exercise_has_format_bug(source: str) -> bool:
    """``print("RESULT=%r" % (a, b))`` -- one specifier against a multi-element tuple.

    Always raises ``TypeError: not all arguments converted during string formatting``, so the
    exercise dies while reporting rather than because the code under test failed. Detected from the
    committed exercise source, statically, with no reference to any run.
    """

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Mod)
            and isinstance(node.left, ast.Constant)
            and isinstance(node.left.value, str)
            and isinstance(node.right, ast.Tuple)
            and node.left.value.replace("%%", "").count("%") == 1
            and len(node.right.elts) > 1
        ):
            return True
    return False


def instrument_failure(text: str, source: str) -> str | None:
    """Why a row produced no observable, when that is attributable to the instrument.

    A flag raised by a broken exercise is not evidence about the patch. The oracle cannot make this
    call gold-free -- it is a post-hoc diagnostic, reported beside the frozen-rule numbers and never
    substituted for them.
    """

    if "ImportError" in text or "ModuleNotFoundError" in text:
        return "instrument_import_failure"
    if "not all arguments converted during string formatting" in text and exercise_has_format_bug(
        source
    ):
        return "instrument_format_failure"
    return None


def adjudicate_log(text: str) -> tuple[bool, list[str], str | None]:
    """Return (flagged, reasons, result_repr) under the frozen gold-free rule."""

    result = None
    for line in text.splitlines():
        if line.startswith("RESULT="):
            result = line[len("RESULT="):]
            break

    reasons: list[str] = []
    exits = EXIT_RE.findall(text)
    if exits and int(exits[0]) != 0:
        reasons.append("nonzero_exit")
    if result is not None:
        match = LEADING_TOKEN_RE.match(result.strip())
        if match and ERROR_TOKEN_RE.search(match.group(1)):
            reasons.append("error_observable")
        if result.strip() == "None":
            reasons.append("absent_value")
    return bool(reasons), reasons, result


def _rates(k: int, n: int, u: int) -> dict:
    """Observed lower, worst-case missing upper, and complete-case, always reported together."""

    return {
        "observed_lower": {"k": k, "n": n, "rate": round(k / n, 6) if n else None,
                           "wilson95": [round(value, 6) for value in wilson(k, n)]},
        "worst_case_missing_upper": {"k": k + u, "n": n,
                                     "rate": round((k + u) / n, 6) if n else None},
        "complete_case": {"k": k, "n": n - u,
                          "rate": round(k / (n - u), 6) if n - u else None},
        "missing_outcomes": u,
    }


def build() -> dict:
    raw = EVAL_SET.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_EVAL_SET_SHA256:
        raise SystemExit("frozen iter230 benchmark sha changed; adjudication may not proceed")
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
            "instrument_failure": None,
            "instance_id": key[1],
            "label": item["label"],
            "observable": None,
            "outcome": None,
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
        flagged, reasons, observable = adjudicate_log(text)
        # The frozen rule lists nonzero_exit as a flag condition in its own right, so a crashed
        # exercise is an observation even with no RESULT= line. Only a row that yields neither a
        # RESULT= nor any flag reason is genuinely missing.
        if observable is None and not reasons:
            row["outcome"] = "missing_no_result"
        else:
            row["outcome"] = "observed"
            row["flagged"] = flagged
            row["flag_reasons"] = reasons
            row["observable"] = observable[:400] if observable is not None else None
            if observable is None:
                source_path = EXP / f"proof/raw/exercises/{stem}.exercise.py"
                source = source_path.read_text() if source_path.is_file() else ""
                row["instrument_failure"] = instrument_failure(text, source)
        rows.append(row)

    def slice_rates(subset: list[dict]) -> dict:
        n = len(subset)
        observed = [row for row in subset if row["outcome"] == "observed"]
        k = sum(1 for row in observed if row["flagged"])
        return _rates(k, n, n - len(observed))

    positives = [row for row in rows if row["label"] == "certified_yet_wrong"]
    negatives = [row for row in rows if row["label"] == "certified_correct"]

    return {
        "schema_version": SCHEMA,
        "eval_set_sha256": FROZEN_EVAL_SET_SHA256,
        "flag_rule": "ADJUDICATION_FREEZE.md (frozen before any oracle output existed)",
        "recall": slice_rates(positives),
        "false_positive_rate": slice_rates(negatives),
        "recall_by_divergence_type": {
            divergence: slice_rates(
                [row for row in positives if row["divergence_type"] == divergence]
            )
            for divergence in ("crash_or_type", "value")
        },
        "iter230_static_baseline": {
            "recall": {"k": ITER230_STATIC_RECALL[0], "n": ITER230_STATIC_RECALL[1]},
            "false_positive_rate": {"k": ITER230_STATIC_FPR[0], "n": ITER230_STATIC_FPR[1]},
        },
        # Honest caveat on the flag counts, not a change to the frozen rule. A row flagged only by
        # nonzero_exit with no RESULT= line died before it could report -- which happens when the
        # PATCHED CODE crashes, but also when the EXERCISE ITSELF is broken (an import that does not
        # exist in the pinned image, a buggy except handler). Both were observed. The oracle cannot
        # tell them apart gold-free, so the count is published beside the rates rather than being
        # quietly folded into them.
        "flagged_without_observable": {
            "certified_yet_wrong": sum(
                1 for row in positives
                if row["flagged"] and row["observable"] is None
            ),
            "certified_correct": sum(
                1 for row in negatives
                if row["flagged"] and row["observable"] is None
            ),
            "note": "flagged by nonzero_exit alone; instrument failure is indistinguishable from "
                    "patched-code failure without a reference",
        },
        # Post-hoc diagnostic, NOT the pre-registered endpoint. Excludes flags raised by a broken
        # exercise rather than by the code under test. Reported beside the frozen-rule rates above,
        # never in place of them.
        "instrument_adjusted_diagnostic": {
            "recall_k": sum(
                1 for row in positives if row["flagged"] and not row["instrument_failure"]
            ),
            "recall_n": len(positives),
            "false_positive_k": sum(
                1 for row in negatives if row["flagged"] and not row["instrument_failure"]
            ),
            "false_positive_n": len(negatives),
            "instrument_failures": sorted(
                f"{row['run']}/{row['instance_id']}:{row['instrument_failure']}"
                for row in rows if row["instrument_failure"]
            ),
        },
        "missing_rows": [
            {"instance_id": row["instance_id"], "label": row["label"], "run": row["run"],
             "exercise_status": row["exercise_status"], "outcome": row["outcome"]}
            for row in rows if row["outcome"] != "observed"
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
        if not OUT.is_file():
            print("iter231 oracle result artifact is missing", file=sys.stderr)
            return 1
        try:
            committed = json.loads(OUT.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"iter231 oracle result artifact is unreadable: {exc}", file=sys.stderr)
            return 1
        problems = compare_json(committed, built)
        if problems:
            print(
                "iter231 oracle result does not regenerate from committed evidence",
                file=sys.stderr,
            )
            for problem in problems[:20]:
                print(f"  {problem}", file=sys.stderr)
            return 1
        print("iter231 oracle result regenerates from committed evidence")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(payload)

    recall = built["recall"]
    fpr = built["false_positive_rate"]
    print(
        f"iter231 oracle recall {recall['observed_lower']['k']}/{recall['observed_lower']['n']} "
        f"(upper {recall['worst_case_missing_upper']['k']}/{recall['worst_case_missing_upper']['n']}, "
        f"complete-case {recall['complete_case']['k']}/{recall['complete_case']['n']}); "
        f"false positives {fpr['observed_lower']['k']}/{fpr['observed_lower']['n']} "
        f"(upper {fpr['worst_case_missing_upper']['k']}/{fpr['worst_case_missing_upper']['n']})"
    )
    for divergence, rates in built["recall_by_divergence_type"].items():
        print(f"  {divergence}: {rates['observed_lower']['k']}/{rates['observed_lower']['n']} "
              f"(missing {rates['missing_outcomes']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
