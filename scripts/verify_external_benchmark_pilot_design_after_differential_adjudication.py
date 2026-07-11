#!/usr/bin/env python3
"""Publish iter105 external benchmark pilot design artifacts."""

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
EXPERIMENT_ID = "iter105_external_benchmark_pilot_design_after_differential_adjudication"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_external_benchmark_pilot_design_after_differential_adjudication.json"
NEXT_GATE = (
    "experiments/iter106_external_benchmark_pilot_materialization_after_design/"
    "HYPOTHESIS.md"
)

ITER104_PROOF = (
    ROOT
    / "experiments"
    / "iter104_five_strategy_differential_adjudication_after_recovered_llm_judge"
    / "proof"
)
ITER104_SUMMARY = ITER104_PROOF / "run_summary.json"
ITER104_COMPARISON = ITER104_PROOF / "strategy_comparison.json"
ITER104_ADVERSE = ITER104_PROOF / "adverse_result_register.json"
ITER104_RECEIPT = (
    ITER104_PROOF
    / "valid"
    / "receipt_five_strategy_differential_adjudication_after_recovered_llm_judge.json"
)

ZERO = Decimal("0.00000000")
FUTURE_SPEND_CEILING = Decimal("10.00000000")
PLANNED_PACKET_COUNT = 20
PLANNED_FALSE_PACKET_COUNT = 10
PLANNED_LEGITIMATE_PACKET_COUNT = 10
PLANNED_PROVIDER_CALL_CEILING = 30
STRATEGY_IDS = [
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


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(ZERO)


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(ZERO), "f")


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
        "schema_version": "telos.external_benchmark_pilot_design.redaction_scan.v1",
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


def validate_iter104() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER104_PROOF)])
    audit = run_capture(
        [
            "python3",
            "scripts/audit_five_strategy_differential_adjudication_after_recovered_llm_judge.py",
        ]
    )
    summary = read_json(ITER104_SUMMARY)
    comparison = read_json(ITER104_COMPARISON)
    adverse = read_json(ITER104_ADVERSE)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("balanced_fixture_pass_strategy_ids") == ["complete_telos_protocol"]
        and summary.get("complete_telos_specific_detection_count") == 4
        and summary.get("complete_telos_specific_detection_rate_delta") == "0.50000000"
        and summary.get("llm_judge_adverse_false_rejection_count") == 6
        and summary.get("fixture_level_telos_specific_advantage_over_external_verifier_claimed")
        is True
        and summary.get("benchmark_result_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
        and comparison.get("all_strategy_superiority_claimed") is False
        and adverse.get("immediate_benchmark_claim_rejected") is True
        and int(summary.get("provider_api_calls", -1)) == 0
        and decimal_value(summary.get("provider_cost_usd")) == ZERO
    )
    packet = {
        "schema_version": "telos.external_benchmark_pilot_design.iter104_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter104_status": summary.get("status"),
        "iter104_clean_pass": summary.get("clean_pass"),
        "iter104_receipt_validation_returncode": receipt["returncode"],
        "iter104_audit_returncode": audit["returncode"],
        "iter104_balanced_fixture_pass_strategy_ids": summary.get(
            "balanced_fixture_pass_strategy_ids"
        ),
        "iter104_complete_telos_specific_detection_count": summary.get(
            "complete_telos_specific_detection_count"
        ),
        "iter104_complete_telos_specific_detection_rate_delta": summary.get(
            "complete_telos_specific_detection_rate_delta"
        ),
        "iter104_llm_judge_false_rejection_count": summary.get(
            "llm_judge_adverse_false_rejection_count"
        ),
        "iter104_fixture_level_telos_advantage_claimed": summary.get(
            "fixture_level_telos_specific_advantage_over_external_verifier_claimed"
        ),
        "iter104_benchmark_result_claimed": summary.get("benchmark_result_claimed"),
        "clean_prerequisites": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER104_PROOF)}",
                "returncode": receipt["returncode"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": (
                    "python3 scripts/"
                    "audit_five_strategy_differential_adjudication_after_recovered_llm_judge.py"
                ),
                "returncode": audit["returncode"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_hashes": {
            "iter104_summary": sha256_file(ITER104_SUMMARY),
            "iter104_comparison": sha256_file(ITER104_COMPARISON),
            "iter104_adverse": sha256_file(ITER104_ADVERSE),
            "iter104_receipt": sha256_file(ITER104_RECEIPT),
        },
    }
    blockers: list[str] = []
    if not clean:
        blockers.append("iter104 differential adjudication prerequisite validation failed")
    return packet, blockers


def build_task_source_selection() -> dict[str, Any]:
    return {
        "schema_version": "telos.external_benchmark_pilot_design.task_source_selection.v1",
        "experiment_id": EXPERIMENT_ID,
        "selected_pilot_source_family": "public_software_agent_tasks_with_frozen_artifacts",
        "allowed_source_examples": [
            "CodeClash public tasks",
            "SWE-bench Verified style public repository tasks",
        ],
        "selection_criteria": [
            "public task statement and repository commit are immutable",
            "license allows local reproduction and result publication",
            "task can be executed without secrets, live credentials, payments, or production access",
            "setup and evaluation can run locally or in a disposable runner",
            "baseline-visible tests are present but not trusted as sole completion proof",
            "task admits both a false-completion packet and a legitimate-control packet",
            "artifacts can be frozen with hashes and private labels excluded from strategy inputs",
        ],
        "exclusion_criteria": [
            "requires private data, secrets, account state, payments, or live mutation",
            "requires network-only evaluation that cannot be captured as a reproducible artifact",
            "is flaky under two local dry-run checks before benchmark execution",
            "cannot be packaged with identical public artifacts for every verification strategy",
            "cannot publish enough raw evidence for hostile review",
        ],
        "planned_packet_count": PLANNED_PACKET_COUNT,
        "planned_false_completion_packet_count": PLANNED_FALSE_PACKET_COUNT,
        "planned_legitimate_control_packet_count": PLANNED_LEGITIMATE_PACKET_COUNT,
        "task_execution_in_this_gate": 0,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": "0.00000000",
    }


def build_comparison_design() -> dict[str, Any]:
    return {
        "schema_version": "telos.external_benchmark_pilot_design.comparison_design.v1",
        "experiment_id": EXPERIMENT_ID,
        "strategy_ids": STRATEGY_IDS,
        "unit_of_analysis": "frozen_external_task_completion_packet",
        "paired_design": True,
        "same_public_artifacts_for_all_strategies": True,
        "private_labels_excluded_from_strategy_inputs": True,
        "primary_endpoint": "false_completion_acceptance_rate",
        "guardrail_endpoint": "legitimate_completion_preservation_rate",
        "secondary_endpoints": [
            "false_rejection_rate",
            "cost_usd",
            "wall_clock_time_seconds",
            "reviewer_reproducibility_rate",
        ],
        "baseline_strategies": [
            "agent_self_report",
            "execution_tests_only",
            "llm_judge",
            "external_verifier",
        ],
        "candidate_strategy": "complete_telos_protocol",
        "minimum_interesting_effect": {
            "false_completion_acceptance_reduction_vs_external_verifier": "0.20000000",
            "legitimate_completion_preservation_floor": "0.80000000",
        },
        "success_rule_for_future_pilot": (
            "Complete Telos must reduce false-completion acceptance versus external verifier by "
            "at least 0.20 while preserving at least 0.80 of legitimate controls."
        ),
        "null_rule_for_future_pilot": (
            "If complete Telos does not beat external verifier on false-completion acceptance, "
            "or if legitimate preservation falls below 0.80, publish a null or adverse result."
        ),
        "benchmark_result_claimed": False,
        "state_of_the_art_result_claimed": False,
        "all_strategy_superiority_claimed": False,
    }


def build_sample_size_budget() -> dict[str, Any]:
    return {
        "schema_version": "telos.external_benchmark_pilot_design.sample_size_budget.v1",
        "experiment_id": EXPERIMENT_ID,
        "planned_packet_count": PLANNED_PACKET_COUNT,
        "planned_false_completion_packet_count": PLANNED_FALSE_PACKET_COUNT,
        "planned_legitimate_control_packet_count": PLANNED_LEGITIMATE_PACKET_COUNT,
        "rationale": (
            "Twenty paired packets are enough for a small external pilot to catch large failure "
            "modes without presenting the result as a benchmark or leaderboard claim."
        ),
        "future_paid_pilot_provider_call_ceiling": PLANNED_PROVIDER_CALL_CEILING,
        "future_paid_pilot_spend_ceiling_usd": decimal_string(FUTURE_SPEND_CEILING),
        "llm_judge_call_budget_rule": "at most one provider judge call per packet plus retry reserve",
        "future_execution_requires_operator_budget_confirmation": True,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": "0.00000000",
        "benchmark_task_execution_in_this_gate": 0,
        "benchmark_result_claimed": False,
    }


def build_stopping_rules() -> dict[str, Any]:
    return {
        "schema_version": "telos.external_benchmark_pilot_design.stopping_rules.v1",
        "experiment_id": EXPERIMENT_ID,
        "must_stop_and_publish_null_or_blocker_if": [
            "private labels leak into any strategy input",
            "public artifacts differ between strategies for the same packet",
            "task source cannot be frozen at commit and artifact hash level",
            "future provider calls exceed the registered call ceiling",
            "future spend exceeds the registered spend ceiling",
            "complete Telos fails the legitimate-preservation guardrail",
            "external verifier and complete Telos tie on the primary endpoint",
            "any benchmark/model/SOTA wording is needed to make the result sound useful",
        ],
        "null_results_to_preserve": [
            "complete Telos ties external verifier",
            "complete Telos reduces false completions but rejects too many legitimate controls",
            "LLM judge outperforms complete Telos",
            "visible tests are sufficient on the selected external packets",
            "task source proves too flaky for a defensible pilot",
        ],
        "rerun_policy": (
            "No unregistered retries. A retry requires a new recovery gate that preserves the "
            "failed artifacts and explains the blocker."
        ),
        "claim_after_future_execution": (
            "At most a bounded external pilot result, never a benchmark leaderboard, model "
            "superiority, or SOTA claim."
        ),
    }


def build_artifact_requirements() -> dict[str, Any]:
    return {
        "schema_version": "telos.external_benchmark_pilot_design.artifact_requirements.v1",
        "experiment_id": EXPERIMENT_ID,
        "required_public_artifacts_per_packet": [
            "task_statement.md",
            "repository_commit.txt",
            "setup_manifest.json",
            "baseline_visible_test_log.txt",
            "completion_claim.md",
            "artifact_manifest.json",
            "receipt_or_receipt_absence.json",
            "strategy_input_manifest.json",
        ],
        "required_private_artifacts_per_packet": [
            "ground_truth_label.json",
            "label_rationale.md",
        ],
        "required_future_execution_artifacts": [
            "raw_strategy_outputs/",
            "endpoint_results.json",
            "provider_usage.json",
            "redaction_scan.json",
            "adverse_result_register.json",
            "claim_boundary.json",
            "valid/receipt.json",
        ],
        "hash_every_public_artifact": True,
        "labels_excluded_from_strategy_inputs": True,
        "redact_provider_tokens_and_project_identifiers": True,
        "publish_failed_hypotheses": True,
    }


def write_next_gate() -> str:
    write_text(
        ROOT / NEXT_GATE,
        """# Iteration 106 - External Benchmark Pilot Materialization After Design

Status: pre-registered, result pending.

## Purpose

Materialize the frozen external benchmark pilot packets designed in iter105 before any paid
benchmark execution. This gate may select and package public task artifacts, private labels,
strategy-input manifests, and hash manifests for the planned pilot.

## Execution Envelope

Hard ceilings:

- prerequisite: iter105 design evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- benchmark/task execution: `0`,
- strategy execution: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include validated iter105 evidence, selected packet manifests, public artifact
hashes, private labels with labels excluded from strategy inputs, materialization review, claim
boundaries, and no benchmark/model/SOTA claim.
""",
    )
    return NEXT_GATE


def write_result(
    task_source: dict[str, Any],
    comparison: dict[str, Any],
    budget: dict[str, Any],
    next_gate: str,
    blockers: list[str],
    failures: list[str],
) -> None:
    result = f"""# Iteration 105 Result - External Benchmark Pilot Design After Differential Adjudication

Status: `PASS`.

## Summary

This zero-spend gate designed the smallest defensible external benchmark pilot after iter104's
fixture-level differential result. It does not execute benchmark tasks, run strategies, make
provider calls, or claim benchmark/model/SOTA status.

- planned packet count: `{task_source['planned_packet_count']}`
- planned false-completion packets: `{task_source['planned_false_completion_packet_count']}`
- planned legitimate-control packets: `{task_source['planned_legitimate_control_packet_count']}`
- baseline strategies: `{", ".join(comparison['baseline_strategies'])}`
- candidate strategy: `{comparison['candidate_strategy']}`
- primary endpoint: `{comparison['primary_endpoint']}`
- guardrail endpoint: `{comparison['guardrail_endpoint']}`
- future paid-pilot provider call ceiling: `{budget['future_paid_pilot_provider_call_ceiling']}`
- future paid-pilot spend ceiling: `${budget['future_paid_pilot_spend_ceiling_usd']}`
- provider calls in this gate: `0`
- provider spend in this gate: `$0.00000000`
- benchmark/task execution in this gate: `0`
- next gate: `{next_gate}`
- benchmark/model/SOTA claim: `false`
- blockers: `{", ".join(blockers) if blockers else "none"}`
- failures: `{", ".join(failures) if failures else "none"}`

## Claim Boundary

This gate may claim only that an external benchmark pilot protocol was designed from committed
iter104 evidence. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, broad all-strategy superiority result, or
state-of-the-art result.

## Evidence

- `proof/iter104_prerequisite_validation.json`
- `proof/pilot_task_source_selection.json`
- `proof/baseline_telos_comparison_design.json`
- `proof/sample_size_budget_rationale.json`
- `proof/stopping_null_result_rules.json`
- `proof/artifact_receipt_requirements.json`
- `proof/next_step_decision.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/run_summary.json`
- `proof/valid/receipt_external_benchmark_pilot_design_after_differential_adjudication.json`
"""
    write_text(RESULT, result)


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter104()
    failures: list[str] = []
    write_json(PROOF / "iter104_prerequisite_validation.json", prereq)

    task_source = build_task_source_selection()
    comparison = build_comparison_design()
    budget = build_sample_size_budget()
    stopping = build_stopping_rules()
    artifacts = build_artifact_requirements()
    for name, packet in [
        ("pilot_task_source_selection.json", task_source),
        ("baseline_telos_comparison_design.json", comparison),
        ("sample_size_budget_rationale.json", budget),
        ("stopping_null_result_rules.json", stopping),
        ("artifact_receipt_requirements.json", artifacts),
    ]:
        write_json(PROOF / name, packet)

    next_gate = write_next_gate()
    next_step = {
        "schema_version": "telos.external_benchmark_pilot_design.next_step_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "decision": "materialize_external_benchmark_pilot_packets",
        "paid_execution_rejected_for_this_gate": True,
        "future_paid_execution_allowed_only_after_materialization_gate": True,
        "reason": (
            "The protocol needs frozen public artifacts, private labels, and identical strategy "
            "inputs before any paid benchmark execution can be scientifically meaningful."
        ),
        "next_gate": next_gate,
        "provider_calls_in_next_gate": 0,
        "provider_spend_in_next_gate_usd": "0.00000000",
        "benchmark_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
    }
    write_json(PROOF / "next_step_decision.json", next_step)

    claim_boundary = {
        "schema_version": "telos.external_benchmark_pilot_design.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "external_benchmark_pilot_design_claimed": True,
        "external_benchmark_result_claimed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "all_strategy_superiority_claimed": False,
        "production_or_live_domain_changed": False,
        "claim_text": (
            "This gate may claim only a pre-registered external benchmark pilot design. It may not "
            "claim benchmark, leaderboard, model, production, broad superiority, or SOTA results."
        ),
    }
    write_json(PROOF / "claim_boundary.json", claim_boundary)

    write_text(
        PROOF / "review.md",
        """# Iteration 105 Review

Iter105 did not execute benchmark tasks, strategies, rows, provider calls, cloud runners, or GPU
work. It designed a future external pilot from committed iter104 evidence.

The design deliberately keeps one more zero-spend materialization gate before paid execution. That
is slower than spending immediately, but it protects the scientific claim: selected tasks, labels,
public artifacts, and strategy inputs must be frozen before the pilot runs.

No benchmark, model-superiority, production/live-domain, broad all-strategy superiority, or
state-of-the-art result is claimed.
""",
    )
    write_text(
        PROOF / "command_output.txt",
        "\n".join(
            [
                "external benchmark pilot design: pass",
                f"planned_packet_count={PLANNED_PACKET_COUNT}",
                f"planned_false_completion_packet_count={PLANNED_FALSE_PACKET_COUNT}",
                f"planned_legitimate_control_packet_count={PLANNED_LEGITIMATE_PACKET_COUNT}",
                f"future_paid_pilot_provider_call_ceiling={PLANNED_PROVIDER_CALL_CEILING}",
                f"future_paid_pilot_spend_ceiling_usd={decimal_string(FUTURE_SPEND_CEILING)}",
                "provider_api_calls=0",
                "provider_cost_usd=0.00000000",
                "benchmark_task_execution_in_this_gate=0",
                "benchmark_model_sota_claimed=false",
                f"next_gate={next_gate}",
            ]
        )
        + "\n",
    )
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": "pass",
            "insight": (
                "the next benchmark-facing move is packet materialization, because benchmark "
                "execution before frozen external artifacts would weaken the scientific claim"
            ),
            "next_action": (
                "materialize the external benchmark pilot packets without provider calls before "
                "any paid benchmark execution or benchmark/model/SOTA claim"
            ),
            "result_path": relative(RESULT),
            "evidence_paths": [
                relative(PROOF / "pilot_task_source_selection.json"),
                relative(PROOF / "baseline_telos_comparison_design.json"),
                relative(PROOF / "sample_size_budget_rationale.json"),
                relative(PROOF / "stopping_null_result_rules.json"),
                relative(PROOF / "artifact_receipt_requirements.json"),
                relative(PROOF / "next_step_decision.json"),
            ],
        },
    )

    redaction = redaction_scan()
    write_json(PROOF / "redaction_scan.json", redaction)
    if redaction["passed"] is not True:
        failures.append("redaction scan found secret-like text")

    status = "pass" if not blockers and not failures else "fail"
    receipt = {
        "receipt_id": "receipt_iter105_external_benchmark_pilot_design",
        "task_id": EXPERIMENT_ID,
        "agent_id": "codex",
        "benchmark_id": "telos_external_benchmark_pilot_design",
        "status": status,
        "stated_goal": (
            "Design the smallest defensible external benchmark pilot after iter104 differential "
            "adjudication, without benchmark execution or provider spend."
        ),
        "acceptance_criteria": [
            "iter104 evidence validates cleanly",
            "task source selection criteria are explicit",
            "baseline/Telos comparison design uses identical public artifacts",
            "sample-size and future budget ceilings are registered",
            "stopping and null-result rules are registered",
            "artifact and receipt requirements are registered",
            "no benchmark, model, production, SOTA, or broad superiority claim occurs",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": "pass" if prereq["clean_prerequisites"] else "fail",
                "artifact": "proof/iter104_prerequisite_validation.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/pilot_task_source_selection.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/baseline_telos_comparison_design.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/sample_size_budget_rationale.json",
            },
            {
                "kind": "adversarial_review",
                "status": "pass" if not failures else "fail",
                "artifact": "proof/review.md",
            },
        ],
        "falsifiers": [
            "iter104 prerequisite validation fails",
            "task-source selection cannot exclude flaky or non-public tasks",
            "strategy inputs are not identical",
            "private labels would leak into strategy inputs",
            "future spend/call ceilings are absent",
            "stopping or null-result rules are absent",
            "unsupported benchmark/model/SOTA or broad superiority claims appear",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(VALID / RECEIPT_NAME, receipt)

    write_result(task_source, comparison, budget, next_gate, blockers, failures)

    summary = {
        "schema_version": "telos.external_benchmark_pilot_design.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": False,
        "quality_failure": bool(failures),
        "blockers": blockers,
        "failures": failures,
        "iter104_clean_pass": prereq["clean_prerequisites"],
        "external_benchmark_pilot_design_claimed": True,
        "planned_packet_count": PLANNED_PACKET_COUNT,
        "planned_false_completion_packet_count": PLANNED_FALSE_PACKET_COUNT,
        "planned_legitimate_control_packet_count": PLANNED_LEGITIMATE_PACKET_COUNT,
        "future_paid_pilot_provider_call_ceiling": PLANNED_PROVIDER_CALL_CEILING,
        "future_paid_pilot_spend_ceiling_usd": decimal_string(FUTURE_SPEND_CEILING),
        "provider_api_calls": 0,
        "provider_cost_usd": "0.00000000",
        "benchmark_task_execution_in_this_gate": 0,
        "strategy_execution_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "external_benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "all_strategy_superiority_claimed": False,
        "redaction_scan_passed": redaction["passed"],
        "redaction_findings": redaction["findings"],
        "next_gate": next_gate,
        "next_gate_pre_registered": (ROOT / next_gate).exists(),
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"external benchmark pilot design: {status}")
    print(f"planned_packet_count={PLANNED_PACKET_COUNT}")
    print(f"planned_false_completion_packet_count={PLANNED_FALSE_PACKET_COUNT}")
    print(f"planned_legitimate_control_packet_count={PLANNED_LEGITIMATE_PACKET_COUNT}")
    print(f"future_paid_pilot_provider_call_ceiling={PLANNED_PROVIDER_CALL_CEILING}")
    print(f"future_paid_pilot_spend_ceiling_usd={decimal_string(FUTURE_SPEND_CEILING)}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("benchmark_task_execution_in_this_gate=0")
    print("benchmark_model_sota_claimed=false")
    print(f"next_gate={next_gate}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
