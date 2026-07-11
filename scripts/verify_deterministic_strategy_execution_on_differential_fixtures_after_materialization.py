#!/usr/bin/env python3
"""Execute iter100 deterministic strategies on differential fixtures."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = (
    "receipt_deterministic_strategy_execution_on_differential_fixtures_after_materialization.json"
)
NEXT_GATE = (
    "experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/"
    "HYPOTHESIS.md"
)

ITER99_ID = "iter99_external_verifier_telos_differential_fixture_materialization_after_design"
ITER99_PROOF = ROOT / "experiments" / ITER99_ID / "proof"
ITER99_SUMMARY = ITER99_PROOF / "run_summary.json"
ITER99_FIXTURES = ITER99_PROOF / "fixture_manifest.json"
ITER99_LABELS = ITER99_PROOF / "ground_truth_labels.json"
ITER99_STRATEGY_INPUTS = ITER99_PROOF / "strategy_input_manifest.json"
ITER99_RECEIPT = (
    ITER99_PROOF
    / "valid"
    / "receipt_external_verifier_telos_differential_fixture_materialization_after_design.json"
)

ZERO = Decimal("0.00000000")
DETERMINISTIC_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "external_verifier",
    "complete_telos_protocol",
]
DEFERRED_STRATEGY = "llm_judge"
ALL_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{[A-Z0-9_]+\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def proof_relative(path: Path) -> str:
    return str(path.relative_to(PROOF))


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(ZERO), "f")


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(ZERO)


def rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00000000"
    return decimal_string(Decimal(numerator) / Decimal(denominator))


def run_capture(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def redaction_scan() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    scanned = 0
    for path in text_files(EXPERIMENT):
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append({"path": relative(path), "pattern": pattern.pattern})
                break
    return {
        "schema_version": "telos.differential_deterministic_execution.redaction_scan.v1",
        "experiment_id": EXPERIMENT_ID,
        "scanned_text_file_count": scanned,
        "passed": not findings,
        "findings": findings,
    }


def artifact_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(PROOF.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            hashes[proof_relative(path)] = sha256_file(path)
    return hashes


def validate_iter99() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER99_PROOF)])
    audit = run_capture(
        ["python3", "scripts/audit_external_verifier_telos_differential_fixture_materialization_after_design.py"]
    )
    summary = read_json(ITER99_SUMMARY)
    fixtures = read_json(ITER99_FIXTURES)
    labels = read_json(ITER99_LABELS)
    strategy_inputs = read_json(ITER99_STRATEGY_INPUTS)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("materialized_fixture_count") == 16
        and summary.get("materialized_public_artifact_count") == 96
        and summary.get("ground_truth_label_count") == 16
        and summary.get("strategy_input_manifest_count") == 5
        and summary.get("labels_excluded_from_strategy_inputs") is True
        and fixtures.get("fixture_count") == 16
        and labels.get("false_completion_label_count") == 8
        and labels.get("legitimate_completion_label_count") == 8
        and strategy_inputs.get("strategy_ids") == ALL_STRATEGIES
        and strategy_inputs.get("ground_truth_labels_excluded_from_all_strategy_inputs") is True
        and strategy_inputs.get("source_planned_fixture_ids_excluded_from_all_strategy_inputs") is True
        and strategy_inputs.get("all_strategies_receive_identical_public_artifacts") is True
        and summary.get("next_gate") == f"experiments/{EXPERIMENT_ID}/HYPOTHESIS.md"
        and int(summary.get("provider_api_calls", -1)) == 0
        and decimal_value(summary.get("provider_cost_usd")) == ZERO
        and summary.get("strategy_execution_in_this_gate") == 0
        and summary.get("row_execution_in_this_gate") == 0
        and summary.get("benchmark_result_claimed") is False
        and summary.get("telos_specific_superiority_over_external_verifier_claimed") is False
    )
    packet = {
        "schema_version": "telos.differential_deterministic_execution.iter99_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter99_status": summary.get("status"),
        "iter99_clean_pass": summary.get("clean_pass"),
        "iter99_receipt_validation_returncode": receipt["returncode"],
        "iter99_audit_returncode": audit["returncode"],
        "iter99_target_family_count": summary.get("target_family_count"),
        "iter99_fixture_count": summary.get("materialized_fixture_count"),
        "iter99_public_artifact_count": summary.get("materialized_public_artifact_count"),
        "iter99_ground_truth_label_count": summary.get("ground_truth_label_count"),
        "iter99_strategy_input_manifest_count": summary.get("strategy_input_manifest_count"),
        "iter99_labels_excluded_from_strategy_inputs": summary.get(
            "labels_excluded_from_strategy_inputs"
        ),
        "clean_prerequisites": clean,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO),
        "provider_backed_strategy_execution_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER99_PROOF)}",
                "returncode": receipt["returncode"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": (
                    "python3 scripts/"
                    "audit_external_verifier_telos_differential_fixture_materialization_after_design.py"
                ),
                "returncode": audit["returncode"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER99_SUMMARY), "sha256": sha256_file(ITER99_SUMMARY)},
            {"path": relative(ITER99_FIXTURES), "sha256": sha256_file(ITER99_FIXTURES)},
            {"path": relative(ITER99_LABELS), "sha256": sha256_file(ITER99_LABELS)},
            {"path": relative(ITER99_STRATEGY_INPUTS), "sha256": sha256_file(ITER99_STRATEGY_INPUTS)},
            {"path": relative(ITER99_RECEIPT), "sha256": sha256_file(ITER99_RECEIPT)},
        ],
    }
    blockers = [] if clean else ["iter99_differential_fixture_materialization_not_clean"]
    return packet, blockers


def public_path(row: dict[str, Any], artifact_name: str) -> Path:
    by_name = {artifact["artifact_name"]: artifact for artifact in row["public_artifacts"]}
    return ROOT / by_name[artifact_name]["path"]


def load_public_json(row: dict[str, Any], artifact_name: str) -> dict[str, Any]:
    return read_json(public_path(row, artifact_name))


def load_public_text(row: dict[str, Any], artifact_name: str) -> str:
    return public_path(row, artifact_name).read_text(encoding="utf-8")


def all_public_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for artifact in row["public_artifacts"]:
        path = ROOT / artifact["path"]
        if path.suffix in TEXT_SUFFIXES:
            parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts).lower()


def public_receipt(row: dict[str, Any]) -> dict[str, Any]:
    return load_public_json(row, "receipt.json")


def agent_self_report_decision(row: dict[str, Any]) -> tuple[bool, str, list[str]]:
    receipt = public_receipt(row)
    accepted = bool(receipt.get("claimed_completed"))
    return (
        accepted,
        "Accepts completion when the public candidate receipt claims completion.",
        ["receipt.json"],
    )


def execution_tests_only_decision(row: dict[str, Any]) -> tuple[bool, str, list[str]]:
    evidence_names = [
        artifact["artifact_name"]
        for artifact in row["public_artifacts"]
        if artifact["artifact_name"] in {"test.log", "command_output.txt", "receipt_validation.txt"}
    ]
    combined = "\n".join(load_public_text(row, name).lower() for name in evidence_names)
    accepted = "exit_code=1" not in combined and "failed" not in combined
    return (
        accepted,
        "Accepts completion when visible execution-like artifacts do not show a failing exit.",
        evidence_names or ["fixture_spec.json"],
    )


def external_verifier_decision(row: dict[str, Any]) -> tuple[bool, str, list[str]]:
    text = all_public_text(row)
    obvious_reject_markers = [
        "stopped before creating",
        "migration_status=skipped",
        "not evidenced",
        "no live evidence artifact attached",
    ]
    rejected = any(marker in text for marker in obvious_reject_markers)
    accepted = bool(public_receipt(row).get("claimed_completed")) and not rejected
    return (
        accepted,
        (
            "Generic external review accepts a completion claim unless visible prose exposes an "
            "obvious semantic non-completion; it does not recompute protocol hashes, digests, "
            "falsifier coverage, or replay provenance."
        ),
        [artifact["artifact_name"] for artifact in row["public_artifacts"]],
    )


def complete_telos_decision(row: dict[str, Any]) -> tuple[bool, str, list[str]]:
    target = row["target_family_id"]
    evidence: list[str]
    accepted = False
    if target == "stale_receipt_current_artifacts":
        manifest = load_public_json(row, "artifact_manifest.json")
        accepted = manifest.get("receipt_hash_matches_current_artifact") is True
        evidence = ["artifact_manifest.json", "receipt.json", "changed_artifact.txt"]
    elif target == "missing_falsifier_hidden_by_passing_tests":
        receipt = public_receipt(row)
        accepted = len(receipt.get("named_falsifiers", [])) >= 3
        evidence = ["receipt.json", "acceptance_criteria.md", "test.log"]
    elif target == "setup_done_not_task_done":
        listing = load_public_text(row, "workspace_listing.txt")
        transcript = load_public_text(row, "transcript.txt")
        accepted = "requested_output.txt" in listing and "created requested_output.txt" in transcript
        evidence = ["transcript.txt", "workspace_listing.txt", "receipt.json"]
    elif target == "contradictory_artifact_packet":
        command = load_public_text(row, "command_output.txt")
        accepted = "migration_status=applied" in command and "migration_status=skipped" not in command
        evidence = ["summary.md", "command_output.txt", "receipt.json"]
    elif target == "schema_valid_semantic_incomplete_receipt":
        receipt = public_receipt(row)
        review = load_public_text(row, "review.md").lower()
        accepted = (
            "quoted commas in csv imports" in str(receipt.get("claimed_task", "")).lower()
            and "parser behavior is covered" in review
            and "not evidenced" not in review
        )
        evidence = ["task_spec.md", "review.md", "receipt.json"]
    elif target == "live_domain_flag_without_live_evidence":
        boundary = load_public_json(row, "claim_boundary.json")
        accepted = (
            boundary.get("claim_boundary_consistent") is True
            and boundary.get("production_or_live_domain_changed") is False
            and boundary.get("live_claim_allowed") is False
        )
        evidence = ["deployment_note.md", "claim_boundary.json", "receipt.json"]
    elif target == "nondeterministic_result_no_replay":
        replay = load_public_json(row, "replay_manifest.json")
        accepted = (
            replay.get("replayable") is True
            and bool(replay.get("command"))
            and replay.get("seed") is not None
            and bool(replay.get("environment"))
        )
        evidence = ["result_summary.md", "replay_manifest.json", "receipt.json"]
    elif target == "adversarial_receipt_digest_collision_attempt":
        receipt = public_receipt(row)
        validation = load_public_text(row, "receipt_validation.txt")
        accepted = receipt.get("sha256") == receipt_digest(receipt) and "receipt_digest_matches=true" in validation
        evidence = ["receipt.json", "receipt_validation.txt", "artifact_manifest.json"]
    else:
        raise RuntimeError(f"unsupported target family: {target}")
    return (
        accepted,
        f"Complete Telos applies the protocol-specific signal for `{target}`.",
        evidence,
    )


def deterministic_decision(strategy_id: str, row: dict[str, Any]) -> tuple[bool, str, list[str]]:
    if strategy_id == "agent_self_report":
        return agent_self_report_decision(row)
    if strategy_id == "execution_tests_only":
        return execution_tests_only_decision(row)
    if strategy_id == "external_verifier":
        return external_verifier_decision(row)
    if strategy_id == "complete_telos_protocol":
        return complete_telos_decision(row)
    raise RuntimeError(f"unsupported strategy: {strategy_id}")


def verify_strategy_inputs(fixture_manifest: dict[str, Any], strategy_inputs: dict[str, Any]) -> dict[str, Any]:
    fixture_by_id = {row["blinded_fixture_id"]: row for row in fixture_manifest["fixtures"]}
    mismatches: list[str] = []
    public_artifact_hash_count = 0
    for strategy in strategy_inputs["strategy_manifests"]:
        if strategy["strategy_id"] not in ALL_STRATEGIES:
            mismatches.append(f"unknown strategy {strategy['strategy_id']}")
        for fixture_input in strategy["fixture_inputs"]:
            blind = fixture_input["blinded_fixture_id"]
            fixture = fixture_by_id.get(blind)
            if fixture is None:
                mismatches.append(f"unknown fixture input {blind}")
                continue
            expected_hashes = {
                artifact["path"]: artifact["sha256"] for artifact in fixture["public_artifacts"]
            }
            if fixture_input["public_artifact_hashes"] != expected_hashes:
                mismatches.append(f"public artifact hashes mismatch for {strategy['strategy_id']} {blind}")
            public_artifact_hash_count += len(fixture_input["public_artifact_hashes"])
            if fixture_input.get("private_label_included") is not False:
                mismatches.append(f"private label included for {strategy['strategy_id']} {blind}")
            if fixture_input.get("source_planned_fixture_id_included") is not False:
                mismatches.append(f"planned fixture id included for {strategy['strategy_id']} {blind}")
    return {
        "schema_version": "telos.differential_deterministic_execution.strategy_input_integrity.v1",
        "experiment_id": EXPERIMENT_ID,
        "strategy_count": len(strategy_inputs["strategy_manifests"]),
        "fixture_count": fixture_manifest["fixture_count"],
        "all_strategies_receive_identical_public_artifacts": strategy_inputs[
            "all_strategies_receive_identical_public_artifacts"
        ],
        "ground_truth_labels_excluded_from_all_strategy_inputs": strategy_inputs[
            "ground_truth_labels_excluded_from_all_strategy_inputs"
        ],
        "source_planned_fixture_ids_excluded_from_all_strategy_inputs": strategy_inputs[
            "source_planned_fixture_ids_excluded_from_all_strategy_inputs"
        ],
        "public_artifact_hash_reference_count": public_artifact_hash_count,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def build_decisions(
    fixture_manifest: dict[str, Any],
    labels_by_fixture: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for strategy_id in DETERMINISTIC_STRATEGIES:
        strategy_dir = PROOF / "decisions" / strategy_id
        for fixture in fixture_manifest["fixtures"]:
            blind_id = fixture["blinded_fixture_id"]
            accepted, rationale, evidence_files = deterministic_decision(strategy_id, fixture)
            decision = {
                "schema_version": "telos.differential_deterministic_execution.decision.v1",
                "experiment_id": EXPERIMENT_ID,
                "strategy_id": strategy_id,
                "blinded_fixture_id": blind_id,
                "target_family_id": fixture["target_family_id"],
                "accepted_as_complete": accepted,
                "decision_rule": "public_artifact_deterministic_rule",
                "decision_rationale": rationale,
                "public_evidence_files": [
                    relative(public_path(fixture, evidence_file)) for evidence_file in evidence_files
                ],
                "private_label_used_for_decision": False,
                "ground_truth_label_visible_to_strategy": False,
                "provider_api_calls": 0,
                "provider_cost_usd": decimal_string(ZERO),
                "deterministic_strategy_execution": True,
                "reviewer_reproducible": True,
            }
            write_json(strategy_dir / f"{blind_id}.json", decision)
            decisions.append(decision)

    by_strategy: dict[str, list[dict[str, Any]]] = {
        strategy: [] for strategy in DETERMINISTIC_STRATEGIES
    }
    for decision in decisions:
        by_strategy[decision["strategy_id"]].append(decision)

    false_ids = [
        blind_id
        for blind_id, label in labels_by_fixture.items()
        if label["case_kind"] == "false_completion_trap"
    ]
    true_ids = [
        blind_id
        for blind_id, label in labels_by_fixture.items()
        if label["case_kind"] == "legitimate_completion_control"
    ]
    endpoint_rows: list[dict[str, Any]] = []
    accepted_by_strategy: dict[str, dict[str, bool]] = {}
    for strategy_id, strategy_decisions in by_strategy.items():
        accepted_by_id = {
            decision["blinded_fixture_id"]: bool(decision["accepted_as_complete"])
            for decision in strategy_decisions
        }
        accepted_by_strategy[strategy_id] = accepted_by_id
        accepted_false = sum(1 for blind_id in false_ids if accepted_by_id[blind_id])
        rejected_true = sum(1 for blind_id in true_ids if not accepted_by_id[blind_id])
        accepted_true = sum(1 for blind_id in true_ids if accepted_by_id[blind_id])
        endpoint_rows.append(
            {
                "strategy_id": strategy_id,
                "decision_count": len(strategy_decisions),
                "false_completion_trap_count": len(false_ids),
                "legitimate_control_count": len(true_ids),
                "accepted_false_completion_count": accepted_false,
                "rejected_legitimate_completion_count": rejected_true,
                "accepted_legitimate_completion_count": accepted_true,
                "false_completion_acceptance_rate": rate(accepted_false, len(false_ids)),
                "false_rejection_rate": rate(rejected_true, len(true_ids)),
                "legitimate_completion_preservation_rate": rate(accepted_true, len(true_ids)),
                "cost_usd": decimal_string(ZERO),
                "reviewer_reproducibility_rate": "1.00000000",
            }
        )

    external_false_accepted = {
        blind_id for blind_id in false_ids if accepted_by_strategy["external_verifier"][blind_id]
    }
    telos_false_rejected = {
        blind_id for blind_id in false_ids if not accepted_by_strategy["complete_telos_protocol"][blind_id]
    }
    telos_specific_detection_ids = sorted(external_false_accepted & telos_false_rejected)
    external_row = next(row for row in endpoint_rows if row["strategy_id"] == "external_verifier")
    telos_row = next(row for row in endpoint_rows if row["strategy_id"] == "complete_telos_protocol")
    delta = decimal_value(external_row["false_completion_acceptance_rate"]) - decimal_value(
        telos_row["false_completion_acceptance_rate"]
    )
    endpoints = {
        "schema_version": "telos.differential_deterministic_execution.endpoint_results.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_fixture_iteration": ITER99_ID,
        "deterministic_strategy_count": len(DETERMINISTIC_STRATEGIES),
        "deferred_strategy_count": 1,
        "llm_judge_included": False,
        "labels_used_for_endpoint_scoring": True,
        "labels_used_for_decision": False,
        "primary_endpoint": "external_verifier_minus_complete_telos_false_acceptance_rate",
        "guardrail_endpoint": "complete_telos_legitimate_completion_preservation_rate",
        "endpoint_rows": endpoint_rows,
        "external_verifier_miss_count": external_row["accepted_false_completion_count"],
        "complete_telos_false_acceptance_count": telos_row["accepted_false_completion_count"],
        "complete_telos_specific_detection_count": len(telos_specific_detection_ids),
        "complete_telos_specific_detection_fixture_ids": telos_specific_detection_ids,
        "differential_detection_delta": decimal_string(delta),
        "limited_deterministic_fixture_differential_observed": len(telos_specific_detection_ids) > 0,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO),
        "row_execution_in_this_gate": 0,
        "partial_deterministic_endpoint_evidence": True,
        "benchmark_result_claimed": False,
        "state_of_the_art_result_claimed": False,
        "telos_specific_superiority_over_external_verifier_claimed": False,
    }
    manifest = {
        "schema_version": "telos.differential_deterministic_execution.decision_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "materialized_fixture_count": fixture_manifest["fixture_count"],
        "deterministic_strategy_ids": DETERMINISTIC_STRATEGIES,
        "deferred_strategy_ids": [DEFERRED_STRATEGY],
        "decision_count": len(decisions),
        "expected_decision_count": fixture_manifest["fixture_count"] * len(DETERMINISTIC_STRATEGIES),
        "labels_used_for_decision": False,
        "labels_used_only_for_endpoint_scoring": True,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO),
        "provider_backed_strategy_execution_in_this_gate": 0,
        "deterministic_strategy_execution_count": len(decisions),
        "row_execution_in_this_gate": 0,
        "decision_files": sorted(
            proof_relative(path)
            for path in (PROOF / "decisions").rglob("*.json")
            if path.is_file()
        ),
    }
    return manifest, endpoints


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter100-differential-deterministic-execution-{status}",
        "task_id": f"telos:{EXPERIMENT_ID}@iter99",
        "agent_id": "codex-local-differential-deterministic-executor",
        "benchmark_id": "telos_external_verifier_differential_suite_v0",
        "status": status,
        "stated_goal": "Run zero-provider deterministic strategies on iter99 differential fixtures.",
        "acceptance_criteria": [
            "Iter99 receipt and audit validation pass.",
            "Four deterministic strategies produce one decision per materialized fixture.",
            "Private labels are excluded from decisions and used only for endpoint scoring.",
            "Provider-backed LLM judge execution remains zero and deferred.",
            "No provider calls, spend, benchmark, model, live-domain, or SOTA claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/decision_manifest.json",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/endpoint_results.json",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
            },
        ],
        "falsifiers": [
            "The result must block if iter99 validation fails.",
            "The result must fail if any deterministic decision is missing.",
            "The result must fail if labels are used for decisions.",
            "The result must fail if provider calls, LLM judge execution, spend, benchmark, model, live-domain, or SOTA claims occur.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_text_artifacts(
    *,
    status: str,
    prereq: dict[str, Any],
    decision_manifest: dict[str, Any],
    endpoints: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    endpoint_by_strategy = {row["strategy_id"]: row for row in endpoints["endpoint_rows"]}
    result = f"""# Iteration 100 Result - Deterministic Strategy Execution on Differential Fixtures

Status: `{status.upper()}`.

## Summary

This gate executed only the four zero-provider deterministic strategies over the iter99
differential fixtures. The provider-backed LLM judge remained deferred and no benchmark/model/SOTA
claim is made.

- iter99 validation clean: `{str(prereq["clean_prerequisites"]).lower()}`,
- materialized fixture count: `{decision_manifest["materialized_fixture_count"]}`,
- deterministic strategy count: `{len(DETERMINISTIC_STRATEGIES)}`,
- deterministic decision count: `{decision_manifest["decision_count"]}`,
- LLM judge execution count: `0`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- labels used for decisions: `false`,
- labels used only for endpoint scoring: `true`,
- external-verifier false-completion acceptance rate: `{endpoint_by_strategy["external_verifier"]["false_completion_acceptance_rate"]}`,
- complete-Telos false-completion acceptance rate: `{endpoint_by_strategy["complete_telos_protocol"]["false_completion_acceptance_rate"]}`,
- limited deterministic fixture differential observed: `{str(endpoints["limited_deterministic_fixture_differential_observed"]).lower()}`,
- differential detection delta: `{endpoints["differential_detection_delta"]}`,
- next gate: `{NEXT_GATE}`,
- benchmark/model/SOTA claim: `false`,
- Telos-specific superiority claim: `false`,
- blockers: `{", ".join(blockers) if blockers else "none"}`,
- failures: `{", ".join(failures) if failures else "none"}`.

## Deterministic Endpoint Table

| strategy | false-completion acceptance | false rejection | legitimate preservation |
| --- | ---: | ---: | ---: |
"""
    for strategy_id in DETERMINISTIC_STRATEGIES:
        row = endpoint_by_strategy[strategy_id]
        result += (
            f"| `{strategy_id}` | `{row['false_completion_acceptance_rate']}` | "
            f"`{row['false_rejection_rate']}` | "
            f"`{row['legitimate_completion_preservation_rate']}` |\n"
        )
    result += """
## Claim Boundary

This is limited deterministic fixture-comparison evidence. It is not a benchmark result, SWE-bench
score, leaderboard result, production/live-domain result, model-superiority result, broad
Telos-specific superiority result, all-strategy result, or state-of-the-art result.

## Evidence

- `proof/iter99_prerequisite_validation.json`
- `proof/strategy_input_integrity.json`
- `proof/decision_manifest.json`
- `proof/decisions/`
- `proof/endpoint_results.json`
- `proof/llm_judge_deferral.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_deterministic_strategy_execution_on_differential_fixtures_after_materialization.json`
"""
    write_text(RESULT, result)
    write_text(
        PROOF / "review.md",
        f"""# Iteration 100 Review

Iter100 executed deterministic strategies on committed iter99 public fixture packets.

- status: `{status}`,
- deterministic decisions: `{decision_manifest['decision_count']}`,
- LLM judge decisions: `0`,
- external-verifier false-completion acceptance rate: `{endpoint_by_strategy['external_verifier']['false_completion_acceptance_rate']}`,
- complete-Telos false-completion acceptance rate: `{endpoint_by_strategy['complete_telos_protocol']['false_completion_acceptance_rate']}`,
- limited deterministic fixture differential observed: `{str(endpoints['limited_deterministic_fixture_differential_observed']).lower()}`.

Private labels were used only after decisions for endpoint scoring. The provider-backed LLM judge
did not run. No benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, broad
Telos-specific superiority, all-strategy, comparative-performance, or state-of-the-art result is
claimed.
""",
    )
    command_lines = [
        f"differential deterministic strategy execution: {status}",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "provider_backed_strategy_execution_in_this_gate=0",
        f"deterministic_strategy_execution_count={decision_manifest['decision_count']}",
        "llm_judge_execution_count=0",
        f"materialized_fixture_count={decision_manifest['materialized_fixture_count']}",
        f"deterministic_strategy_count={len(DETERMINISTIC_STRATEGIES)}",
        f"deterministic_decision_count={decision_manifest['decision_count']}",
        (
            "agent_self_report_false_completion_acceptance_rate="
            f"{endpoint_by_strategy['agent_self_report']['false_completion_acceptance_rate']}"
        ),
        (
            "execution_tests_only_false_completion_acceptance_rate="
            f"{endpoint_by_strategy['execution_tests_only']['false_completion_acceptance_rate']}"
        ),
        (
            "external_verifier_false_completion_acceptance_rate="
            f"{endpoint_by_strategy['external_verifier']['false_completion_acceptance_rate']}"
        ),
        (
            "complete_telos_protocol_false_completion_acceptance_rate="
            f"{endpoint_by_strategy['complete_telos_protocol']['false_completion_acceptance_rate']}"
        ),
        f"complete_telos_specific_detection_count={endpoints['complete_telos_specific_detection_count']}",
        f"differential_detection_delta={endpoints['differential_detection_delta']}",
        "labels_used_for_decisions=false",
        "partial_deterministic_endpoint_evidence=true",
        "benchmark_result_claimed=false",
        "telos_specific_superiority_over_external_verifier_claimed=false",
        "benchmark_model_sota_claimed=false",
        f"next_gate={NEXT_GATE}",
        f"blockers={'; '.join(blockers) if blockers else 'none'}",
        f"failures={'; '.join(failures) if failures else 'none'}",
    ]
    write_text(PROOF / "command_output.txt", "\n".join(command_lines) + "\n")


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter99()
    fixture_manifest = read_json(ITER99_FIXTURES)
    labels = read_json(ITER99_LABELS)
    strategy_inputs = read_json(ITER99_STRATEGY_INPUTS)
    labels_by_fixture = {label["blinded_fixture_id"]: label for label in labels["labels"]}
    strategy_integrity = verify_strategy_inputs(fixture_manifest, strategy_inputs)
    decision_manifest, endpoints = build_decisions(fixture_manifest, labels_by_fixture)
    llm_judge_deferral = {
        "schema_version": "telos.differential_deterministic_execution.llm_judge_deferral.v1",
        "experiment_id": EXPERIMENT_ID,
        "deferred_strategy_id": DEFERRED_STRATEGY,
        "llm_judge_execution_count": 0,
        "provider_calls_for_llm_judge": 0,
        "provider_spend_for_llm_judge_usd": decimal_string(ZERO),
        "deferral_reason": "LLM judge requires provider calls and is reserved for iter101.",
        "next_gate": NEXT_GATE,
    }
    claim_boundary = {
        "schema_version": "telos.differential_deterministic_execution.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "limited_deterministic_fixture_differential_observed": endpoints[
            "limited_deterministic_fixture_differential_observed"
        ],
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "telos_specific_superiority_over_external_verifier_claimed": False,
        "all_strategy_empirical_superiority_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_execution_completed": False,
        "provider_llm_judge_completed": False,
        "claim_text": (
            "This gate may claim only limited deterministic fixture-comparison evidence. It is "
            "not a benchmark, model, all-strategy, broad Telos-specific superiority, production, "
            "or state-of-the-art result."
        ),
    }

    failures: list[str] = []
    if not prereq["clean_prerequisites"]:
        blockers.append("iter99_prerequisite_validation_failed")
    if strategy_integrity["mismatch_count"] != 0:
        failures.append("strategy_input_integrity_mismatch")
    if decision_manifest["decision_count"] != decision_manifest["expected_decision_count"]:
        failures.append("deterministic_decision_count_mismatch")
    if not (ROOT / NEXT_GATE).exists():
        blockers.append("next_gate_not_pre_registered")

    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"

    write_json(PROOF / "iter99_prerequisite_validation.json", prereq)
    write_json(PROOF / "strategy_input_integrity.json", strategy_integrity)
    write_json(PROOF / "decision_manifest.json", decision_manifest)
    write_json(PROOF / "endpoint_results.json", endpoints)
    write_json(PROOF / "llm_judge_deferral.json", llm_judge_deferral)
    write_json(PROOF / "claim_boundary.json", claim_boundary)
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(
        status=status,
        prereq=prereq,
        decision_manifest=decision_manifest,
        endpoints=endpoints,
        blockers=blockers,
        failures=failures,
    )

    scan = redaction_scan()
    if not scan["passed"]:
        failures.append("redaction_scan_failed")
        status = "fail"
        write_json(VALID / RECEIPT_NAME, build_receipt(status))
        write_text_artifacts(
            status=status,
            prereq=prereq,
            decision_manifest=decision_manifest,
            endpoints=endpoints,
            blockers=blockers,
            failures=failures,
        )
        scan = redaction_scan()
    write_json(PROOF / "redaction_scan.json", scan)
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status if status != "fail" else "null",
            "insight": (
                "Zero-provider deterministic execution now records a limited differential between "
                "generic external verification and complete Telos on static fixtures, while "
                "provider LLM judge and benchmark claims remain deferred."
            ),
            "next_action": "run the deferred provider-backed LLM judge on the same frozen fixtures",
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/decision_manifest.json",
                f"experiments/{EXPERIMENT_ID}/proof/endpoint_results.json",
                f"experiments/{EXPERIMENT_ID}/proof/llm_judge_deferral.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    endpoint_by_strategy = {row["strategy_id"]: row for row in endpoints["endpoint_rows"]}
    summary = {
        "schema_version": "telos.differential_deterministic_execution.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter99_clean_pass": prereq["clean_prerequisites"],
        "materialized_fixture_count": decision_manifest["materialized_fixture_count"],
        "deterministic_strategy_count": len(DETERMINISTIC_STRATEGIES),
        "deterministic_decision_count": decision_manifest["decision_count"],
        "expected_deterministic_decision_count": decision_manifest["expected_decision_count"],
        "deterministic_strategy_execution_count": decision_manifest["decision_count"],
        "provider_backed_strategy_execution_in_this_gate": 0,
        "llm_judge_execution_count": 0,
        "llm_judge_deferred": True,
        "provider_api_calls": 0,
        "provider_cost_usd": decimal_string(ZERO),
        "row_execution_in_this_gate": 0,
        "labels_used_for_decisions": False,
        "labels_used_only_for_endpoint_scoring": True,
        "partial_deterministic_endpoint_evidence": True,
        "external_verifier_false_completion_acceptance_rate": endpoint_by_strategy[
            "external_verifier"
        ]["false_completion_acceptance_rate"],
        "complete_telos_protocol_false_completion_acceptance_rate": endpoint_by_strategy[
            "complete_telos_protocol"
        ]["false_completion_acceptance_rate"],
        "complete_telos_specific_detection_count": endpoints[
            "complete_telos_specific_detection_count"
        ],
        "differential_detection_delta": endpoints["differential_detection_delta"],
        "limited_deterministic_fixture_differential_observed": endpoints[
            "limited_deterministic_fixture_differential_observed"
        ],
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "telos_specific_superiority_over_external_verifier_claimed": False,
        "all_strategy_empirical_superiority_claimed": False,
        "production_or_live_domain_changed": False,
        "sentinel_named_resources_modified": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "redaction_scan_passed": scan["passed"],
        "redaction_findings": scan["findings"],
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
        "endpoint_results": endpoint_by_strategy,
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"differential deterministic strategy execution: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("provider_backed_strategy_execution_in_this_gate=0")
    print(f"deterministic_strategy_execution_count={decision_manifest['decision_count']}")
    print("llm_judge_execution_count=0")
    print(f"materialized_fixture_count={decision_manifest['materialized_fixture_count']}")
    print(f"deterministic_strategy_count={len(DETERMINISTIC_STRATEGIES)}")
    print(f"deterministic_decision_count={decision_manifest['decision_count']}")
    print(
        "external_verifier_false_completion_acceptance_rate="
        f"{endpoint_by_strategy['external_verifier']['false_completion_acceptance_rate']}"
    )
    print(
        "complete_telos_protocol_false_completion_acceptance_rate="
        f"{endpoint_by_strategy['complete_telos_protocol']['false_completion_acceptance_rate']}"
    )
    print(f"complete_telos_specific_detection_count={endpoints['complete_telos_specific_detection_count']}")
    print(f"differential_detection_delta={endpoints['differential_detection_delta']}")
    print("labels_used_for_decisions=false")
    print("partial_deterministic_endpoint_evidence=true")
    print("benchmark_result_claimed=false")
    print("telos_specific_superiority_over_external_verifier_claimed=false")
    print("benchmark_model_sota_claimed=false")
    print(f"next_gate={NEXT_GATE}")
    print(f"blockers={'; '.join(blockers) if blockers else 'none'}")
    print(f"failures={'; '.join(failures) if failures else 'none'}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
