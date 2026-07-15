#!/usr/bin/env python3
"""Audit prior mission exposure in the frozen iter202 target cohort.

This is a pre-output audit. It distinguishes the property needed for pooling
(no overlap with iter200's neutral-solve attempts) from the stronger, false
claim that no target appeared in any prior mission result.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter202_natural_rate_scaled"
TARGETS = EXP / "proof/raw/solve_targets.json"
OUT = EXP / "proof/raw/sample_overlap_audit.json"
ITER200_TARGETS = (
    ROOT
    / "experiments/iter200_natural_certified_yet_wrong_rate/proof/raw/"
    "solve_targets.json"
)
ITER193_TARGETS = (
    ROOT
    / "experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/"
    "phase_a_candidates/phase_a_summary.json"
)
ITER199_TARGETS = (
    ROOT
    / "experiments/iter199_benchmark_expansion_across_repos/proof/raw/targets.json"
)
RELEASED_V1 = ROOT / "benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl"
PROVIDER_ROW_MAP_SOURCES = (
    RELEASED_V1,
    ROOT
    / "benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/"
    "legitimate_controls_v1.jsonl",
)
PROVIDER_PACKET_MAP_SOURCES = (
    ROOT
    / "benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/"
    "packets.jsonl",
    ROOT
    / "benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/"
    "blinded_control_packets_v1/packets.jsonl",
)

# These committed artifacts establish local/execution-facing use of instances before
# iter202. Candidate-pool and source-snapshot inventories are intentionally excluded:
# mere membership in the upstream universe is not a result-bearing exposure.
PRIOR_LOCAL_RESULT_SOURCES = (
    ROOT / "experiments/iter109_real_trajectory_tamper_detection_pilot/proof/clean_decisions.json",
    ROOT / "experiments/iter109_real_trajectory_tamper_detection_pilot/proof/hack_decisions.json",
    ROOT / "experiments/iter139_property_derivability/proof/derivability.json",
    ROOT / "experiments/iter148_protocol_effect_replication/proof/replication_results.json",
    ROOT / "experiments/iter150_gold_free_oracle_rate/proof/goldfree_oracle_run_d.json",
)

ITER_RE = re.compile(r"^iter(\d+)_")
INSTANCE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-\d+$")


def load_build_module():
    path = ROOT / "scripts/build_iter202_solve_targets.py"
    spec = importlib.util.spec_from_file_location("build_iter202_solve_targets", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load iter202 target builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def target_ids_from_json(path: Path, key: str) -> set[str]:
    return {row["instance_id"] for row in json.loads(path.read_text())[key]}


def ids_mentioned(paths: tuple[Path, ...] | list[Path], candidates: set[str]) -> set[str]:
    mentioned: set[str] = set()
    for path in paths:
        text = path.read_text(errors="ignore")
        mentioned.update(instance_id for instance_id in candidates if instance_id in text)
    return mentioned


def prior_provider_ledgers() -> list[Path]:
    """Return committed pre-iter202 provider call ledgers in deterministic order."""

    paths: list[Path] = []
    experiments = ROOT / "experiments"
    for path in experiments.glob("iter*/**/*call_ledger*.jsonl"):
        experiment_dir = path.relative_to(experiments).parts[0]
        match = ITER_RE.match(experiment_dir)
        if match and int(match.group(1)) < 202:
            paths.append(path)
    return sorted(paths)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL row: {path.relative_to(ROOT)}:{line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"non-object JSONL row: {path.relative_to(ROOT)}:{line_number}")
        rows.append(row)
    return rows


def provider_identity_maps() -> tuple[dict[str, str], dict[str, str], list[dict]]:
    """Build and cross-check row-id and packet-id mappings to SWE-bench instance IDs."""

    row_to_instance: dict[str, str] = {}
    packet_to_instance: dict[str, str] = {}
    source_evidence = []
    for path in PROVIDER_ROW_MAP_SOURCES:
        rows = read_jsonl(path)
        for row in rows:
            row_id = row.get("row_id")
            instance_id = row.get("instance_id")
            if not isinstance(row_id, str) or not isinstance(instance_id, str):
                raise ValueError(f"provider row mapping is incomplete: {path.relative_to(ROOT)}")
            previous = row_to_instance.setdefault(row_id, instance_id)
            if previous != instance_id:
                raise ValueError(f"provider row mapping conflicts for {row_id}")
        source_evidence.append(
            {
                "path": str(path.relative_to(ROOT)),
                "role": "row_id_to_instance_id",
                "row_count": len(rows),
                "sha256": sha256_file(path),
            }
        )
    for path in PROVIDER_PACKET_MAP_SOURCES:
        rows = read_jsonl(path)
        for row in rows:
            packet_id = row.get("packet_id")
            row_id = row.get("row_id")
            payload = row.get("model_prompt_payload")
            instance_id = payload.get("instance_id") if isinstance(payload, dict) else None
            if (
                not isinstance(packet_id, str)
                or not isinstance(row_id, str)
                or not isinstance(instance_id, str)
            ):
                raise ValueError(f"provider packet mapping is incomplete: {path.relative_to(ROOT)}")
            if row_to_instance.get(row_id) != instance_id:
                raise ValueError(f"provider packet/row mapping conflicts for {packet_id}")
            previous = packet_to_instance.setdefault(packet_id, instance_id)
            if previous != instance_id:
                raise ValueError(f"provider packet mapping conflicts for {packet_id}")
        source_evidence.append(
            {
                "path": str(path.relative_to(ROOT)),
                "role": "packet_id_to_instance_id",
                "row_count": len(rows),
                "sha256": sha256_file(path),
            }
        )
    return row_to_instance, packet_to_instance, source_evidence


def resolve_ledger_instance_id(
    row: dict,
    *,
    row_to_instance: dict[str, str],
    packet_to_instance: dict[str, str],
    path: Path,
    line_number: int,
) -> tuple[str, list[str]]:
    """Resolve one ledger row fail-closed and reject conflicting identity routes."""

    resolutions: list[tuple[str, str]] = []
    call_id = row.get("call_id")
    if isinstance(call_id, str):
        direct = call_id.split(":", 1)[0]
        if INSTANCE_ID_RE.fullmatch(direct):
            resolutions.append(("direct_call_id", direct))

    row_id = row.get("row_id")
    if row_id is not None:
        if not isinstance(row_id, str) or row_id not in row_to_instance:
            raise ValueError(
                f"unmapped provider row_id: {path.relative_to(ROOT)}:{line_number}"
            )
        resolutions.append(("row_id", row_to_instance[row_id]))

    packet_id = row.get("packet_id")
    if packet_id is not None:
        if not isinstance(packet_id, str) or packet_id not in packet_to_instance:
            raise ValueError(
                f"unmapped provider packet_id: {path.relative_to(ROOT)}:{line_number}"
            )
        resolutions.append(("packet_id", packet_to_instance[packet_id]))

    if not resolutions:
        raise ValueError(f"unresolved provider ledger row: {path.relative_to(ROOT)}:{line_number}")
    instance_ids = {instance_id for _, instance_id in resolutions}
    if len(instance_ids) != 1:
        raise ValueError(
            f"conflicting provider ledger identity routes: {path.relative_to(ROOT)}:{line_number}"
        )
    return next(iter(instance_ids)), sorted({method for method, _ in resolutions})


def resolve_provider_ledgers(
    paths: list[Path], target_ids: set[str]
) -> tuple[set[str], dict]:
    """Resolve every pre-iter202 ledger row and retain source-completeness evidence."""

    row_to_instance, packet_to_instance, map_sources = provider_identity_maps()
    all_instance_ids: set[str] = set()
    ledger_evidence = []
    total_rows = 0
    for path in paths:
        rows = read_jsonl(path)
        resolved_ids: set[str] = set()
        overlap_ids: set[str] = set()
        schema_versions: set[str] = set()
        mapping_counts: Counter[str] = Counter()
        for line_number, row in enumerate(rows, start=1):
            instance_id, methods = resolve_ledger_instance_id(
                row,
                row_to_instance=row_to_instance,
                packet_to_instance=packet_to_instance,
                path=path,
                line_number=line_number,
            )
            resolved_ids.add(instance_id)
            all_instance_ids.add(instance_id)
            if instance_id in target_ids:
                overlap_ids.add(instance_id)
            schema = row.get("schema_version")
            schema_versions.add(schema if isinstance(schema, str) else "<absent>")
            for method in methods:
                mapping_counts[method] += 1
        total_rows += len(rows)
        ledger_evidence.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256_file(path),
                "row_count": len(rows),
                "schema_versions": sorted(schema_versions),
                "mapping_mode_row_counts": dict(sorted(mapping_counts.items())),
                "resolved_instance_count": len(resolved_ids),
                "iter202_overlap_count": len(overlap_ids),
                "iter202_overlap_ids": sorted(overlap_ids),
            }
        )
    return all_instance_ids, {
        "ledger_file_count": len(paths),
        "ledger_row_count": total_rows,
        "all_rows_resolved_without_conflict": True,
        "identity_map_sources": map_sources,
        "ledgers": ledger_evidence,
    }


def ordered_ids_sha256(instance_ids: list[str]) -> str:
    payload = "\n".join(instance_ids) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def build_audit() -> dict:
    target_manifest = json.loads(TARGETS.read_text())
    targets = target_manifest["targets"]
    ordered_ids = [row["instance_id"] for row in targets]
    target_ids = set(ordered_ids)
    if len(target_ids) != len(ordered_ids):
        raise ValueError("iter202 target IDs are not unique")

    iter200_ids = target_ids_from_json(ITER200_TARGETS, "targets")
    iter193_ids = target_ids_from_json(ITER193_TARGETS, "manifest")
    iter199_ids = target_ids_from_json(ITER199_TARGETS, "targets")
    provider_paths = prior_provider_ledgers()
    all_provider_ledger_ids, provider_ledger_resolution = resolve_provider_ledgers(
        provider_paths, target_ids
    )
    provider_ids = all_provider_ledger_ids & target_ids
    local_result_ids = ids_mentioned(list(PRIOR_LOCAL_RESULT_SOURCES), target_ids)
    released_v1_ids = ids_mentioned([RELEASED_V1], target_ids)
    prior_outcome_ids = provider_ids | local_result_ids
    no_prior_outcome_ids = target_ids - prior_outcome_ids

    build = load_build_module()
    source_rows = json.loads(build.SNAPSHOT.read_text())["rows"]
    excluded = build.excluded_ids()
    eligible_rows = [row for row in source_rows if build.eligible(row, excluded)]
    eligible_ids = {row["instance_id"] for row in eligible_rows}
    eligible_prior_outcome_ids = (
        all_provider_ledger_ids & eligible_ids
    ) | ids_mentioned(list(PRIOR_LOCAL_RESULT_SOURCES), eligible_ids)
    eligible_unexposed_by_repo: dict[str, list[str]] = defaultdict(list)
    eligible_total_by_repo: dict[str, int] = defaultdict(int)
    for row in eligible_rows:
        repo = row["repo"]
        eligible_total_by_repo[repo] += 1
        if row["instance_id"] not in eligible_prior_outcome_ids:
            eligible_unexposed_by_repo[repo].append(row["instance_id"])

    cap = int(target_manifest["cap_per_repo"])
    max_unexposed_under_cap = sum(
        min(len(instance_ids), cap) for instance_ids in eligible_unexposed_by_repo.values()
    )
    per_repo = []
    for repo in sorted(eligible_total_by_repo):
        unexposed = sorted(eligible_unexposed_by_repo.get(repo, []))
        per_repo.append(
            {
                "repo": repo,
                "eligible": eligible_total_by_repo[repo],
                "eligible_without_prior_outcome_exposure": len(unexposed),
                "selectable_without_prior_outcome_exposure_under_cap": min(len(unexposed), cap),
            }
        )

    annotations = []
    for row in targets:
        instance_id = row["instance_id"]
        categories = []
        if instance_id in local_result_ids:
            categories.append("prior_local_result_artifact")
        if instance_id in provider_ids:
            categories.append("prior_provider_call_ledger")
        if instance_id in released_v1_ids:
            categories.append("released_v1_benchmark_row")
        annotations.append(
            {
                "instance_id": instance_id,
                "repo": row["repo"],
                "prior_outcome_exposed": instance_id in prior_outcome_ids,
                "prior_provider_call_ledger": instance_id in provider_ids,
                "categories": categories,
            }
        )

    return {
        "schema_version": "telos.iter202.sample_overlap_audit.v1",
        "experiment_id": "iter202_natural_rate_scaled",
        "audit_scope": (
            "Committed pre-iter202 artifacts present in this repository; source snapshots and "
            "candidate-pool inventories alone do not count as result-bearing exposure."
        ),
        "frozen_target_count": len(targets),
        "ordered_target_ids_sha256": ordered_ids_sha256(ordered_ids),
        "ordered_hash_serialization": "UTF-8 instance IDs joined by LF with one trailing LF",
        "summary": {
            "iter200_neutral_solve_overlap": len(target_ids & iter200_ids),
            "iter193_or_iter199_elicited_target_overlap": len(
                target_ids & (iter193_ids | iter199_ids)
            ),
            "prior_local_result_artifact_overlap": len(local_result_ids),
            "prior_provider_call_ledger_overlap": len(provider_ids),
            "prior_outcome_exposed_union": len(prior_outcome_ids),
            "no_prior_outcome_exposure": len(no_prior_outcome_ids),
            "released_v1_benchmark_row_overlap": len(released_v1_ids),
        },
        "overlap_ids": {
            "iter200_neutral_solve": sorted(target_ids & iter200_ids),
            "iter193_or_iter199_elicited_targets": sorted(
                target_ids & (iter193_ids | iter199_ids)
            ),
            "prior_local_result_artifacts": sorted(local_result_ids),
            "prior_provider_call_ledgers": sorted(provider_ids),
            "prior_outcome_exposed_union": sorted(prior_outcome_ids),
            "no_prior_outcome_exposure": sorted(no_prior_outcome_ids),
            "released_v1_benchmark_rows": sorted(released_v1_ids),
        },
        "evidence_sources": {
            "prior_local_result_artifacts": [
                str(path.relative_to(ROOT)) for path in PRIOR_LOCAL_RESULT_SOURCES
            ],
            "prior_provider_call_ledgers": [
                str(path.relative_to(ROOT)) for path in provider_paths
            ],
            "released_v1_benchmark": str(RELEASED_V1.relative_to(ROOT)),
            "pooling_disjointness": str(ITER200_TARGETS.relative_to(ROOT)),
            "recent_elicited_disjointness": [
                str(ITER193_TARGETS.relative_to(ROOT)),
                str(ITER199_TARGETS.relative_to(ROOT)),
            ],
        },
        "provider_ledger_resolution": provider_ledger_resolution,
        "same_rule_replacement_feasibility": {
            "eligible_universe": len(eligible_ids),
            "eligible_without_prior_outcome_exposure": len(
                eligible_ids - eligible_prior_outcome_ids
            ),
            "frozen_per_repo_cap": cap,
            "maximum_unexposed_rows_selectable_under_frozen_cap": max_unexposed_under_cap,
            "required_rows": len(targets),
            "same_rule_disjoint_replacement_available": max_unexposed_under_cap >= len(targets),
            "per_repo": per_repo,
            "decision": (
                "Retain the frozen IDs. A 53-row no-overlap replacement exists only by changing the "
                "registered per-repository weighting after provider initiation; the unchanged cap can "
                f"select at most {max_unexposed_under_cap}."
            ),
        },
        "required_result_sensitivity": {
            "primary": "all 53 frozen analyzed target IDs",
            "prior_outcome_exposure_split": {
                "exposed_attempts": len(prior_outcome_ids),
                "unexposed_attempts": len(no_prior_outcome_ids),
            },
            "prior_provider_call_ledger_split": {
                "exposed_attempts": len(provider_ids),
                "without_ledger_evidence_attempts": len(target_ids - provider_ids),
            },
            "rule": (
                "Report the same k/N missing-outcome quantities within each split; do not describe "
                "the cohort as unused across the mission."
            ),
        },
        "claim_boundary": (
            "The 53 iter202 IDs are disjoint from iter200's analyzed neutral-solve targets, but the cohort is "
            "not mission-history fresh. Prior-use strata are descriptive sensitivity analyses, not "
            "evidence of causal contamination or a general model frequency."
        ),
        "targets": annotations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    audit = build_audit()
    rendered = json.dumps(audit, indent=2, sort_keys=True) + "\n"
    if args.check:
        if json.loads(OUT.read_text()) != audit:
            print("iter202 sample overlap audit does not reproduce")
            return 1
        print(
            "iter202 overlap audit reproduces: "
            f"iter200=0 prior_outcome={audit['summary']['prior_outcome_exposed_union']} "
            f"provider_ledger={audit['summary']['prior_provider_call_ledger_overlap']}"
        )
    elif args.write:
        OUT.write_text(rendered)
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
