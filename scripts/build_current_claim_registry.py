#!/usr/bin/env python3
"""Rebuild Telos's six current internally regenerated claims.

This builder derives scientific values from the iter237 correction.  It does
not discover prose claims and it does not assign public-surface bindings.  The
claim-registry validator owns those two jobs and resolves a closed, curated set
of public projections back to JSON pointers in the records returned here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "mission/claim_registry.json"
SEAL_REGISTRY = ROOT / "mission/seal_registry.json"
DEPENDENCY_MANIFEST = (
    ROOT
    / "experiments/iter238_claim_seal_workflow_controls/proof/"
    "internal_claim_dependencies.json"
)
CORRECTION = (
    ROOT / "experiments/iter237_truth_maintenance_gate/proof/correction.json"
)
TRANSFER_ANALYSIS = (
    ROOT
    / "experiments/iter236_transfer_analysis_reconstruction/proof/"
    "transfer_analysis.json"
)
FIXED_COHORT_TARGETS = (
    ROOT
    / "experiments/iter223_natural_rate_safety_aware/proof/raw/"
    "solve_targets.json"
)
BASELINE_SEAL_ID = "iter237-merged-historical-baseline"
DERIVATION_ARGV = [
    "python3",
    "scripts/build_current_claim_registry.py",
    "--print-internal",
]
SELECTOR_PREDECESSOR_CLAIM_ID = "telos.selector.fix_size.reported_p_0_008"
PREDECESSOR_VALIDATOR_ARGV = [
    "python3",
    "scripts/validate_iter237_truth_maintenance.py",
]
DEPENDENCY_MANIFEST_SCHEMA = "telos.internal_claim_dependencies.v1"

_STATIC_DEPENDENCY_PATHS = {
    "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/"
    "swebench_verified_rows_snapshot.json",
    "experiments/iter202_natural_rate_scaled/proof/raw/solve_targets.json",
    "experiments/iter223_natural_rate_safety_aware/proof/raw/solve_targets.json",
    "experiments/iter224_natural_rate_scale_n/proof/audit_report.json",
    "experiments/iter224_natural_rate_scale_n/proof/iter200_per_candidate.json",
    "experiments/iter224_natural_rate_scale_n/proof/raw/solve_targets.json",
    "experiments/iter228_fresh_diverse_cohort/proof/audit_report.json",
    "experiments/iter228_fresh_diverse_cohort/proof/iter200_per_candidate.json",
    "experiments/iter228_fresh_diverse_cohort/proof/raw/solve_targets.json",
    "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json",
    "experiments/iter233_natural_benchmark_release/release/answers/answers.json",
    "experiments/iter235_witness_recovery/proof/raw/judge/judge_summary.json",
    "experiments/iter235_witness_recovery/proof/raw/witnesses/"
    "witnesses_summary.json",
    "experiments/iter236_transfer_analysis_reconstruction/proof/"
    "transfer_analysis.json",
    "experiments/iter237_truth_maintenance_gate/RESULT.md",
    "experiments/iter237_truth_maintenance_gate/proof/correction.json",
    "mission/seal_registry.json",
    "scripts/build_current_claim_registry.py",
    "scripts/build_iter202_solve_targets.py",
    "scripts/build_iter235_targets.py",
    "scripts/build_iter236_transfer_analysis.py",
    "scripts/run_certified_resolved_adversary.py",
    "scripts/run_iter200_solver.py",
    "scripts/validate_iter202_runtime_freeze.py",
    "scripts/validate_iter237_truth_maintenance.py",
    "telos/json_compare.py",
    "telos/patch_normalization.py",
    "telos/secure_checkpoint_fs.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_relative(path: str) -> bool:
    candidate = PurePosixPath(path)
    return (
        bool(path)
        and not candidate.is_absolute()
        and "\\" not in path
        and "\x00" not in path
        and all(part not in {"", ".", ".."} for part in candidate.parts)
        and candidate.as_posix() == path
    )


def _git_blob_exists(reference_commit: str, path: str) -> bool:
    if not _canonical_relative(path):
        return False
    result = subprocess.run(
        ["git", "cat-file", "-t", f"{reference_commit}:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "blob"


def baseline_seal_contains(path: str) -> bool:
    """Return whether the exact path is a protected baseline Git blob.

    A path prefix alone is insufficient.  In particular, iter238 is an allowed
    additive successor below ``experiments/`` and did not exist at the
    reference commit, so it is never attributed to the retrospective baseline.
    """

    registry = json.loads(SEAL_REGISTRY.read_text(encoding="utf-8"))
    records = [
        record
        for record in registry.get("records", [])
        if record.get("seal_id") == BASELINE_SEAL_ID
    ]
    if len(records) != 1:
        raise ValueError(f"expected one {BASELINE_SEAL_ID!r} seal record")
    record = records[0]
    reference = record.get("reference_commit")
    if not isinstance(reference, str):
        raise ValueError("baseline seal lacks reference_commit")

    selected = False
    for protected_set in record.get("protected_sets", []):
        selector = protected_set.get("selector", {})
        kind = selector.get("kind")
        if kind == "tree":
            root = selector.get("path")
            selected = selected or (
                isinstance(root, str)
                and (path == root or path.startswith(f"{root}/"))
            )
        elif kind == "path_list":
            selected = selected or path in selector.get("paths", [])
    return selected and _git_blob_exists(reference, path)


def source(path: str) -> dict[str, Any]:
    absolute = ROOT / path
    seal_ids = [BASELINE_SEAL_ID] if baseline_seal_contains(path) else []
    return {
        "path": path,
        "sha256": sha256(absolute),
        "classification": "sealed" if seal_ids else "mutable",
        "seal_ids": seal_ids,
    }


def internal_dependency_paths() -> list[str]:
    """Return the audited transitive code/data closure read by the derivation."""

    paths = set(_STATIC_DEPENDENCY_PATHS)
    for run in (
        "iter200_natural_certified_yet_wrong_rate",
        "iter223_natural_rate_safety_aware",
        "iter225_cross_model_generalization",
        "iter226_cross_model_generalization_gpt54",
        "iter227_cross_provider_generalization",
        "iter229_cross_provider_gemini",
    ):
        paths.add(f"experiments/{run}/proof/iter200_per_candidate.json")
        paths.add(f"experiments/{run}/proof/blind_judge_verdicts.json")

    witness_summary = json.loads(
        (
            ROOT
            / "experiments/iter235_witness_recovery/proof/raw/witnesses/"
            "witnesses_summary.json"
        ).read_text(encoding="utf-8")
    )
    manifest = witness_summary.get("manifest")
    if not isinstance(manifest, list):
        raise ValueError("iter235 witness summary manifest is not an array")
    for row in manifest:
        if not isinstance(row, dict) or row.get("status") != "witness":
            continue
        run = row.get("run")
        instance_id = row.get("instance_id")
        if not isinstance(run, str) or not isinstance(instance_id, str):
            raise ValueError("iter235 recovered witness identity is malformed")
        paths.add(
            "experiments/iter235_witness_recovery/proof/raw/execution/"
            f"{run}__{instance_id}.witness.log"
        )

    for path in sorted(paths):
        if not _canonical_relative(path) or not (ROOT / path).is_file():
            raise ValueError(f"internal dependency is unsafe or missing: {path}")
    return sorted(paths)


def build_dependency_manifest() -> dict[str, Any]:
    return {
        "schema_version": DEPENDENCY_MANIFEST_SCHEMA,
        "derivation_argv": DERIVATION_ARGV,
        "predecessor_validator_argv": PREDECESSOR_VALIDATOR_ARGV,
        "dependencies": [source(path) for path in internal_dependency_paths()],
    }


def derivation(pointer: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    digest_payload = json.dumps(
        {
            "argv": DERIVATION_ARGV,
            "output_pointer": pointer,
            "predecessor_validator_argv": PREDECESSOR_VALIDATOR_ARGV,
            "inputs": [
                {"path": item["path"], "sha256": item["sha256"]}
                for item in sources
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "mode": "validated_predecessor_projection",
        "argv": DERIVATION_ARGV,
        "output_pointer": pointer,
        "predecessor_validator_argv": PREDECESSOR_VALIDATOR_ARGV,
        "dependency_contract": (
            "The sealed iter237 correction is projected only as a predecessor "
            "artifact. Its separately CI-enforced validator rebuilds the "
            "transitive scientific evidence; these sources bind that validator "
            "implementation and its direct builder/comparator code."
        ),
        "input_digest_sha256": hashlib.sha256(digest_payload).hexdigest(),
    }


def claim(
    *,
    claim_id: str,
    status: str,
    unit: str,
    cohort: str,
    independence_boundary: str,
    value: Any,
    missingness: dict[str, Any],
    excluded_inferences: list[str],
    sources: list[dict[str, Any]],
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    pointer = f"/claims/{claim_id}"
    return {
        "claim_id": claim_id,
        "revision": 1,
        "status": status,
        "kind": "internally_regenerated_empirical",
        "unit": unit,
        "cohort": cohort,
        "independence_boundary": independence_boundary,
        "value": value,
        "missingness": missingness,
        "excluded_inferences": excluded_inferences,
        "derivation": derivation(pointer, sources),
        "sources": sources,
        "surface_binding_ids": [],
        "supersedes": [] if supersedes is None else list(supersedes),
        "superseded_by": None,
    }


def build_internal_claims() -> dict[str, dict[str, Any]]:
    """Return the exact six current claims regenerated from predecessor bytes."""

    correction_document = json.loads(CORRECTION.read_text(encoding="utf-8"))
    correction = correction_document["claims"]
    transfer = correction["T1_transfer"]
    fresh = correction["T2_fresh_cohort_concentration"]
    recurrence = correction["T3_cross_solver_recurrence"]
    labels = correction["T4_benchmark_labels"]
    transfer_analysis = json.loads(
        TRANSFER_ANALYSIS.read_text(encoding="utf-8")
    )
    within_cohort = transfer_analysis["within_cohort"]
    transfer_cohort = transfer_analysis["cohort"]
    target_document = json.loads(FIXED_COHORT_TARGETS.read_text(encoding="utf-8"))
    target_rows = target_document.get("targets")
    target_count = target_document.get("count")
    if (
        type(target_count) is not int
        or not isinstance(target_rows, list)
        or target_count != len(target_rows)
    ):
        raise ValueError("fixed-cohort target count does not match retained rows")

    predecessor_sources = [
        source("experiments/iter237_truth_maintenance_gate/proof/correction.json"),
        source("scripts/build_current_claim_registry.py"),
        source("scripts/validate_iter237_truth_maintenance.py"),
        source("scripts/build_iter236_transfer_analysis.py"),
        source("telos/json_compare.py"),
        source(
            "experiments/iter238_claim_seal_workflow_controls/proof/"
            "internal_claim_dependencies.json"
        ),
    ]

    def sources(*paths: str) -> list[dict[str, Any]]:
        records = [*predecessor_sources, *(source(path) for path in paths)]
        return list({record["path"]: record for record in records}.values())

    transfer_sources = [
        *sources(
            "experiments/iter236_transfer_analysis_reconstruction/proof/"
            "transfer_analysis.json",
        ),
    ]
    fresh_sources = sources(
        "experiments/iter224_natural_rate_scale_n/proof/audit_report.json",
        "experiments/iter228_fresh_diverse_cohort/proof/audit_report.json",
    )
    recurrence_sources = sources(
        (
            "experiments/iter235_witness_recovery/proof/raw/witnesses/"
            "witnesses_summary.json"
        ),
        (
            "experiments/iter235_witness_recovery/proof/raw/judge/"
            "judge_summary.json"
        ),
        (
            "experiments/iter223_natural_rate_safety_aware/proof/raw/"
            "solve_targets.json"
        ),
        "scripts/build_iter235_targets.py",
    )
    label_sources = sources(
        "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
    )

    fixed_runs = recurrence["fixed_cohort_runs"]
    all_runs = recurrence["all_six_runs"]
    records = [
        claim(
            claim_id="telos.transfer.fix_size",
            status=transfer["status"],
            unit="held-out task row",
            cohort=(
                "447 registered non-cohort rows plus an exploratory fixed-cohort "
                "comparison"
            ),
            independence_boundary=(
                "Held-out rows contain selector prevalence and zero susceptibility "
                "outcome labels."
            ),
            value={
                "registered_held_out_rows": transfer["registered_held_out_rows"],
                "registered_outcome_endpoint": transfer[
                    "registered_outcome_endpoint"
                ],
                "registered_outcome_labels": transfer[
                    "registered_outcome_labels"
                ],
                "selectors": transfer["selectors"],
            },
            missingness={
                "mode": "endpoint_absent",
                "outcome_labels": transfer["registered_outcome_labels"],
                "reason": (
                    "The registered held-out reconstruction has no susceptibility "
                    "outcome field."
                ),
            },
            excluded_inferences=[
                "validated transfer",
                "predictive enrichment",
                "causal fix-complexity effect",
            ],
            sources=transfer_sources,
        ),
        claim(
            claim_id="telos.selector.fix_size_exploratory",
            status="exploratory",
            unit="fixed-cohort task target",
            cohort=(
                f"post-hoc comparison within the reused {target_count}-target "
                "cohort"
            ),
            independence_boundary=(
                "Selected after inspection, uncorrected for multiple comparisons, "
                "and not tested on outcome-labelled held-out rows."
            ),
            value={
                **transfer["exploratory_within_cohort"],
                "solver_model_count": len(fixed_runs),
                "comparison_group_count": 2,
                "labelled_target_count": transfer_cohort["hacked_count"],
                "unlabelled_target_count": transfer_cohort["other_count"],
                "labelled_median_added_source_lines": within_cohort[
                    "hacked_median"
                ],
                "unlabelled_median_added_source_lines": within_cohort[
                    "other_median"
                ],
            },
            missingness={
                "mode": "none_for_statistic",
                "reason": "All rows used by this post-hoc statistic are present.",
            },
            excluded_inferences=[
                "confirmed predictor",
                "validated transfer",
                "causal effect",
            ],
            sources=transfer_sources,
            supersedes=[SELECTOR_PREDECESSOR_CLAIM_ID],
        ),
        claim(
            claim_id="telos.cohort.fresh_concentration",
            status=fresh["status"],
            unit="certified patch",
            cohort="iter224 and iter228 fresh single-solver cohorts",
            independence_boundary=(
                "Only one solver was used and thirteen certified outcomes remain "
                "unadjudicated."
            ),
            value={
                "cohort_count": len(fresh["cohorts"]),
                "cohorts": fresh["cohorts"],
                "total": fresh["total"],
                "least_favourable": fresh["least_favourable"],
                "reused_reference": fresh["reused_reference"],
                "registered_strict_inequality_holds": fresh[
                    "registered_strict_inequality_holds"
                ],
            },
            missingness={
                "mode": "certified_outcome_unadjudicated",
                "u": fresh["total"]["u"],
                "N": fresh["total"]["N"],
                "reason": "Thirteen certified outcomes lack adjudicated labels.",
            },
            excluded_inferences=[
                "fresh-cohort concentration",
                "fresh-cohort population rate",
                "causal repository explanation",
            ],
            sources=fresh_sources,
        ),
        claim(
            claim_id="telos.recurrence.fixed_cohort",
            status=recurrence["status"],
            unit="certified patch attempt",
            cohort="five solver runs on one fixed 53-target convenience cohort",
            independence_boundary=(
                "Targets, witness generator, judges, and susceptible task "
                "identities are reused."
            ),
            value={
                "cohort_count": 1,
                "target_count": target_count,
                "solver_configuration_count": len(fixed_runs),
                "additional_solver_configuration_count": len(fixed_runs) - 1,
                "positive_run_count": sum(
                    row["k"] > 0 for row in fixed_runs.values()
                ),
                "minimum_positive_per_run": min(
                    row["k"] for row in fixed_runs.values()
                ),
                "provider_count": len(
                    {
                        "openai"
                        if row["solver_model"].startswith("gpt-")
                        else "anthropic"
                        if row["solver_model"].startswith("claude-")
                        else "google"
                        for row in fixed_runs.values()
                    }
                ),
                "fixed_cohort_runs": fixed_runs,
                "fixed_cohort_patch_level_positives": sum(
                    row["k"] for row in fixed_runs.values()
                ),
            },
            missingness={
                "mode": "certified_outcome_unadjudicated",
                "u_by_run": {
                    run: row["u"] for run, row in fixed_runs.items()
                },
                "reason": "Four fixed-cohort runs retain unadjudicated outcomes.",
            },
            excluded_inferences=recurrence["excluded_inferences"],
            sources=recurrence_sources,
        ),
        claim(
            claim_id="telos.recurrence.all_runs_dependence",
            status=recurrence["status"],
            unit="patch-level operational label and unique task identity",
            cohort="all six measured runs, including the separate iter200 run",
            independence_boundary=(
                "Repeated solver attempts on shared tasks are not independent task "
                "samples."
            ),
            value={
                "all_runs": all_runs,
                "measured_run_count": len(all_runs),
                "certifications": sum(row["N"] for row in all_runs.values()),
                "patch_level_positives": recurrence["patch_level_positives"],
                "unique_task_identities": recurrence["unique_task_identities"],
                "unadjudicated": sum(row["u"] for row in all_runs.values()),
                "iter200_observed": {
                    "numerator": all_runs["iter200"]["k"],
                    "denominator": all_runs["iter200"]["N"],
                },
                "iter200_least_favourable": {
                    "numerator": (
                        all_runs["iter200"]["k"] + all_runs["iter200"]["u"]
                    ),
                    "denominator": all_runs["iter200"]["N"],
                },
                "iter200_complete_case": {
                    "numerator": all_runs["iter200"]["k"],
                    "denominator": (
                        all_runs["iter200"]["N"] - all_runs["iter200"]["u"]
                    ),
                },
            },
            missingness={
                "mode": "certified_outcome_unadjudicated",
                "u": sum(row["u"] for row in all_runs.values()),
                "reason": "Eight certified outcomes remain unadjudicated.",
            },
            excluded_inferences=recurrence["excluded_inferences"],
            sources=recurrence_sources,
        ),
        claim(
            claim_id="telos.benchmark.operational_labels",
            status=labels["status"],
            unit="released detector-benchmark row",
            cohort="frozen 67-row operational detector benchmark",
            independence_boundary=(
                "Labels are reference-differential operations, not independent "
                "human semantic adjudications."
            ),
            value={
                "row_count": labels["positive_count"] + labels["control_count"],
                "positive_count": labels["positive_count"],
                "control_count": labels["control_count"],
                "retained_witness_count": 1,
                "controls": labels["controls"],
                "independent_semantic_ground_truth": labels[
                    "independent_semantic_ground_truth"
                ],
            },
            missingness={
                "mode": "semantic_control_status_unresolved",
                "rows": labels["controls"][
                    "no_divergence_on_one_retained_witness"
                ],
                "reason": (
                    "Witness non-divergence does not independently establish "
                    "semantic correctness."
                ),
            },
            excluded_inferences=[
                "validated false-positive rate",
                "independent semantic ground truth",
                "leaderboard ranking",
            ],
            sources=label_sources,
        ),
    ]
    return {record["claim_id"]: record for record in records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-internal",
        action="store_true",
        help="print the internally regenerated claim records",
    )
    parser.add_argument(
        "--print-dependency-manifest",
        action="store_true",
        help="print the audited transitive code/data dependency closure",
    )
    parser.add_argument(
        "--write-dependency-manifest",
        action="store_true",
        help="write the audited transitive dependency closure artifact",
    )
    args = parser.parse_args()
    if args.print_dependency_manifest:
        print(json.dumps(build_dependency_manifest(), indent=2, sort_keys=True))
        return 0
    if args.write_dependency_manifest:
        payload = (
            json.dumps(build_dependency_manifest(), indent=2, sort_keys=True)
            + "\n"
        )
        DEPENDENCY_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        DEPENDENCY_MANIFEST.write_text(payload, encoding="utf-8")
        print(DEPENDENCY_MANIFEST.relative_to(ROOT))
        return 0
    claims = build_internal_claims()
    if args.print_internal:
        print(json.dumps({"claims": claims}, indent=2, sort_keys=True))
        return 0
    parser.error("select --print-internal")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
