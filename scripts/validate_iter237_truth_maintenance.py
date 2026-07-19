#!/usr/bin/env python3
"""Re-derive and validate the additive iter237 scientific correction.

This guard is deliberately narrower than a claim registry.  It binds the four
claims named by iter237 (T1--T4) to committed builders and retained artifacts,
checks that the iter235 predecessor still matches its merged-master bytes, and
requires the additive correction result to state the same claim boundary.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from telos.json_compare import compare_json  # noqa: E402


ITER237 = ROOT / "experiments/iter237_truth_maintenance_gate"
CORRECTION = ITER237 / "proof/correction.json"
RESULT = ITER237 / "RESULT.md"
ITER236_BUILDER = ROOT / "scripts/build_iter236_transfer_analysis.py"
SEALED_PREFIX = "experiments/iter235_witness_recovery"
SEALED_REFERENCE_COMMIT = "27e8f5ab44db637be24eb8eee96b283cc2cf0da4"

RUNS = (
    "iter200_natural_certified_yet_wrong_rate",
    "iter223_natural_rate_safety_aware",
    "iter225_cross_model_generalization",
    "iter226_cross_model_generalization_gpt54",
    "iter227_cross_provider_generalization",
    "iter229_cross_provider_gemini",
)
FIXED_COHORT_RUNS = RUNS[1:]
DISPLAY_NAMES = {
    "iter200_natural_certified_yet_wrong_rate": "iter200",
    "iter223_natural_rate_safety_aware": "iter223",
    "iter225_cross_model_generalization": "iter225",
    "iter226_cross_model_generalization_gpt54": "iter226",
    "iter227_cross_provider_generalization": "iter227",
    "iter229_cross_provider_gemini": "iter229",
}


class EvidenceError(RuntimeError):
    """Raised when a source artifact cannot support the registered derivation."""


def validate_structural_source_rule_source(
    source: str,
    *,
    path: str = "<memory>",
) -> list[str]:
    """Require iter236 to execute, rather than restate, the imported source rule."""

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [f"{path}: source-rule implementation is not parseable: {exc.msg}"]

    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "added_source_lines"
    ]
    if len(functions) != 1:
        return [f"{path}: expected exactly one added_source_lines function"]
    function = functions[0]

    def is_imported_call(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "one_src"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "adv"
        )

    assignments = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "current_included"
            for target in node.targets
        )
    ]
    if not any(any(is_imported_call(node) for node in ast.walk(item.value)) for item in assignments):
        return [
            f"{path}: added_source_lines does not obtain current_included "
            "by executing imported adv.one_src"
        ]

    restated_literals = sorted(
        {
            node.value
            for node in ast.walk(function)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and ("/test" in node.value or "test_" in node.value)
        }
    )
    if restated_literals:
        return [
            f"{path}: added_source_lines restates source-rule literals: "
            + ", ".join(repr(value) for value in restated_literals)
        ]
    return []


def validate_structural_source_rule(path: Path = ITER236_BUILDER) -> list[str]:
    """Validate the active iter236 source-rule implementation."""

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read iter236 source-rule implementation: {exc}"]
    return validate_structural_source_rule_source(source, path=str(path))


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise EvidenceError(f"cannot import evidence builder {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read JSON evidence {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"JSON evidence must be an object: {path}")
    return value


def _records(document: dict, key: str) -> list[dict]:
    value = document.get(key)
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise EvidenceError(f"expected object array at {key}")
    return value


def _derive_transfer() -> dict:
    builder = _load_module(
        ITER236_BUILDER,
        "iter237_iter236_builder",
    )
    rebuilt = builder.build()
    transfer = rebuilt.get("transfer")
    held_out = rebuilt.get("held_out")
    if not isinstance(transfer, dict) or not isinstance(held_out, dict):
        raise EvidenceError("iter236 rebuild lacks transfer or held-out accounting")

    expected_selector_keys = {
        "threshold_rule",
        "threshold",
        "held_out_evaluated",
        "selected_fraction",
    }
    selectors: dict[str, dict] = {}
    for name in ("added", "added_per_f2p", "added_per_graded"):
        record = transfer.get(name)
        if not isinstance(record, dict) or set(record) != expected_selector_keys:
            raise EvidenceError(
                f"iter236 {name} schema changed; review the T1 outcome boundary"
            )
        selectors[name] = {
            "held_out_evaluated": record["held_out_evaluated"],
            "selected_fraction": record["selected_fraction"],
            "threshold": record["threshold"],
        }

    if set(held_out) != {"count", "median_added"}:
        raise EvidenceError(
            "iter236 held-out schema changed; review the T1 outcome boundary"
        )

    within = rebuilt.get("within_cohort")
    if not isinstance(within, dict):
        raise EvidenceError("iter236 rebuild lacks within-cohort statistics")

    return {
        "status": "untested",
        "registered_held_out_rows": held_out["count"],
        "registered_outcome_endpoint": None,
        "registered_outcome_labels": 0,
        "selectors": selectors,
        "basis": (
            "The registered reconstruction contains held-out selector prevalence "
            "but no candidate-patch susceptibility endpoint."
        ),
        "exploratory_within_cohort": {
            "mannwhitney_u": within["mannwhitney_u"],
            "p_two_sided_asymptotic_tie_continuity": within["p_two_sided"],
        },
    }


def _derive_fresh_cohorts(reused_reference: dict) -> dict:
    paths = {
        "iter224": (
            ROOT
            / "experiments/iter224_natural_rate_scale_n/proof/audit_report.json"
        ),
        "iter228": (
            ROOT
            / "experiments/iter228_fresh_diverse_cohort/proof/audit_report.json"
        ),
    }
    cohorts: dict[str, dict[str, int]] = {}
    for name, path in paths.items():
        audit = _read_json(path)
        funnel = audit.get("funnel")
        if not isinstance(funnel, dict):
            raise EvidenceError(f"{name} audit lacks funnel accounting")
        cohorts[name] = {
            "k": funnel["blind_confirmed_natural_hacks"],
            "N": funnel["certified_model_patches"],
            "u": funnel["certified_outcome_unadjudicated"],
        }

    total = {
        key: sum(cohort[key] for cohort in cohorts.values())
        for key in ("k", "N", "u")
    }
    fresh_worst = total["k"] + total["u"]
    concentration_admitted = (
        fresh_worst * reused_reference["N"]
        < reused_reference["k"] * total["N"]
    )
    return {
        "status": "supported" if concentration_admitted else "inconclusive",
        "cohorts": cohorts,
        "total": total,
        "least_favourable": {"numerator": fresh_worst, "denominator": total["N"]},
        "reused_reference": reused_reference,
        "registered_strict_inequality_holds": concentration_admitted,
        "basis": (
            "The concentration claim requires (k_fresh + u_fresh) / N_fresh "
            "< k_reused / N_reused."
        ),
    }


def _execution_log_is_complete(run: str, instance_id: str) -> bool:
    path = (
        ROOT
        / "experiments/iter235_witness_recovery/proof/raw/execution"
        / f"{run}__{instance_id}.witness.log"
    )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return (
        text.count("RESULT=") == 2
        and "EXIT candidate=0" in text
        and "EXIT gold=0" in text
    )


def _derive_recurrence() -> dict:
    target_builder = _load_module(
        ROOT / "scripts/build_iter235_targets.py",
        "iter237_iter235_target_builder",
    )
    target_rebuild = target_builder.build()
    target_runs = target_rebuild.get("runs")
    if not isinstance(target_runs, dict):
        raise EvidenceError("iter235 target rebuild lacks per-run accounting")

    witness_document = _read_json(
        ROOT
        / "experiments/iter235_witness_recovery/proof/raw/witnesses"
        / "witnesses_summary.json"
    )
    witness_rows = _records(witness_document, "manifest")
    recovered = {
        (row["run"], row["instance_id"])
        for row in witness_rows
        if row.get("status") == "witness"
    }
    incomplete_logs = sorted(
        f"{run}/{instance_id}"
        for run, instance_id in recovered
        if not _execution_log_is_complete(run, instance_id)
    )
    if incomplete_logs:
        raise EvidenceError(
            "iter235 recovered rows lack complete two-arm execution logs: "
            + ", ".join(incomplete_logs)
        )

    recovery_judges = _read_json(
        ROOT
        / "experiments/iter235_witness_recovery/proof/raw/judge/judge_summary.json"
    )
    recovery_verdicts = _records(recovery_judges, "verdicts")
    new_positives = {
        (row["run"], row["instance_id"])
        for row in recovery_verdicts
        if row.get("confirmed") is True
    }
    if not new_positives <= recovered:
        raise EvidenceError("iter235 confirms a row outside the recovered execution set")

    eval_set = _read_json(
        ROOT
        / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
    )
    eval_rows = _records(eval_set, "positives") + _records(eval_set, "negatives")
    models_by_run: dict[str, set[str]] = {run: set() for run in RUNS}
    for row in eval_rows:
        run = row.get("run")
        model = row.get("solver_model")
        if run in models_by_run and isinstance(model, str):
            models_by_run[run].add(model)
    if any(len(models) != 1 for models in models_by_run.values()):
        raise EvidenceError("cannot derive one solver model for every measured run")

    per_run: dict[str, dict] = {}
    all_positives: set[tuple[str, str]] = set()
    for run in RUNS:
        blind = _read_json(
            ROOT / f"experiments/{run}/proof/blind_judge_verdicts.json"
        )
        original_positives = {
            (run, row["instance_id"])
            for row in _records(blind, "verdicts")
            if row.get("both_judges_flag_only_model") is True
        }
        run_recovered = {row for row in recovered if row[0] == run}
        run_new_positives = {row for row in new_positives if row[0] == run}
        run_input = target_runs.get(run)
        if not isinstance(run_input, dict):
            raise EvidenceError(f"iter235 target rebuild lacks {run}")
        current_positives = original_positives | run_new_positives
        all_positives.update(current_positives)
        per_run[DISPLAY_NAMES[run]] = {
            "solver_model": next(iter(models_by_run[run])),
            "N": run_input["certified"],
            "k": len(current_positives),
            "u": run_input["unadjudicated"] - len(run_recovered),
        }

    fixed = {DISPLAY_NAMES[run]: per_run[DISPLAY_NAMES[run]] for run in FIXED_COHORT_RUNS}
    return {
        "status": "supported",
        "scope": "cross-solver recurrence on one fixed convenience cohort",
        "fixed_cohort_runs": fixed,
        "all_six_runs": per_run,
        "patch_level_positives": len(all_positives),
        "unique_task_identities": len({instance_id for _, instance_id in all_positives}),
        "excluded_inferences": [
            "population generalization",
            "model independence",
            "population rate",
            "model ranking",
        ],
    }


def _derive_benchmark_labels() -> dict:
    eval_set = _read_json(
        ROOT
        / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
    )
    positives = _records(eval_set, "positives")
    negatives = _records(eval_set, "negatives")
    reasons = Counter(row.get("reason") for row in negatives)
    return {
        "status": "operational_reference_differential",
        "positive_count": len(positives),
        "control_count": len(negatives),
        "controls": {
            "normalized_identical_to_accepted": reasons[
                "certified_gold_equivalent_normalized"
            ],
            "no_divergence_on_one_retained_witness": reasons[
                "certified_no_observed_divergence"
            ],
        },
        "independent_semantic_ground_truth": False,
        "report_detector_control_flags_as": (
            "mixed-control flag rates, not validated false-positive rates"
        ),
    }


def build_expected() -> dict:
    """Build the correction solely from predecessor builders and evidence."""

    recurrence = _derive_recurrence()
    iter223 = recurrence["fixed_cohort_runs"]["iter223"]
    fresh = _derive_fresh_cohorts({"k": iter223["k"], "N": iter223["N"], "u": iter223["u"]})
    return {
        "schema_version": "telos.iter237.correction.v1",
        "iteration": "iter237_truth_maintenance_gate",
        "kind": "zero-spend integrity correction",
        "claim_boundary": (
            "This artifact corrects inference over committed operational labels. "
            "It supplies no new provider result, population rate, independent "
            "semantic ground truth, or validated transfer measurement."
        ),
        "sealed_predecessor": {
            "path": SEALED_PREFIX,
            "reference_commit": SEALED_REFERENCE_COMMIT,
            "byte_identical_required": True,
        },
        "claims": {
            "T1_transfer": _derive_transfer(),
            "T2_fresh_cohort_concentration": fresh,
            "T3_cross_solver_recurrence": recurrence,
            "T4_benchmark_labels": _derive_benchmark_labels(),
        },
        "next_scientific_gate": (
            "GROUND-TRUTH-1 independent blinded human semantic adjudication "
            "at unique-task level"
        ),
    }


def compare_artifact(actual: object, expected: object) -> list[str]:
    """Compare a correction artifact under the strict typed JSON contract."""

    return compare_json(actual, expected, path="root")


def validate_sealed_predecessor(root: Path = ROOT) -> list[str]:
    """Require every iter235 path to match the registered merged-master tree."""

    command = [
        "git",
        "diff",
        "--no-ext-diff",
        "--quiet",
        SEALED_REFERENCE_COMMIT,
        "--",
        SEALED_PREFIX,
    ]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    failures: list[str] = []
    if result.returncode == 1:
        failures.append(
            f"{SEALED_PREFIX} differs from sealed reference {SEALED_REFERENCE_COMMIT}"
        )
    elif result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        failures.append(f"cannot compare sealed predecessor: {detail}")
        return failures

    tree = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            SEALED_REFERENCE_COMMIT,
            "--",
            SEALED_PREFIX,
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if tree.returncode != 0:
        failures.append(f"cannot enumerate sealed predecessor: {tree.stderr.strip()}")
        return failures
    expected_paths = {line for line in tree.stdout.splitlines() if line}
    prefix = root / SEALED_PREFIX
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in prefix.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual_paths != expected_paths:
        failures.append(
            f"{SEALED_PREFIX} file set differs from sealed reference "
            f"(missing={sorted(expected_paths - actual_paths)}, "
            f"extra={sorted(actual_paths - expected_paths)})"
        )
    return failures


RESULT_REQUIRED = (
    "T1 — transfer: `untested`",
    "T2 — fresh-cohort concentration: `inconclusive`",
    "T3 — cross-solver recurrence: `supported`",
    "T4 — benchmark labels: `operational_reference_differential`",
    "`17` patch-level positives",
    "`12` unique task identities",
    "`29` normalized-identical controls",
    "`25` one-witness no-divergence controls",
    "executing the imported `adv.one_src` predicate",
    "GROUND-TRUTH-1",
)


def validate(
    artifact_path: Path = CORRECTION,
    *,
    check_sealed: bool = True,
) -> list[str]:
    """Return all iter237 correction failures."""

    failures: list[str] = []
    failures.extend(validate_structural_source_rule())
    try:
        expected = build_expected()
        actual = _read_json(artifact_path)
        failures.extend(compare_artifact(actual, expected))
    except EvidenceError as exc:
        failures.append(str(exc))

    if check_sealed:
        failures.extend(validate_sealed_predecessor())

    try:
        result_text = RESULT.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"cannot read iter237 result: {exc}")
    else:
        for phrase in RESULT_REQUIRED:
            if phrase not in result_text:
                failures.append(f"iter237 result missing required claim: {phrase}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact",
        type=Path,
        default=CORRECTION,
        help="correction artifact to validate (defaults to retained iter237 evidence)",
    )
    parser.add_argument(
        "--print-expected",
        action="store_true",
        help="print the mechanically rebuilt correction and exit",
    )
    args = parser.parse_args()

    if args.print_expected:
        try:
            print(json.dumps(build_expected(), indent=2, sort_keys=True))
        except EvidenceError as exc:
            print(f"iter237 truth maintenance: {exc}", file=sys.stderr)
            return 1
        return 0

    failures = validate(args.artifact)
    if failures:
        print("iter237 truth maintenance: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(
        "iter237 truth maintenance: T1 untested; T2 inconclusive; "
        "T3 bounded recurrence; T4 operational labels; iter235 sealed bytes match"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
