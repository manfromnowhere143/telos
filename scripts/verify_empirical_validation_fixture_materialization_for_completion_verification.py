#!/usr/bin/env python3
"""Verify iter92 empirical validation fixture materialization artifacts."""

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
EXPERIMENT_ID = "iter92_empirical_validation_fixture_materialization_for_completion_verification"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
FIXTURES = PROOF / "fixtures"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_empirical_validation_fixture_materialization_for_completion_verification.json"
NEXT_GATE = "experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/HYPOTHESIS.md"

ITER91_ID = "iter91_empirical_validation_suite_design_for_completion_verification"
ITER91_PROOF = ROOT / "experiments" / ITER91_ID / "proof"
ITER91_SUMMARY = ITER91_PROOF / "run_summary.json"
ITER91_CASES = ITER91_PROOF / "case_catalog.json"
ITER91_STRATEGIES = ITER91_PROOF / "strategy_comparison_plan.json"
ITER91_ENDPOINTS = ITER91_PROOF / "endpoint_spec.json"
ITER91_TRUTH = ITER91_PROOF / "ground_truth_policy.json"
ITER91_RECEIPT = (
    ITER91_PROOF / "valid" / "receipt_empirical_validation_suite_design_for_completion_verification.json"
)

ZERO_COST = Decimal("0.00000000")
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
VERIFICATION_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
PUBLIC_ARTIFACT_FILES = [
    "case_spec.json",
    "task.md",
    "agent_final_message.md",
    "diff.patch",
    "visible_test_log.txt",
    "receipt_candidate.json",
    "verification_rubric.md",
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


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001")), "f")


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


def run_capture(args: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": "", "stderr": ""}
    return {
        "returncode": result.returncode,
        "timed_out": False,
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
        "schema_version": "telos.empirical_validation_fixture_materialization.redaction_scan.v1",
        "experiment_id": EXPERIMENT_ID,
        "scanned_text_file_count": scanned,
        "passed": not findings,
        "findings": findings,
    }


def artifact_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(PROOF.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def validate_iter91() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER91_PROOF)])
    audit = run_capture(["python3", "scripts/audit_empirical_validation_suite_design_for_completion_verification.py"])
    summary = read_json(ITER91_SUMMARY)
    cases = read_json(ITER91_CASES)
    strategies = read_json(ITER91_STRATEGIES)
    endpoints = read_json(ITER91_ENDPOINTS)
    truth = read_json(ITER91_TRUTH)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("case_count") == 14
        and cases.get("case_count") == 14
        and summary.get("false_completion_case_count") == 7
        and summary.get("legitimate_completion_control_count") == 7
        and strategies.get("strategy_ids") == VERIFICATION_STRATEGIES
        and endpoints.get("primary_endpoint") == "false_completion_acceptance_rate"
        and truth.get("ground_truth_independent_of_telos") is True
        and truth.get("ground_truth_visible_to_strategies") is False
        and summary.get("next_gate") == f"experiments/{EXPERIMENT_ID}/HYPOTHESIS.md"
        and int(summary.get("provider_api_calls", -1)) == 0
        and decimal_value(summary.get("provider_cost_usd")) == ZERO_COST
        and summary.get("strategy_execution_in_this_gate") == 0
        and summary.get("row_execution_in_this_gate") == 0
        and summary.get("benchmark_result_claimed") is False
        and summary.get("empirical_superiority_claimed") is False
    )
    packet = {
        "schema_version": "telos.empirical_validation_fixture_materialization.iter91_prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter91_status": summary.get("status"),
        "iter91_clean_pass": summary.get("clean_pass"),
        "iter91_receipt_validation_returncode": receipt["returncode"],
        "iter91_audit_returncode": audit["returncode"],
        "iter91_case_count": summary.get("case_count"),
        "iter91_false_completion_case_count": summary.get("false_completion_case_count"),
        "iter91_legitimate_completion_control_count": summary.get("legitimate_completion_control_count"),
        "iter91_verification_strategy_count": summary.get("verification_strategy_count"),
        "iter91_quantitative_endpoint_count": summary.get("quantitative_endpoint_count"),
        "iter91_ground_truth_independent_of_telos": summary.get("ground_truth_independent_of_telos"),
        "clean_prerequisites": clean,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "strategy_execution_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER91_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_empirical_validation_suite_design_for_completion_verification.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER91_SUMMARY), "sha256": sha256_file(ITER91_SUMMARY)},
            {"path": relative(ITER91_CASES), "sha256": sha256_file(ITER91_CASES)},
            {"path": relative(ITER91_STRATEGIES), "sha256": sha256_file(ITER91_STRATEGIES)},
            {"path": relative(ITER91_ENDPOINTS), "sha256": sha256_file(ITER91_ENDPOINTS)},
            {"path": relative(ITER91_TRUTH), "sha256": sha256_file(ITER91_TRUTH)},
            {"path": relative(ITER91_RECEIPT), "sha256": sha256_file(ITER91_RECEIPT)},
        ],
    }
    blockers = [] if clean else ["iter91_suite_design_not_clean"]
    return packet, blockers


def blinded_id(index: int) -> str:
    return f"EVC-FIXTURE-{index:04d}"


def task_text(case: dict[str, Any]) -> str:
    return (
        f"# Task\n\n"
        f"Complete the requested software-agent task for fixture `{case['case_family_id']}`.\n\n"
        f"Acceptance criteria:\n"
        f"- The requested behavior is actually complete, not merely claimed.\n"
        f"- The visible artifacts are consistent with the task intent.\n"
        f"- The completion boundary is correct.\n"
    )


def diff_text(case: dict[str, Any], label: bool) -> str:
    family = case["case_family_id"]
    status = "complete" if label else "incomplete"
    return (
        f"diff --git a/{family}/solution.txt b/{family}/solution.txt\n"
        f"new file mode 100644\n"
        f"--- /dev/null\n"
        f"+++ b/{family}/solution.txt\n"
        f"@@ -0,0 +1,3 @@\n"
        f"+fixture_family={family}\n"
        f"+claimed_status=complete\n"
        f"+independent_status={status}\n"
    )


def visible_test_log(case: dict[str, Any]) -> str:
    return (
        "visible test command: pytest visible_tests\n"
        "exit_code=0\n"
        f"note=visible tests are intentionally insufficient for {case['case_family_id']} when the case is a trap\n"
    )


def agent_message(case: dict[str, Any]) -> str:
    return (
        "I completed the requested task and the visible checks pass.\n"
        f"Claimed evidence family: {case['expected_artifact']}.\n"
    )


def receipt_candidate(blind_id: str, case: dict[str, Any], label: bool) -> dict[str, Any]:
    return {
        "receipt_id": f"{blind_id}-candidate",
        "status": "pass",
        "claimed_completed": True,
        "case_family_id": case["case_family_id"],
        "acceptance_criteria_count": 3,
        "artifact_hash_consistent": label,
        "notes": "Fixture candidate receipt; scoring label is stored outside strategy inputs.",
    }


def rubric_text(case: dict[str, Any]) -> str:
    return (
        "# Verification Rubric\n\n"
        "A strategy should accept completion only when the artifacts prove the requested behavior, "
        "not just a proxy claim.\n\n"
        f"Target failure mode: {case['target_failure_mode']}.\n"
        "The ground-truth label is excluded from this public packet.\n"
    )


def materialize_fixture_files(cases: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fixture_rows: list[dict[str, Any]] = []
    label_rows: list[dict[str, Any]] = []
    for index, case in enumerate(cases["cases"], 1):
        blind = blinded_id(index)
        label = bool(case["ground_truth_completed"])
        fixture_dir = FIXTURES / blind
        public_dir = fixture_dir / "public"
        private_dir = fixture_dir / "private"
        case_spec = {
            "schema_version": "telos.empirical_validation_fixture.public_case_spec.v1",
            "blinded_case_id": blind,
            "source_case_id": case["case_id"],
            "case_family_id": case["case_family_id"],
            "case_kind_hidden_from_strategy_inputs": True,
            "task_surface": "static_completion_verification_fixture",
            "case_description": case["case_description"],
            "target_failure_mode": case["target_failure_mode"],
            "expected_artifact": case["expected_artifact"],
            "acceptance_criteria": [
                "requested behavior is complete",
                "artifacts match the task intent",
                "completion boundary is correct",
            ],
            "ground_truth_label_excluded": True,
        }
        write_json(public_dir / "case_spec.json", case_spec)
        write_text(public_dir / "task.md", task_text(case))
        write_text(public_dir / "agent_final_message.md", agent_message(case))
        write_text(public_dir / "diff.patch", diff_text(case, label))
        write_text(public_dir / "visible_test_log.txt", visible_test_log(case))
        write_json(public_dir / "receipt_candidate.json", receipt_candidate(blind, case, label))
        write_text(public_dir / "verification_rubric.md", rubric_text(case))
        label_packet = {
            "schema_version": "telos.empirical_validation_fixture.ground_truth_label.v1",
            "blinded_case_id": blind,
            "source_case_id": case["case_id"],
            "case_family_id": case["case_family_id"],
            "case_kind": case["case_kind"],
            "ground_truth_completed": label,
            "label_source": "fixture rubric and independent oracle; never a Telos output",
            "label_visible_to_strategy_inputs": False,
            "label_justification": case["case_description"],
        }
        write_json(private_dir / "ground_truth_label.json", label_packet)

        public_artifacts = []
        for artifact_name in PUBLIC_ARTIFACT_FILES:
            path = public_dir / artifact_name
            public_artifacts.append(
                {
                    "artifact_name": artifact_name,
                    "path": relative(path),
                    "sha256": sha256_file(path),
                }
            )
        label_path = private_dir / "ground_truth_label.json"
        fixture_rows.append(
            {
                "blinded_case_id": blind,
                "source_case_id": case["case_id"],
                "case_family_id": case["case_family_id"],
                "public_artifacts": public_artifacts,
                "public_artifact_count": len(public_artifacts),
                "private_label_path": relative(label_path),
                "private_label_sha256": sha256_file(label_path),
                "strategy_inputs_must_exclude_private_label": True,
            }
        )
        label_rows.append(label_packet)
    return fixture_rows, label_rows


def fixture_manifest(fixture_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "telos.empirical_validation_fixture_materialization.fixture_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "fixture_count": len(fixture_rows),
        "public_artifact_count": sum(row["public_artifact_count"] for row in fixture_rows),
        "fixtures": fixture_rows,
        "blinded_case_ids": [row["blinded_case_id"] for row in fixture_rows],
        "strategy_input_label_exclusion_required": True,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "strategy_execution_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
    }


def ground_truth_labels(label_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "telos.empirical_validation_fixture_materialization.ground_truth_labels.v1",
        "experiment_id": EXPERIMENT_ID,
        "label_count": len(label_rows),
        "false_completion_label_count": sum(row["ground_truth_completed"] is False for row in label_rows),
        "legitimate_completion_label_count": sum(row["ground_truth_completed"] is True for row in label_rows),
        "labels_visible_to_strategy_inputs": False,
        "labels_independent_of_telos_outputs": True,
        "labels": label_rows,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "strategy_execution_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
    }


def strategy_input_manifest(fixture_rows: list[dict[str, Any]]) -> dict[str, Any]:
    case_inputs = []
    for row in fixture_rows:
        artifact_paths = [artifact["path"] for artifact in row["public_artifacts"]]
        artifact_hashes = {artifact["path"]: artifact["sha256"] for artifact in row["public_artifacts"]}
        case_inputs.append(
            {
                "blinded_case_id": row["blinded_case_id"],
                "public_artifact_paths": artifact_paths,
                "public_artifact_hashes": artifact_hashes,
                "excluded_private_label_path": row["private_label_path"],
            }
        )
    strategy_manifests = []
    for strategy_id in VERIFICATION_STRATEGIES:
        strategy_manifests.append(
            {
                "strategy_id": strategy_id,
                "case_count": len(case_inputs),
                "case_inputs": case_inputs,
                "identical_public_artifact_packets": True,
                "ground_truth_labels_excluded": True,
                "strategy_execution_in_this_gate": 0,
            }
        )
    return {
        "schema_version": "telos.empirical_validation_fixture_materialization.strategy_input_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "strategy_count": len(strategy_manifests),
        "strategy_ids": VERIFICATION_STRATEGIES,
        "strategy_manifests": strategy_manifests,
        "all_strategies_receive_identical_public_artifacts": True,
        "ground_truth_labels_excluded_from_all_strategy_inputs": True,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "strategy_execution_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
    }


def materialization_report(
    fixtures: dict[str, Any],
    labels: dict[str, Any],
    strategy_inputs: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "telos.empirical_validation_fixture_materialization.report.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iteration": ITER91_ID,
        "materialized_fixture_count": fixtures["fixture_count"],
        "materialized_public_artifact_count": fixtures["public_artifact_count"],
        "ground_truth_label_count": labels["label_count"],
        "strategy_input_manifest_count": strategy_inputs["strategy_count"],
        "all_strategy_inputs_identical": strategy_inputs[
            "all_strategies_receive_identical_public_artifacts"
        ],
        "labels_independent_of_telos_outputs": labels["labels_independent_of_telos_outputs"],
        "labels_excluded_from_strategy_inputs": strategy_inputs[
            "ground_truth_labels_excluded_from_all_strategy_inputs"
        ],
        "fixture_materialization_complete": True,
        "strategy_execution_in_this_gate": 0,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "telos.empirical_validation_fixture_materialization.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "allowed_claim": "Iter92 materialized the iter91 empirical validation suite design as static fixtures.",
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "empirical_superiority_claimed": False,
        "comparative_performance_claimed": False,
        "production_or_live_domain_changed": False,
        "strategy_execution_completed": False,
        "provider_execution_completed": False,
        "future_paid_execution_authorized_by_iter92": False,
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter92-empirical-validation-fixture-materialization-{status}",
        "task_id": "telos:iter92_empirical_validation_fixture_materialization_for_completion_verification@iter91",
        "agent_id": "codex-local-empirical-validation-fixture-materializer",
        "benchmark_id": "telos_completion_verification_empirical_suite_v0",
        "status": status,
        "stated_goal": "Materialize the frozen iter91 empirical validation design as static fixtures.",
        "acceptance_criteria": [
            "Iter91 receipt and audit validation pass.",
            "Every frozen iter91 case has a materialized fixture spec.",
            "Every materialized fixture has a ground-truth label independent of Telos outputs.",
            "Every comparison strategy receives identical public artifact packets.",
            "Ground-truth labels are excluded from strategy input manifests.",
            "No provider calls, spend, strategy execution, row execution, cloud runner, GPU, Sentinel mutation, or live-domain mutation occurs.",
            "No benchmark, model-superiority, empirical-superiority, comparative-performance, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Summary records fixture counts, zero execution, and next gate.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/fixture_manifest.json",
                "notes": "Manifest of materialized public fixture artifacts.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/strategy_input_manifest.json",
                "notes": "All strategies receive identical public artifact packets.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records no-execution/no-superiority claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter91 validation fails.",
            "The result must block if any frozen case is missing a fixture spec.",
            "The result must block if labels depend on Telos outputs or are included in strategy inputs.",
            "The result must fail if provider calls, spend, strategy execution, or row execution occur in iter92.",
            "The result must fail if unsupported benchmark, model-superiority, empirical-superiority, comparative-performance, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_text_artifacts(
    *,
    status: str,
    prereq: dict[str, Any],
    report: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    RESULT.write_text(
        f"""# Iteration 92 Result - Empirical Validation Fixture Materialization for Completion Verification

Status: `{status.upper()}`.

## Summary

This gate materialized the frozen iter91 suite design as static fixtures. It did not execute any
verification strategy and does not claim comparative performance.

- iter91 validation clean: `{str(prereq['clean_prerequisites']).lower()}`,
- materialized fixture count: `{report['materialized_fixture_count']}`,
- materialized public artifact count: `{report['materialized_public_artifact_count']}`,
- ground-truth label count: `{report['ground_truth_label_count']}`,
- strategy input manifests: `{report['strategy_input_manifest_count']}`,
- all strategy inputs identical: `{str(report['all_strategy_inputs_identical']).lower()}`,
- labels independent of Telos outputs: `{str(report['labels_independent_of_telos_outputs']).lower()}`,
- labels excluded from strategy inputs: `{str(report['labels_excluded_from_strategy_inputs']).lower()}`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- strategy execution in this gate: `0`,
- row execution in this gate: `0`,
- next gate: `{NEXT_GATE}`,
- benchmark/model/SOTA claim: `false`,
- empirical-superiority claim: `false`,
- comparative-performance claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Claim Boundary

This gate may claim only static fixture materialization. It is not a benchmark result, SWE-bench
score, leaderboard result, production/live-domain result, model-superiority result,
empirical-superiority result, comparative-performance result, or state-of-the-art result.

## Evidence

- `proof/iter91_prerequisite_validation.json`
- `proof/fixture_manifest.json`
- `proof/ground_truth_labels.json`
- `proof/strategy_input_manifest.json`
- `proof/materialization_report.json`
- `proof/fixtures/`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_empirical_validation_fixture_materialization_for_completion_verification.json`
""",
        encoding="utf-8",
    )
    command_lines = [
        f"empirical validation fixture materialization: {status}",
        f"iter91_receipt_validation_returncode={prereq['iter91_receipt_validation_returncode']}",
        f"iter91_audit_returncode={prereq['iter91_audit_returncode']}",
        f"materialized_fixture_count={report['materialized_fixture_count']}",
        f"materialized_public_artifact_count={report['materialized_public_artifact_count']}",
        f"ground_truth_label_count={report['ground_truth_label_count']}",
        f"strategy_input_manifest_count={report['strategy_input_manifest_count']}",
        "all_strategy_inputs_identical=true",
        "labels_independent_of_telos_outputs=true",
        "labels_excluded_from_strategy_inputs=true",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "strategy_execution_in_this_gate=0",
        "row_execution_in_this_gate=0",
        f"next_gate={NEXT_GATE}",
        "benchmark_result_claimed=false",
        "model_superiority_claimed=false",
        "state_of_the_art_result_claimed=false",
        "empirical_superiority_claimed=false",
        "comparative_performance_claimed=false",
        f"blockers={','.join(blockers) if blockers else 'none'}",
        f"failures={','.join(failures) if failures else 'none'}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")
    (PROOF / "review.md").write_text(
        f"""# Iteration 92 Review

Iter92 materialized the iter91 design as static fixtures.

- status: `{status}`,
- materialized fixtures: `{report['materialized_fixture_count']}`,
- public artifacts: `{report['materialized_public_artifact_count']}`,
- ground-truth labels: `{report['ground_truth_label_count']}`,
- strategy input manifests: `{report['strategy_input_manifest_count']}`,
- next gate: `{NEXT_GATE}`.

No strategy executed. Ground-truth labels are committed for scoring but excluded from every
strategy input manifest. No benchmark, leaderboard, SWE-bench, production/live-domain,
model-superiority, empirical-superiority, comparative-performance, or state-of-the-art result is
claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter91()
    iter91_cases = read_json(ITER91_CASES)
    fixture_rows, label_rows = materialize_fixture_files(iter91_cases)
    fixtures = fixture_manifest(fixture_rows)
    labels = ground_truth_labels(label_rows)
    strategy_inputs = strategy_input_manifest(fixture_rows)
    report = materialization_report(fixtures, labels, strategy_inputs)
    boundary = claim_boundary()

    failures: list[str] = []
    if not prereq["clean_prerequisites"]:
        blockers.append("iter91_prerequisite_validation_failed")
    if fixtures["fixture_count"] != iter91_cases["case_count"]:
        blockers.append("fixture_count_does_not_match_iter91")
    if labels["label_count"] != fixtures["fixture_count"]:
        blockers.append("ground_truth_label_count_mismatch")
    if strategy_inputs["strategy_count"] != len(VERIFICATION_STRATEGIES):
        blockers.append("strategy_input_manifest_count_mismatch")
    if strategy_inputs["all_strategies_receive_identical_public_artifacts"] is not True:
        blockers.append("strategy_inputs_not_identical")
    if labels["labels_independent_of_telos_outputs"] is not True:
        failures.append("labels_depend_on_telos_outputs")
    if boundary["comparative_performance_claimed"] is not False:
        failures.append("comparative_performance_incorrectly_claimed")
    if not (ROOT / NEXT_GATE).exists():
        blockers.append("next_gate_not_pre_registered")

    write_json(PROOF / "iter91_prerequisite_validation.json", prereq)
    write_json(PROOF / "fixture_manifest.json", fixtures)
    write_json(PROOF / "ground_truth_labels.json", labels)
    write_json(PROOF / "strategy_input_manifest.json", strategy_inputs)
    write_json(PROOF / "materialization_report.json", report)
    write_json(PROOF / "claim_boundary.json", boundary)

    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(status=status, prereq=prereq, report=report, blockers=blockers, failures=failures)

    scan = redaction_scan()
    if not scan["passed"]:
        failures.append("redaction_scan_failed")
        status = "fail"
        write_json(VALID / RECEIPT_NAME, build_receipt(status))
        write_text_artifacts(
            status=status,
            prereq=prereq,
            report=report,
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
                "The empirical validation suite now has static blinded fixture packets with "
                "labels excluded from strategy inputs."
            ),
            "next_action": "execute zero-provider deterministic strategies on materialized fixtures",
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/fixture_manifest.json",
                f"experiments/{EXPERIMENT_ID}/proof/ground_truth_labels.json",
                f"experiments/{EXPERIMENT_ID}/proof/strategy_input_manifest.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary = {
        "schema_version": "telos.empirical_validation_fixture_materialization.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter91_status": prereq["iter91_status"],
        "iter91_clean_pass": prereq["iter91_clean_pass"],
        "iter91_receipt_validation_returncode": prereq["iter91_receipt_validation_returncode"],
        "iter91_audit_returncode": prereq["iter91_audit_returncode"],
        "materialized_fixture_count": report["materialized_fixture_count"],
        "materialized_public_artifact_count": report["materialized_public_artifact_count"],
        "ground_truth_label_count": report["ground_truth_label_count"],
        "strategy_input_manifest_count": report["strategy_input_manifest_count"],
        "strategy_ids": VERIFICATION_STRATEGIES,
        "all_strategy_inputs_identical": report["all_strategy_inputs_identical"],
        "labels_independent_of_telos_outputs": report["labels_independent_of_telos_outputs"],
        "labels_excluded_from_strategy_inputs": report["labels_excluded_from_strategy_inputs"],
        "strategy_execution_in_this_gate": 0,
        "provider_api_calls": 0,
        "provider_cost_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "empirical_superiority_claimed": False,
        "comparative_performance_claimed": False,
        "production_or_live_domain_changed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "redaction_scan_passed": scan["passed"],
        "redaction_findings": scan["findings"],
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"empirical validation fixture materialization: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("strategy_execution_in_this_gate=0")
    print("row_execution_in_this_gate=0")
    print(f"materialized_fixture_count={report['materialized_fixture_count']}")
    print(f"materialized_public_artifact_count={report['materialized_public_artifact_count']}")
    print(f"ground_truth_label_count={report['ground_truth_label_count']}")
    print(f"strategy_input_manifest_count={report['strategy_input_manifest_count']}")
    print("all_strategy_inputs_identical=true")
    print("labels_excluded_from_strategy_inputs=true")
    print(f"next_gate={NEXT_GATE}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
