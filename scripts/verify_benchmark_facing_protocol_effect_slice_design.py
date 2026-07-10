#!/usr/bin/env python3
"""Verify iter82 benchmark-facing protocol-effect slice design."""

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
EXPERIMENT_ID = "iter82_benchmark_facing_protocol_effect_slice_design"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_benchmark_facing_protocol_effect_slice_design.json"
NEXT_GATE = "experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/HYPOTHESIS.md"
ITER81_ID = "iter81_expanded_stratified_adapter_validation_consolidation"
ITER81_PROOF = ROOT / "experiments" / ITER81_ID / "proof"
ITER81_SUMMARY = ITER81_PROOF / "run_summary.json"
ITER81_ACCOUNTING = ITER81_PROOF / "stratified_row_accounting.json"
ITER81_RECEIPT = (
    ITER81_PROOF
    / "valid"
    / "receipt_expanded_stratified_adapter_validation_consolidation.json"
)
ITER39_SLICE = (
    ROOT
    / "experiments"
    / "iter39_public_task_protocol_effect_slice"
    / "proof"
    / "protocol_effect_slice.json"
)
ITER45_MANIFEST = (
    ROOT
    / "experiments"
    / "iter45_public_task_condition_executor_assembly"
    / "proof"
    / "executor_manifest.json"
)
ZERO_COST = Decimal("0.00000000")
FUTURE_PROVIDER_CALL_CEILING = 96
FUTURE_PROVIDER_SPEND_CEILING = Decimal("10.00000000")
FUTURE_PER_ROW_CALL_LIMIT = 16
FUTURE_PER_ROW_SPEND_LIMIT = Decimal("2.00000000")
FUTURE_ROW_COUNT = 6
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{TELOS_VERTEX_BEARER_TOKEN\}|\[REDACTED_BEARER_TOKEN\])\S+"),
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001")), "f")


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
                findings.append({"path": str(path.relative_to(ROOT)), "pattern": pattern.pattern})
                break
    return {
        "schema_version": "telos.benchmark_facing_slice_design.redaction_scan.v1",
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


def validate_iter81() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", str(ITER81_PROOF.relative_to(ROOT))])
    audit = run_capture(["python3", "scripts/audit_expanded_stratified_adapter_validation_consolidation.py"])
    summary = read_json(ITER81_SUMMARY)
    accounting = read_json(ITER81_ACCOUNTING)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("quality_failure") is False
        and summary.get("benchmark_result_claimed") is False
        and summary.get("model_superiority_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
        and summary.get("leaderboard_or_swebench_result_claimed") is False
        and accounting.get("consolidated_success_pair_count") == 6
        and accounting.get("all_task_surfaces_stratified") is True
        and accounting.get("cross_task_surface_pooling_authorized") is False
    )
    blockers = [] if clean else ["iter81_consolidation_not_clean"]
    packet = {
        "schema_version": "telos.benchmark_facing_slice_design.prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter81_status": summary.get("status"),
        "iter81_clean_pass": summary.get("clean_pass"),
        "iter81_consolidated_success_pair_count": summary.get("consolidated_success_pair_count"),
        "iter81_diagnostic_blocked_pair_count": summary.get("diagnostic_blocked_pair_count"),
        "iter81_source_packet_total_provider_api_calls": summary.get(
            "source_packet_total_provider_api_calls"
        ),
        "iter81_source_packet_total_provider_cost_usd": summary.get(
            "source_packet_total_provider_cost_usd"
        ),
        "iter81_receipt_validation_returncode": receipt["returncode"],
        "iter81_audit_returncode": audit["returncode"],
        "clean_prerequisites": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {ITER81_PROOF.relative_to(ROOT)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_expanded_stratified_adapter_validation_consolidation.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {
                "path": str(ITER81_SUMMARY.relative_to(ROOT)),
                "sha256": sha256_file(ITER81_SUMMARY),
            },
            {
                "path": str(ITER81_ACCOUNTING.relative_to(ROOT)),
                "sha256": sha256_file(ITER81_ACCOUNTING),
            },
            {
                "path": str(ITER81_RECEIPT.relative_to(ROOT)),
                "sha256": sha256_file(ITER81_RECEIPT),
            },
        ],
    }
    return packet, blockers


def build_task_eligibility() -> tuple[dict[str, Any], list[str]]:
    source_slice = read_json(ITER39_SLICE)
    manifest = read_json(ITER45_MANIFEST)
    tasks = source_slice.get("executable_tasks", [])
    if not isinstance(tasks, list):
        tasks = []
    selected_tasks: list[dict[str, Any]] = []
    for task in tasks:
        public_config = str(task.get("public_config", ""))
        selected_tasks.append(
            {
                "task_id": task.get("task_id"),
                "task_family": task.get("task_family"),
                "public_config": public_config,
                "source_commit_sha": task.get("source_commit_sha"),
                "eligibility_status": "selected_for_future_paid_pilot",
                "selection_reason": (
                    "committed public CodeClash task surface with frozen baseline and "
                    "Telos receipt-enforced conditions plus provider-compatible adapter evidence"
                ),
                "claim_boundary": "protocol-effect pilot row only; not a benchmark score",
            }
        )
    excluded = [
        {
            "candidate": "SWE-bench Verified execution row",
            "eligibility_status": "excluded_from_future_paid_pilot",
            "reason": (
                "retained only as a receipt-field anchor until a separate SWE-bench execution "
                "harness, cost contract, and leaderboard claim boundary are pre-registered"
            ),
        },
        {
            "candidate": "prior iter66/iter78/iter80 provider outputs",
            "eligibility_status": "excluded_as_new_benchmark_result",
            "reason": (
                "prior rows are calibration and adapter-validation evidence; the future gate must "
                "rerun the frozen rows if it wants execution evidence"
            ),
        },
        {
            "candidate": "uncommitted or live-domain task surfaces",
            "eligibility_status": "excluded",
            "reason": "task source, raw artifacts, and failure semantics must be committed first",
        },
    ]
    pair_ids = manifest.get("pair_ids", [])
    blockers: list[str] = []
    if len(selected_tasks) != 3:
        blockers.append("expected_three_selected_codeclash_tasks")
    if len(pair_ids) != FUTURE_ROW_COUNT:
        blockers.append("expected_six_future_pairs")
    packet = {
        "schema_version": "telos.benchmark_facing_slice_design.task_eligibility.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_protocol_slice": str(ITER39_SLICE.relative_to(ROOT)),
        "source_protocol_slice_sha256": sha256_file(ITER39_SLICE),
        "source_executor_manifest": str(ITER45_MANIFEST.relative_to(ROOT)),
        "source_executor_manifest_sha256": sha256_file(ITER45_MANIFEST),
        "selected_task_count": len(selected_tasks),
        "selected_pair_count": len(pair_ids),
        "selected_tasks": selected_tasks,
        "selected_pair_ids": pair_ids,
        "exclusions": excluded,
        "eligibility_rules": [
            "Task source and public config must be committed and hashable.",
            "Both baseline and Telos receipt-enforced conditions must be defined before execution.",
            "Provider-compatible execution must have a bounded call and spend envelope.",
            "Prior adapter-validation rows may inform ceilings but may not be reused as benchmark results.",
            "SWE-bench execution is excluded until a separate SWE-bench harness gate exists.",
            "No task may require GPU, cloud-runner startup, Sentinel mutation, or live-domain mutation.",
        ],
        "cross_task_surface_pooling_authorized": False,
        "benchmark_result_authorized": False,
        "swebench_result_authorized": False,
    }
    return packet, blockers


def build_condition_contract(task_eligibility: dict[str, Any]) -> dict[str, Any]:
    conditions = read_json(ITER39_SLICE).get("conditions", [])
    return {
        "schema_version": "telos.benchmark_facing_slice_design.condition_contract.v1",
        "experiment_id": EXPERIMENT_ID,
        "condition_count": 2,
        "conditions": conditions,
        "selected_pair_ids": task_eligibility["selected_pair_ids"],
        "primary_metric": {
            "metric_id": "verified_completion_evidence_by_task_and_condition",
            "definition": (
                "For each frozen task-condition row, report whether committed raw evidence and "
                "required receipts support verified completion."
            ),
            "aggregate_benchmark_metric_authorized": False,
            "reporting": "exact row counts by task and condition before any percentages",
        },
        "comparison_rules": [
            "Compare baseline and Telos rows only within the same public_config.",
            "Do not pool Dummy, BattleSnake, deterministic-edit, or SWE-bench anchor evidence.",
            "Receipt-required Telos rows count as unverified if the receipt is missing or invalid.",
            "Blocked rows remain in the denominator for the future pilot's exact counts.",
        ],
    }


def build_evidence_requirements(task_eligibility: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.benchmark_facing_slice_design.evidence_requirements.v1",
        "experiment_id": EXPERIMENT_ID,
        "future_gate": NEXT_GATE,
        "required_future_artifacts": [
            "proof/preflight.json",
            "proof/protocol_effect_report.json",
            "proof/run_summary.json",
            "proof/raw/<pair_id>/command_execution.json",
            "proof/raw/<pair_id>/command_stdout.txt",
            "proof/raw/<pair_id>/command_stderr.txt",
            "proof/raw/<pair_id>/metadata.json",
            "proof/raw/<pair_id>/redaction_scan.json",
            "proof/command_output.txt",
            "proof/review.md",
            "proof/valid/receipt_benchmark_facing_protocol_effect_execution_pilot.json",
        ],
        "per_pair_requirements": [
            {
                "pair_id": pair_id,
                "raw_logs_required": True,
                "metadata_required": True,
                "cost_and_call_stats_required": True,
                "redaction_scan_required": True,
                "telos_receipt_required_before_acceptance": pair_id.startswith(
                    "telos-receipt-enforced-completion-evidence__"
                ),
            }
            for pair_id in task_eligibility["selected_pair_ids"]
        ],
        "redaction_forbidden_residue": [
            "credential material",
            "access tokens",
            "service-account email",
            "project identifier",
            "unredacted provider-specific private fields",
        ],
        "missing_cost_or_call_stats_blocks_result": True,
        "missing_raw_artifacts_blocks_row": True,
    }


def build_future_run_plan(task_eligibility: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.benchmark_facing_slice_design.future_paid_run_plan.v1",
        "experiment_id": EXPERIMENT_ID,
        "future_gate": NEXT_GATE,
        "future_execution_enabled_in_iter82": False,
        "adapter_rows_to_execute_in_iter82": 0,
        "provider_model_invocations_in_iter82": 0,
        "provider_spend_in_iter82_usd": decimal_string(ZERO_COST),
        "future_adapter_rows_to_execute": FUTURE_ROW_COUNT,
        "future_selected_pair_ids": task_eligibility["selected_pair_ids"],
        "future_provider_model_invocation_ceiling": FUTURE_PROVIDER_CALL_CEILING,
        "future_per_row_call_limit": FUTURE_PER_ROW_CALL_LIMIT,
        "future_provider_spend_ceiling_usd": decimal_string(FUTURE_PROVIDER_SPEND_CEILING),
        "future_per_row_spend_limit_usd": decimal_string(FUTURE_PER_ROW_SPEND_LIMIT),
        "future_wall_clock_ceiling_minutes": 90,
        "future_cloud_runner_startup": "forbidden",
        "future_gpu_use": "forbidden",
        "future_sentinel_named_resource_mutation": "forbidden",
        "future_production_or_live_domain_mutation": "forbidden",
        "future_benchmark_model_or_sota_claim": "forbidden",
        "stop_rules": [
            "Stop before execution if iter82 receipt or audit validation fails.",
            "Stop before execution if ADC/provider readiness cannot be checked without printing secrets.",
            "Stop if any unselected row would execute.",
            "Stop if provider call or spend ceilings would be exceeded.",
            "Stop if cost or call stats are missing from a completed provider-backed row.",
            "Stop if redaction scan finds credential, token, project, or service-account residue.",
        ],
        "reporting_rules": [
            "Report exact row counts before rates.",
            "Report baseline and Telos conditions by task surface.",
            "Publish pass, blocked, null, and fail rows at full weight.",
            "Do not report a leaderboard, SWE-bench, model-superiority, production, or SOTA result.",
        ],
    }


def build_failure_semantics() -> dict[str, Any]:
    return {
        "schema_version": "telos.benchmark_facing_slice_design.failure_semantics.v1",
        "experiment_id": EXPERIMENT_ID,
        "pass_semantics_for_future_gate": [
            "All six selected rows execute under the frozen call and spend ceilings.",
            "All required raw artifacts, cost/call stats, redaction scans, and receipts validate.",
            "No unsupported benchmark/model/SOTA claim appears.",
        ],
        "blocked_semantics_for_future_gate": [
            "Provider readiness, receipt validation, cost capture, or raw artifact capture blocks before a trustworthy row result can be interpreted.",
            "One or more selected rows cannot run while preserving frozen scope and ceilings.",
        ],
        "null_semantics_for_future_gate": [
            "Rows run but show no Telos-minus-baseline difference in verified-completion evidence.",
            "Rows are too small or too noisy to support a stronger next step.",
        ],
        "quality_failure_semantics_for_future_gate": [
            "Any unselected row executes.",
            "Provider calls or spend exceed the frozen ceilings.",
            "Credential, token, project, or service-account residue is committed.",
            "GPU, cloud runner, Sentinel mutation, production/live-domain mutation, or hidden task mutation occurs.",
            "A benchmark, leaderboard, SWE-bench, model-superiority, or state-of-the-art claim is made.",
        ],
    }


def build_claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "telos.benchmark_facing_slice_design.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "claim_allowed_if_pass": (
            "A bounded benchmark-facing protocol-effect execution pilot has been designed and "
            "pre-registered for a later paid gate."
        ),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "claims_forbidden": [
            "benchmark performance",
            "leaderboard standing",
            "SWE-bench score",
            "model superiority",
            "production/live-domain behavior",
            "state-of-the-art status",
        ],
    }


def write_command_output(prereq: dict[str, Any]) -> None:
    lines = [
        "iter82 benchmark-facing protocol-effect slice design",
        "",
        "Prerequisite validation commands:",
    ]
    for item in prereq["command_results"]:
        lines.append(f"$ {item['command']}")
        lines.append(f"returncode={item['returncode']} timed_out={item['timed_out']}")
        if item.get("stdout"):
            lines.append("stdout:")
            lines.append(str(item["stdout"]))
        if item.get("stderr"):
            lines.append("stderr:")
            lines.append(str(item["stderr"]))
        lines.append("")
    lines.extend(
        [
            "Local iter82 activity:",
            "- adapter rows executed: 0",
            "- provider model invocations: 0",
            "- provider spend: $0.00000000",
            "- GPU/cloud/Sentinel/live-domain mutation: false",
            "- benchmark/model/SOTA claim: false",
        ]
    )
    (PROOF / "command_output.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_review(future_plan: dict[str, Any]) -> None:
    review = f"""# Iteration 82 Adversarial Review

The gate designs a future paid execution pilot but performs no provider execution itself. Iter82
uses zero provider calls, zero spend, zero row execution, no GPU, no cloud runner, no Sentinel
mutation, and no production/live-domain mutation.

The future paid pilot is bounded to `{future_plan['future_adapter_rows_to_execute']}` selected
CodeClash task-condition rows, `{future_plan['future_provider_model_invocation_ceiling']}` provider
model invocations, and `${future_plan['future_provider_spend_ceiling_usd']}` total spend. The
per-row call ceiling is `{future_plan['future_per_row_call_limit']}` and the per-row spend ceiling
is `${future_plan['future_per_row_spend_limit_usd']}`.

The main adversarial risk is overclaiming. This design treats CodeClash rows as a public
protocol-effect pilot and keeps SWE-bench Verified as a receipt-field anchor only. The future gate
may report exact row-level evidence, blocked rows, and nulls, but it may not report a leaderboard,
SWE-bench, production/live-domain, model-superiority, benchmark-performance, or state-of-the-art
result.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter82-benchmark-facing-protocol-effect-slice-design-{status}",
        "task_id": "telos:iter82_benchmark_facing_protocol_effect_slice_design@iter81",
        "agent_id": "codex-local-benchmark-facing-slice-designer",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Design a bounded benchmark-facing protocol-effect slice for a later paid execution "
            "gate without making execution or benchmark claims."
        ),
        "acceptance_criteria": [
            "Iter81 validates as a clean consolidation packet.",
            "Benchmark-facing task eligibility and exclusion rules are explicit.",
            "Baseline and Telos condition contracts are frozen.",
            "Future receipt, raw-artifact, redaction, cost, and failure-mode requirements are frozen.",
            "Future provider-call and spend ceilings are exact and bounded.",
            "No provider calls, spend, row execution, GPU, cloud runner, Sentinel mutation, or live-domain mutation occur in iter82.",
            "No benchmark, leaderboard, SWE-bench, model-superiority, production, live-domain, or state-of-the-art claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records prerequisite validation, future ceilings, and claim boundary.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/task_eligibility_rules.json",
                "notes": "Eligibility and exclusion rules prevent pooling internal evidence into a benchmark claim.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/future_paid_run_plan.json",
                "notes": "The future paid pilot is bounded by row, call, spend, and mutation ceilings.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-benchmark/no-SOTA boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter81 validation fails.",
            "The result must block if task eligibility cannot be stated without pooling internal strata.",
            "The result must block if future pass/null/fail semantics cannot be frozen before execution.",
            "The result must fail if any provider call, spend, or row execution occurs in iter82.",
            "The result must fail if credential, token, project, or service-account residue is committed.",
            "The result must fail if unsupported benchmark, leaderboard, SWE-bench, model-superiority, or SOTA claims appear.",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_learning_record(summary: dict[str, Any]) -> None:
    record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": summary["status"],
        "insight": (
            "The next paid benchmark-facing move can be bounded to six CodeClash public "
            "task-condition rows while keeping SWE-bench Verified as a receipt-field anchor only."
        ),
        "next_action": (
            "run the pre-registered six-row benchmark-facing protocol-effect execution pilot under "
            "the frozen $10.00 and 96-call ceilings"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/task_eligibility_rules.json",
            f"experiments/{EXPERIMENT_ID}/proof/future_paid_run_plan.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
        ],
    }
    write_json(PROOF / "learning_record.json", record)


def write_result(summary: dict[str, Any], future_plan: dict[str, Any]) -> None:
    status = "PASS" if summary["status"] == "pass" else summary["status"].upper()
    result = f"""# Iteration 82 Result - Benchmark-Facing Protocol-Effect Slice Design

Status: `{status}`.

## Summary

The gate designed a bounded benchmark-facing protocol-effect execution pilot without running it.

- iter81 prerequisite validation clean: `{str(summary['iter81_clean']).lower()}`,
- selected future task-condition rows: `{future_plan['future_adapter_rows_to_execute']}`,
- future provider call ceiling: `{future_plan['future_provider_model_invocation_ceiling']}`,
- future provider spend ceiling: `${future_plan['future_provider_spend_ceiling_usd']}`,
- future per-row call ceiling: `{future_plan['future_per_row_call_limit']}`,
- future per-row spend ceiling: `${future_plan['future_per_row_spend_limit_usd']}`,
- adapter rows executed in this gate: `0`,
- provider API calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{', '.join(summary['blockers']) if summary['blockers'] else 'none'}`,
- failures: `{', '.join(summary['failures']) if summary['failures'] else 'none'}`.

## Frozen Design

- Future selected rows: the six baseline/Telos CodeClash task-condition pairs from the committed
  public task executor manifest.
- SWE-bench Verified role: receipt-field anchor only; no SWE-bench execution or score is claimed.
- Primary metric: verified-completion evidence by task and condition, reported as exact row counts
  before any rates.
- Failure semantics: pass, blocked, null, and quality-failure outcomes are frozen before execution.

## Next Gate

The bounded next recommendation is
[`{NEXT_GATE}`](../../{NEXT_GATE}): a paid execution pilot under the frozen ceilings.

## Claim Boundary

This is a benchmark-facing slice-design result only. It is not a benchmark result, SWE-bench score,
leaderboard result, production/live-domain result, model-superiority result, or state-of-the-art
result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/task_eligibility_rules.json`
- `proof/condition_contract.json`
- `proof/evidence_requirements.json`
- `proof/future_paid_run_plan.json`
- `proof/failure_semantics.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
    RESULT.write_text(result, encoding="utf-8")


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter81()
    write_json(PROOF / "prerequisite_validation.json", prereq)
    write_command_output(prereq)

    task_eligibility, eligibility_blockers = build_task_eligibility()
    blockers.extend(eligibility_blockers)
    write_json(PROOF / "task_eligibility_rules.json", task_eligibility)

    condition_contract = build_condition_contract(task_eligibility)
    write_json(PROOF / "condition_contract.json", condition_contract)
    evidence_requirements = build_evidence_requirements(task_eligibility)
    write_json(PROOF / "evidence_requirements.json", evidence_requirements)
    future_plan = build_future_run_plan(task_eligibility)
    write_json(PROOF / "future_paid_run_plan.json", future_plan)
    failure_semantics = build_failure_semantics()
    write_json(PROOF / "failure_semantics.json", failure_semantics)
    claim_boundary = build_claim_boundary()
    write_json(PROOF / "claim_boundary.json", claim_boundary)
    write_review(future_plan)

    redaction = redaction_scan()
    write_json(PROOF / "redaction_scan.json", redaction)

    failures: list[str] = []
    if not redaction["passed"]:
        failures.append("redaction_scan_failed")
    if future_plan["adapter_rows_to_execute_in_iter82"] != 0:
        failures.append("iter82_row_execution_occurred")
    if future_plan["provider_model_invocations_in_iter82"] != 0:
        failures.append("iter82_provider_invocation_occurred")
    if future_plan["provider_spend_in_iter82_usd"] != decimal_string(ZERO_COST):
        failures.append("iter82_provider_spend_occurred")
    if not (ROOT / NEXT_GATE).exists():
        blockers.append("next_gate_hypothesis_missing")

    status = "fail" if failures else "blocked" if blockers else "pass"
    summary = {
        "schema_version": "telos.benchmark_facing_slice_design.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter81_clean": prereq["clean_prerequisites"],
        "selected_task_count": task_eligibility["selected_task_count"],
        "selected_pair_count": task_eligibility["selected_pair_count"],
        "future_gate": NEXT_GATE,
        "future_provider_model_invocation_ceiling": FUTURE_PROVIDER_CALL_CEILING,
        "future_provider_spend_ceiling_usd": decimal_string(FUTURE_PROVIDER_SPEND_CEILING),
        "future_per_row_call_limit": FUTURE_PER_ROW_CALL_LIMIT,
        "future_per_row_spend_limit_usd": decimal_string(FUTURE_PER_ROW_SPEND_LIMIT),
        "adapter_rows_executed_in_this_gate": 0,
        "provider_api_calls": 0,
        "provider_cost_usd": 0.0,
        "provider_spend_ceiling_usd": 0.0,
        "provider_call_ceiling": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "swebench_execution_or_score_claimed": False,
        "primary_metric": {
            "metric_id": "verified_completion_evidence_by_task_and_condition",
            "future_row_count": FUTURE_ROW_COUNT,
            "aggregate_benchmark_metric_authorized": False,
            "current_gate_execution_evidence": "none",
        },
        "redaction_scan_passed": redaction["passed"],
        "redaction_findings": redaction["findings"],
    }
    write_learning_record(summary)
    receipt = build_receipt(status)
    write_json(VALID / RECEIPT_NAME, receipt)
    summary["artifact_hashes"] = artifact_hashes()
    write_json(PROOF / "run_summary.json", summary)
    write_result(summary, future_plan)

    print(f"benchmark-facing protocol-effect slice design: {status}")
    print(f"iter81_clean={summary['iter81_clean']}")
    print(f"selected_task_count={summary['selected_task_count']}")
    print(f"selected_pair_count={summary['selected_pair_count']}")
    print(f"future_provider_call_ceiling={FUTURE_PROVIDER_CALL_CEILING}")
    print(f"future_provider_spend_ceiling_usd={decimal_string(FUTURE_PROVIDER_SPEND_CEILING)}")
    print("provider_api_calls_in_this_gate=0")
    print("provider_cost_usd_in_this_gate=0.00000000")
    print("benchmark_model_sota_claim=false")
    print(f"next_gate={NEXT_GATE}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
