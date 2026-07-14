#!/usr/bin/env python3
"""Publish iter185 panel-miss property-probe design without provider calls."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter185_reward_hack_panel_miss_property_probe_design"
NEXT_EXPERIMENT_ID = "iter186_reward_hack_panel_property_probe_packet_materialization"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"
NEXT_HYPOTHESIS = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"

ITER179_METRICS = (
    ROOT
    / "experiments"
    / "iter179_reward_hack_panel_full_cohort_adjudication"
    / "proof"
    / "full_cohort_panel_metrics.json"
)
ITER179_ROW_AUDIT = (
    ROOT
    / "experiments"
    / "iter179_reward_hack_panel_full_cohort_adjudication"
    / "proof"
    / "row_level_disagreement_and_nondecision_audit.json"
)
ITER182_RESULT = (
    ROOT / "experiments" / "iter182_reward_hack_panel_repair_execution_adjudication" / "RESULT.md"
)
ITER184_SOURCE_MATRIX = (
    ROOT
    / "experiments"
    / "iter184_reward_hack_panel_frontier_research_alignment_design"
    / "proof"
    / "source_linked_frontier_alignment_matrix.json"
)
ITER184_TECHNIQUE_MAP = (
    ROOT
    / "experiments"
    / "iter184_reward_hack_panel_frontier_research_alignment_design"
    / "proof"
    / "telos_gap_to_technique_map.json"
)
BENCHMARK_ROWS = ROOT / "benchmarks" / "reward_hack_benchmark_v1" / "reward_hack_benchmark_v1.jsonl"
BENCHMARK_MANIFEST = ROOT / "benchmarks" / "reward_hack_benchmark_v1" / "manifest.json"
CONTROL_ROWS = (
    ROOT / "benchmarks" / "reward_hack_benchmark_v1" / "legitimate_controls_v1" / "legitimate_controls_v1.jsonl"
)

PUBLIC_SURFACES = [
    ROOT / "README.md",
    ROOT / "docs" / "REPORT.md",
    ROOT / "docs" / "MISSION_LOOP.md",
    ROOT / "docs" / "LITERATURE_ALIGNMENT_2026.md",
    ROOT / "CONTINUITY.md",
    ROOT / "HANDOFF.md",
    ROOT / "mission" / "loop.json",
]

PRIMARY_MISS_COHORT = PROOF / "primary_miss_cohort_manifest.json"
DISAGREEMENT_AUDIT = PROOF / "disagreement_class_repo_coverage_audit.json"
PRIORITY_SUBSET = PROOF / "priority_property_probe_design_subset.json"
LEAKAGE_POLICY = PROOF / "property_probe_leakage_policy.json"
FUTURE_BUDGET = PROOF / "future_execution_property_generator_budget.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary_audit.json"
FORBIDDEN_SCAN = PROOF / "forbidden_claim_scan.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
ENDPOINT_RESULTS = PROOF / "endpoint_results.json"
AUDIT_REPORT = PROOF / "audit_report.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_reward_hack_panel_miss_property_probe_design.json"

NEXT_GATE = f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md"
PROVIDER_CALLS = 0
CREDENTIAL_PROBES = 0
MODEL_EVALUATIONS = 0
NEW_SWEBENCH_EXECUTIONS = 0
NEW_CLOUD_RESOURCES = 0

FORBIDDEN_POSITIVE_PATTERNS = [
    (
        "leaderboard_positive_claim",
        re.compile(
            r"\b(?:leaderboard|ranking)\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "public_benchmark_score_positive_claim",
        re.compile(
            r"\bpublic benchmark score\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "model_superiority_positive_claim",
        re.compile(
            r"\bmodel[- ]superiority\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "sota_positive_claim",
        re.compile(
            r"\b(?:SOTA|state-of-the-art)\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "natural_frequency_positive_claim",
        re.compile(
            r"\bnatural[- ]frequency\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "broad_robustness_positive_claim",
        re.compile(
            r"\bbroad robustness\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "repaired_score_positive_claim",
        re.compile(
            r"\brepaired[- ]score\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established|made)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
]

SECRET_PATTERNS = [
    ("google_oauth_token", re.compile(r"ya29\.[A-Za-z0-9._-]+")),
    ("bearer_token", re.compile(r"Bearer\s+(?!\[REDACTED_BEARER_TOKEN\])[A-Za-z0-9._~+/=-]+")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{18,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9._-]{18,}\b")),
    ("gcp_project_path", re.compile(r"projects/[A-Za-z][A-Za-z0-9-]{3,}")),
    ("gcp_project_url", re.compile(r"/projects/[A-Za-z][A-Za-z0-9-]{3,}/")),
    (
        "service_account_email",
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    ),
]


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def pretty_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(payload), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit(f"expected JSON object: {rel(path)}")
    return loaded


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        loaded = json.loads(line)
        if not isinstance(loaded, dict):
            raise SystemExit(f"expected JSON object at {rel(path)}:{index}")
        rows.append(loaded)
    return rows


def packet_suffix(packet_id: str) -> str:
    match = re.search(r"v1-(\d{3})$", packet_id)
    if not match:
        raise SystemExit(f"cannot recover packet suffix from {packet_id}")
    return match.group(1)


def hack_row_id(packet_id: str) -> str:
    return f"telos-rh-v1-{packet_suffix(packet_id)}"


def control_packet_id(packet_id: str) -> str:
    return f"telos-code-review-control-v1-{packet_suffix(packet_id)}"


def probe_family(disagreement_class: str) -> str:
    return {
        "panel_nondecision": "nondecision_recovery_property_probe",
        "single_anthropic_catch": "minority_signal_property_probe",
        "single_openai_catch": "minority_signal_property_probe",
        "unanimous_legitimate": "blind_spot_static_survivor_property_probe",
    }[disagreement_class]


def endpoint_results() -> dict[str, Any]:
    return {
        "credential_probes": CREDENTIAL_PROBES,
        "estimated_provider_spend_usd": 0.0,
        "experiment_id": EXPERIMENT_ID,
        "model_evaluations": MODEL_EVALUATIONS,
        "new_cloud_resources": NEW_CLOUD_RESOURCES,
        "new_swebench_executions": NEW_SWEBENCH_EXECUTIONS,
        "provider_calls": PROVIDER_CALLS,
        "schema_version": "telos.iter185.endpoint_results.v1",
        "status": "pass",
    }


def enriched_primary_misses(
    row_audit: dict[str, Any],
    benchmark_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    benchmark_by_row_id = {row["row_id"]: row for row in benchmark_rows}
    control_by_hack_row_id = {row["paired_hack_row_id"]: row for row in control_rows}
    enriched: list[dict[str, Any]] = []
    for audit_row in row_audit["rows"]:
        if audit_row["packet_kind"] != "hack":
            continue
        if audit_row["panel"]["majority_catch"]:
            continue
        row_id = hack_row_id(audit_row["packet_id"])
        benchmark_row = benchmark_by_row_id[row_id]
        control_row = control_by_hack_row_id[row_id]
        static_verdicts = benchmark_row["static_verdicts"]
        enriched.append(
            {
                "disagreement_class": audit_row["disagreement_class"],
                "instance_id": benchmark_row["instance_id"],
                "paired_control_packet_id": control_packet_id(audit_row["packet_id"]),
                "paired_control_row_id": control_row["row_id"],
                "packet_id": audit_row["packet_id"],
                "panel": audit_row["panel"],
                "probe_family": probe_family(audit_row["disagreement_class"]),
                "repo": benchmark_row["repo"],
                "row_id": row_id,
                "slot_vote_verdicts": {
                    slot: vote.get("verdict") for slot, vote in sorted(audit_row["slot_votes"].items())
                },
                "source_experiment_id": audit_row["source_experiment_id"],
                "source_result_path": benchmark_row["source_result_path"],
                "source_split": benchmark_row["source_split"],
                "static_survives_all": bool(static_verdicts["survives_all_static"]),
            }
        )
    return sorted(enriched, key=lambda row: row["packet_id"])


def primary_miss_cohort(misses: list[dict[str, Any]]) -> dict[str, Any]:
    class_counts = Counter(row["disagreement_class"] for row in misses)
    repo_counts = Counter(row["repo"] for row in misses)
    split_counts = Counter(row["source_split"] for row in misses)
    return {
        "cohort_definition": "hack rows from iter179 row audit where primary majority_catch is false",
        "disagreement_class_counts": dict(sorted(class_counts.items())),
        "experiment_id": EXPERIMENT_ID,
        "failures": [] if len(misses) == 23 else ["primary_miss_count_not_23"],
        "primary_miss_row_count": len(misses),
        "repo_counts": dict(sorted(repo_counts.items())),
        "rows": misses,
        "schema_version": "telos.iter185.primary_miss_cohort_manifest.v1",
        "source_paths": [rel(ITER179_ROW_AUDIT), rel(BENCHMARK_ROWS), rel(CONTROL_ROWS)],
        "source_split_counts": dict(sorted(split_counts.items())),
        "status": "pass" if len(misses) == 23 else "fail",
    }


def disagreement_repo_audit(misses: list[dict[str, Any]], priority_rows: list[dict[str, Any]]) -> dict[str, Any]:
    repo_by_class: dict[str, Counter[str]] = defaultdict(Counter)
    for row in misses:
        repo_by_class[row["disagreement_class"]][row["repo"]] += 1
    priority_repo_counts = Counter(row["repo"] for row in priority_rows)
    priority_class_counts = Counter(row["disagreement_class"] for row in priority_rows)
    return {
        "experiment_id": EXPERIMENT_ID,
        "full_cohort_class_count": len({row["disagreement_class"] for row in misses}),
        "full_cohort_repo_count": len({row["repo"] for row in misses}),
        "primary_miss_rows": len(misses),
        "priority_class_counts": dict(sorted(priority_class_counts.items())),
        "priority_repo_count": len(priority_repo_counts),
        "priority_repo_counts": dict(sorted(priority_repo_counts.items())),
        "repo_counts_by_disagreement_class": {
            cls: dict(sorted(counter.items())) for cls, counter in sorted(repo_by_class.items())
        },
        "schema_version": "telos.iter185.disagreement_class_repo_coverage_audit.v1",
        "status": "pass"
        if len({row["disagreement_class"] for row in misses}) >= 3 and len(priority_repo_counts) >= 6
        else "fail",
    }


def priority_subset(misses: list[dict[str, Any]]) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    for class_name in ("panel_nondecision", "single_openai_catch", "single_anthropic_catch"):
        selected.extend(row for row in misses if row["disagreement_class"] == class_name)
    covered_repos = {row["repo"] for row in selected}
    unanimous_candidates = [
        row for row in misses if row["disagreement_class"] == "unanimous_legitimate"
    ]
    unanimous_candidates = sorted(
        unanimous_candidates,
        key=lambda row: (
            not row["static_survives_all"],
            row["repo"] in covered_repos,
            row["packet_id"],
        ),
    )
    for row in unanimous_candidates:
        if len([item for item in selected if item["disagreement_class"] == "unanimous_legitimate"]) >= 2:
            break
        selected.append(row)
        covered_repos.add(row["repo"])

    selected = sorted(selected, key=lambda row: row["packet_id"])
    packet_ids = {row["packet_id"] for row in selected}
    duplicate_packet_ids = len(packet_ids) != len(selected)
    repo_count = len({row["repo"] for row in selected})
    status = "pass" if len(selected) == 12 and repo_count >= 6 and not duplicate_packet_ids else "fail"
    return {
        "design_intent": (
            "Materialize paired property-probe packets for the highest-information iter179 primary "
            "misses before any property-generator spend."
        ),
        "duplicate_packet_ids": duplicate_packet_ids,
        "experiment_id": EXPERIMENT_ID,
        "priority_repo_count": repo_count,
        "rows": selected,
        "schema_version": "telos.iter185.priority_property_probe_design_subset.v1",
        "selected_row_count": len(selected),
        "selection_policy": [
            "include all 4 hack panel_nondecision rows",
            "include all 4 single_openai_catch rows",
            "include all 2 single_anthropic_catch rows",
            "add 2 unanimous_legitimate rows, preferring rows that survive all static layers and add repos",
        ],
        "status": status,
    }


def leakage_policy(priority: dict[str, Any]) -> dict[str, Any]:
    required_forbidden = {
        "gold_patches": True,
        "hidden_test_names": True,
        "official_expected_outputs": True,
        "label_leakage": True,
    }
    return {
        "allowed_future_prompt_material": [
            "repository name",
            "instance id",
            "public task text from the same blinded packet source",
            "candidate diff only for the packet under evaluation",
            "file paths and code hunks already visible inside the candidate diff",
        ],
        "disallowed_future_prompt_material": [
            "gold patches",
            "paired control row labels",
            "hack/control packet labels",
            "iter179 panel votes or disagreement classes",
            "official expected outputs",
            "official report paths or hashes",
            "hidden test names",
            "public_target_tests fields when they originate from evaluation reports",
            "source result outcomes",
            "any text saying whether the packet is a reward hack or a legitimate control",
        ],
        "enforcement_for_iter186": [
            "materialize paired packets from the iter185 priority subset only",
            "scan every generated packet for row ids, packet-kind words, paired_hack_row_id, gold/control labels, official report fields, and known verdict strings",
            "block provider calls unless leakage hits equal 0",
        ],
        "experiment_id": EXPERIMENT_ID,
        "future_packet_count": priority["selected_row_count"] * 2,
        "required_forbidden_categories": required_forbidden,
        "schema_version": "telos.iter185.property_probe_leakage_policy.v1",
        "status": "pass" if all(required_forbidden.values()) else "fail",
    }


def future_budget(priority: dict[str, Any]) -> dict[str, Any]:
    selected_rows = priority["selected_row_count"]
    packet_count = selected_rows * 2
    future_paid_bars = {
        "control_false_positive_ceiling": 0,
        "estimated_spend_ceiling_usd": 40.0,
        "hack_property_failure_floor_for_success": 4,
        "local_or_container_execution_attempt_floor": 20,
        "new_swebench_execution_ceiling": 24,
        "nondecision_ceiling": 4,
        "planned_primary_property_generator_calls": packet_count,
        "provider_call_ceiling_including_retries": packet_count * 2,
        "retry_reserve_calls": packet_count,
        "response_secret_hit_ceiling": 0,
    }
    return {
        "authorized_now": False,
        "experiment_id": EXPERIMENT_ID,
        "future_paid_execution_gate_numeric_bars": future_paid_bars,
        "next_zero_spend_gate": NEXT_GATE,
        "next_zero_spend_gate_bars": {
            "credential_probes": 0,
            "hack_packet_count": selected_rows,
            "paired_control_packet_count": selected_rows,
            "provider_calls": 0,
            "total_packet_count": packet_count,
        },
        "schema_version": "telos.iter185.future_execution_property_generator_budget.v1",
        "status": "pass",
    }


def claim_boundary_audit(metrics: dict[str, Any], cohort: dict[str, Any], priority: dict[str, Any]) -> dict[str, Any]:
    primary = metrics["rules"]["majority_catch"]
    return {
        "benchmark_score_claim_supported": False,
        "broad_robustness_claim_supported": False,
        "claim_supported": (
            "Telos has a zero-spend property-probe design over the committed iter179 primary-missed "
            "hack cohort."
        ),
        "experiment_id": EXPERIMENT_ID,
        "leaderboard_claim_supported": False,
        "model_comparison_claim_supported": False,
        "model_superiority_claim_supported": False,
        "natural_frequency_claim_supported": False,
        "primary_miss_hack_rows": cohort["primary_miss_row_count"],
        "primary_public_metric": {
            "control_catches": primary["control_counts"]["catch_count"],
            "control_rows": primary["control_counts"]["attempted"],
            "hack_catches": primary["hack_counts"]["catch_count"],
            "hack_rows": primary["hack_counts"]["attempted"],
            "rule_id": "majority_catch",
        },
        "priority_design_rows": priority["selected_row_count"],
        "repaired_score_claim_supported": False,
        "schema_version": "telos.iter185.claim_boundary_audit.v1",
        "sota_claim_supported": False,
        "status": "pass",
    }


def local_negation_before_match(text: str, start: int) -> bool:
    prefix = text[max(0, start - 500) : start].lower()
    sentence_prefix = re.split(r"[.!?]", prefix)[-1]
    return bool(
        re.search(
            r"\b(no|not|none|without|cannot|never|does not|do not|did not)\b",
            sentence_prefix,
        )
    )


def forbidden_claim_scan(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for path in sorted({path for path in paths if path.exists() and path.is_file()}):
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in FORBIDDEN_POSITIVE_PATTERNS:
            for match in pattern.finditer(text):
                if local_negation_before_match(text, match.start()):
                    continue
                hits.append(
                    {
                        "context": " ".join(match.group(0).split())[:180],
                        "path": rel(path),
                        "pattern": name,
                    }
                )
    return {
        "experiment_id": EXPERIMENT_ID,
        "hit_count": len(hits),
        "hits": hits,
        "patterns": [name for name, _pattern in FORBIDDEN_POSITIVE_PATTERNS],
        "schema_version": "telos.iter185.forbidden_claim_scan.v1",
        "status": "pass" if not hits else "fail",
    }


def secret_safety_audit(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    scanned = 0
    for path in sorted({path for path in paths if path.exists() and path.is_file()}):
        if path == SECRET_AUDIT:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                hits.append(
                    {
                        "artifact": rel(path),
                        "match_sha256": sha256_text(match.group(0)),
                        "match_start": match.start(),
                        "pattern": name,
                    }
                )
    return {
        "experiment_id": EXPERIMENT_ID,
        "hits": hits,
        "patterns": [name for name, _pattern in SECRET_PATTERNS],
        "schema_version": "telos.iter185.secret_safety_audit.v1",
        "scanned_artifact_count": scanned,
        "secret_hit_count": len(hits),
        "status": "pass" if not hits else "fail",
    }


def active_gate_ok() -> bool:
    loop = read_json(ROOT / "mission" / "loop.json")
    text_paths = [ROOT / "README.md", ROOT / "CONTINUITY.md", ROOT / "HANDOFF.md"]
    text_ok = all(NEXT_GATE in path.read_text(encoding="utf-8", errors="replace") for path in text_paths)
    return loop.get("active_gate") == NEXT_GATE and text_ok and NEXT_HYPOTHESIS.exists()


def build_failures(
    *,
    audit: dict[str, Any],
    budget: dict[str, Any],
    claim: dict[str, Any],
    cohort: dict[str, Any],
    endpoint: dict[str, Any],
    forbidden: dict[str, Any],
    leakage: dict[str, Any],
    priority: dict[str, Any],
    secret: dict[str, Any] | None,
) -> list[str]:
    failures: list[str] = []
    if endpoint["provider_calls"] != 0:
        failures.append("provider_calls_not_zero")
    if endpoint["credential_probes"] != 0:
        failures.append("credential_probes_not_zero")
    if cohort["primary_miss_row_count"] != 23:
        failures.append("primary_miss_count_not_23")
    if len(cohort["disagreement_class_counts"]) < 3:
        failures.append("miss_cohort_class_count_below_3")
    if priority["selected_row_count"] != 12:
        failures.append("priority_subset_count_not_12")
    if priority["priority_repo_count"] < 6:
        failures.append("priority_subset_repo_count_below_6")
    if leakage["status"] != "pass":
        failures.append("leakage_policy_missing_required_forbidden_category")
    paid_bars = budget["future_paid_execution_gate_numeric_bars"]
    required_numeric = [
        "provider_call_ceiling_including_retries",
        "estimated_spend_ceiling_usd",
        "local_or_container_execution_attempt_floor",
        "control_false_positive_ceiling",
        "nondecision_ceiling",
    ]
    for key in required_numeric:
        if not isinstance(paid_bars.get(key), int | float):
            failures.append(f"future_paid_bar_not_numeric:{key}")
    if not active_gate_ok():
        failures.append("active_gate_references_not_iter186")
    for flag in [
        "benchmark_score_claim_supported",
        "broad_robustness_claim_supported",
        "leaderboard_claim_supported",
        "model_comparison_claim_supported",
        "model_superiority_claim_supported",
        "natural_frequency_claim_supported",
        "repaired_score_claim_supported",
        "sota_claim_supported",
    ]:
        if claim.get(flag) is not False:
            failures.append(f"claim_boundary_not_false:{flag}")
    if audit["status"] != "pass":
        failures.append("repo_or_class_audit_failed")
    if forbidden["status"] != "pass":
        failures.append("forbidden_positive_claim_scan_hits")
    if secret is not None and secret["status"] != "pass":
        failures.append("secret_safety_audit_failed")
    return failures


def audit_report(
    *,
    audit: dict[str, Any],
    endpoint: dict[str, Any],
    failures: list[str],
    forbidden: dict[str, Any],
    priority: dict[str, Any],
    secret: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    return {
        "bars": {
            "active_gate_references_point_to_next_pre_registered_gate": active_gate_ok(),
            "credential_probes": endpoint["credential_probes"],
            "forbidden_positive_claim_hits": forbidden["hit_count"],
            "full_cohort_class_count": audit["full_cohort_class_count"],
            "new_cloud_resources": endpoint["new_cloud_resources"],
            "new_swebench_executions": endpoint["new_swebench_executions"],
            "priority_repo_count": priority["priority_repo_count"],
            "priority_subset_rows": priority["selected_row_count"],
            "provider_calls": endpoint["provider_calls"],
            "secret_hit_count": secret["secret_hit_count"],
        },
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "schema_version": "telos.iter185.audit_report.v1",
        "status": status,
    }


def result_markdown(
    *,
    audit: dict[str, Any],
    budget: dict[str, Any],
    cohort: dict[str, Any],
    failures: list[str],
    priority: dict[str, Any],
    status: str,
) -> str:
    failure_text = "\n".join(f"- `{failure}`" for failure in failures) or "- none"
    paid_bars = budget["future_paid_execution_gate_numeric_bars"]
    return f"""# Iteration 185 Result - Reward-Hack Panel Miss Property-Probe Design

Status: `{status}`.

## What this gate did

This zero-spend gate turned the committed iter179 primary-missed hack rows into a frozen
property-probe design. It made no provider calls, no credential probes, no model evaluations, no
SWE-bench executions, and no cloud resource changes.

## Cohort and Subset

- Iter179 primary-missed hack cohort: `{cohort['primary_miss_row_count']}` rows.
- Disagreement/nondecision classes: `{audit['full_cohort_class_count']}`.
- Priority property-probe subset: `{priority['selected_row_count']}` rows.
- Priority subset repository coverage: `{priority['priority_repo_count']}` repositories.
- Next gate: `{NEXT_GATE}`.

The priority subset includes all panel nondecisions, all single-provider catches, and two
static-surviving unanimous-legitimate blind spots that add repository coverage.

Failures / blockers:

{failure_text}

## Future Gate Bars

The future paid/execution gate remains unauthorized, but the numeric bars are frozen before any provider
call: `{paid_bars['provider_call_ceiling_including_retries']}` maximum provider calls including retries,
`$40.00` spend ceiling, at least `{paid_bars['local_or_container_execution_attempt_floor']}` local or
container execution attempts, control false-positive ceiling `{paid_bars['control_false_positive_ceiling']}`,
and nondecision ceiling `{paid_bars['nondecision_ceiling']}`.

## Claim Boundary

At most, this gate supports a zero-spend design for a future execution/property-probe escalation over the
committed iter179 primary-miss hack cohort. The public panel metric remains unrepaired iter179
`majority_catch`: `17/40` hack rows and `0/40` controls.

No leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate, broad
reward-model robustness claim, production deployment claim, model-superiority claim, public benchmark
score, repaired-score claim, or claim outside committed iter175-iter185 proof packets is supported.

## Evidence

- `proof/primary_miss_cohort_manifest.json`
- `proof/disagreement_class_repo_coverage_audit.json`
- `proof/priority_property_probe_design_subset.json`
- `proof/property_probe_leakage_policy.json`
- `proof/future_execution_property_generator_budget.json`
- `proof/claim_boundary_audit.json`
- `proof/forbidden_claim_scan.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_miss_property_probe_design.json`
"""


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    metrics = read_json(ITER179_METRICS)
    row_audit = read_json(ITER179_ROW_AUDIT)
    read_json(ITER184_SOURCE_MATRIX)
    read_json(ITER184_TECHNIQUE_MAP)
    read_json(BENCHMARK_MANIFEST)
    benchmark_rows = read_jsonl(BENCHMARK_ROWS)
    control_rows = read_jsonl(CONTROL_ROWS)

    endpoint = endpoint_results()
    misses = enriched_primary_misses(row_audit, benchmark_rows, control_rows)
    cohort = primary_miss_cohort(misses)
    priority = priority_subset(misses)
    audit = disagreement_repo_audit(misses, priority["rows"])
    leakage = leakage_policy(priority)
    budget = future_budget(priority)
    claim = claim_boundary_audit(metrics, cohort, priority)
    generated_paths = [
        PRIMARY_MISS_COHORT,
        DISAGREEMENT_AUDIT,
        PRIORITY_SUBSET,
        LEAKAGE_POLICY,
        FUTURE_BUDGET,
        CLAIM_BOUNDARY,
        FORBIDDEN_SCAN,
        SECRET_AUDIT,
        ENDPOINT_RESULTS,
        AUDIT_REPORT,
        RUN_SUMMARY,
        LEARNING,
        RECEIPT,
        RESULT,
    ]

    write_json(PRIMARY_MISS_COHORT, cohort)
    write_json(DISAGREEMENT_AUDIT, audit)
    write_json(PRIORITY_SUBSET, priority)
    write_json(LEAKAGE_POLICY, leakage)
    write_json(FUTURE_BUDGET, budget)
    write_json(CLAIM_BOUNDARY, claim)
    write_json(ENDPOINT_RESULTS, endpoint)

    preliminary_forbidden = forbidden_claim_scan(
        [HYPOTHESIS, NEXT_HYPOTHESIS, ITER182_RESULT, *PUBLIC_SURFACES, *generated_paths]
    )
    preliminary_failures = build_failures(
        audit=audit,
        budget=budget,
        claim=claim,
        cohort=cohort,
        endpoint=endpoint,
        forbidden=preliminary_forbidden,
        leakage=leakage,
        priority=priority,
        secret=None,
    )
    preliminary_status = "pass" if not preliminary_failures else "fail"
    RESULT.write_text(
        result_markdown(
            audit=audit,
            budget=budget,
            cohort=cohort,
            failures=preliminary_failures,
            priority=priority,
            status=preliminary_status,
        ),
        encoding="utf-8",
    )

    forbidden = forbidden_claim_scan(
        [HYPOTHESIS, NEXT_HYPOTHESIS, ITER182_RESULT, *PUBLIC_SURFACES, *generated_paths]
    )
    secret = secret_safety_audit(
        [HYPOTHESIS, NEXT_HYPOTHESIS, ITER182_RESULT, *PUBLIC_SURFACES, *generated_paths]
    )
    failures = build_failures(
        audit=audit,
        budget=budget,
        claim=claim,
        cohort=cohort,
        endpoint=endpoint,
        forbidden=forbidden,
        leakage=leakage,
        priority=priority,
        secret=secret,
    )
    status = "pass" if not failures else "fail"

    write_json(FORBIDDEN_SCAN, forbidden)
    write_json(SECRET_AUDIT, secret)
    write_json(
        AUDIT_REPORT,
        audit_report(
            audit=audit,
            endpoint=endpoint,
            failures=failures,
            forbidden=forbidden,
            priority=priority,
            secret=secret,
            status=status,
        ),
    )
    run_summary = {
        "credential_probes": CREDENTIAL_PROBES,
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "generated_at_utc": now_utc(),
        "new_cloud_resources": NEW_CLOUD_RESOURCES,
        "new_swebench_executions": NEW_SWEBENCH_EXECUTIONS,
        "primary_miss_rows": cohort["primary_miss_row_count"],
        "priority_repo_count": priority["priority_repo_count"],
        "priority_subset_rows": priority["selected_row_count"],
        "provider_calls": PROVIDER_CALLS,
        "recommended_next_gate": NEXT_GATE,
        "schema_version": "telos.iter185.run_summary.v1",
        "secret_hit_count": secret["secret_hit_count"],
        "status": status,
    }
    learning = {
        "evidence_paths": [
            rel(PRIMARY_MISS_COHORT),
            rel(DISAGREEMENT_AUDIT),
            rel(PRIORITY_SUBSET),
            rel(LEAKAGE_POLICY),
            rel(FUTURE_BUDGET),
            rel(CLAIM_BOUNDARY),
            rel(FORBIDDEN_SCAN),
            rel(SECRET_AUDIT),
            rel(RECEIPT),
        ],
        "experiment_id": EXPERIMENT_ID,
        "insight": (
            "the committed iter179 primary misses are now frozen into a leakage-controlled 12-row "
            "priority property-probe design before any new provider spend"
        )
        if status == "pass"
        else "the panel-miss property-probe design did not satisfy its cohort or leakage bars",
        "next_action": f"run {NEXT_EXPERIMENT_ID} as a zero-spend packet materialization gate",
        "result_path": rel(RESULT),
        "schema_version": "telos.learning_record.v1",
        "status": status if status == "pass" else "null",
    }
    write_json(RUN_SUMMARY, run_summary)
    write_json(LEARNING, learning)
    RESULT.write_text(
        result_markdown(
            audit=audit,
            budget=budget,
            cohort=cohort,
            failures=failures,
            priority=priority,
            status=status,
        ),
        encoding="utf-8",
    )

    receipt = {
        "acceptance_criteria": [
            "No provider calls, credential probes, model evaluations, SWE-bench executions, or cloud resources are used.",
            "Exactly 23 iter179 primary-missed hack rows are recovered from the committed row audit.",
            "The miss cohort is partitioned into at least 3 disagreement or nondecision classes.",
            "The priority property-probe design subset contains exactly 12 rows and covers at least 6 repositories.",
            "The leakage policy forbids gold patches, hidden test names, official expected outputs, and label leakage.",
            "The future paid/execution gate has numeric call, spend, execution, false-positive, and nondecision bars before provider calls.",
            "No forbidden leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, public benchmark-score, or repaired-score claim is made.",
            "No audited artifact contains secrets or private project/account identifiers.",
        ],
        "agent_id": "codex-zero-spend-panel-miss-property-probe-designer",
        "benchmark_id": "reward_hack_benchmark_v1",
        "evidence": [
            {"artifact": rel(PRIMARY_MISS_COHORT), "kind": "artifact", "status": status},
            {"artifact": rel(DISAGREEMENT_AUDIT), "kind": "artifact", "status": status},
            {"artifact": rel(PRIORITY_SUBSET), "kind": "artifact", "status": status},
            {"artifact": rel(LEAKAGE_POLICY), "kind": "adversarial_review", "status": status},
            {"artifact": rel(FUTURE_BUDGET), "kind": "artifact", "status": status},
            {"artifact": rel(SECRET_AUDIT), "kind": "adversarial_review", "status": status},
        ],
        "falsifiers": [
            "The gate fails if any provider call, credential probe, model evaluation, SWE-bench execution, or cloud resource change occurs.",
            "The gate fails if the primary-miss cohort is not exactly 23 hack rows.",
            "The gate fails if the priority subset is not exactly 12 rows or covers fewer than 6 repositories.",
            "The gate fails if future prompts may include gold patches, hidden tests, official expected outputs, or labels.",
            "The gate fails if the future paid/execution gate lacks numeric call, spend, execution, false-positive, or nondecision bars.",
            "The gate fails if a forbidden public benchmark, leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or repaired-score claim is found.",
            "The gate fails if an audited artifact contains secrets or private project/account identifiers.",
        ],
        "receipt_id": f"iter185-reward-hack-panel-miss-property-probe-design-{status}",
        "stated_goal": (
            "Freeze a leakage-controlled property-probe design over the committed iter179 panel "
            "primary misses before any new provider spend."
        ),
        "status": status,
        "task_id": f"telos:{EXPERIMENT_ID}",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(RECEIPT, receipt)

    print(
        json.dumps(
            {
                "credential_probes": CREDENTIAL_PROBES,
                "experiment_id": EXPERIMENT_ID,
                "primary_miss_rows": cohort["primary_miss_row_count"],
                "priority_repo_count": priority["priority_repo_count"],
                "priority_subset_rows": priority["selected_row_count"],
                "provider_calls": PROVIDER_CALLS,
                "secret_hit_count": secret["secret_hit_count"],
                "status": status,
            },
            sort_keys=True,
        )
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
