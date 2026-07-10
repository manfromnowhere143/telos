#!/usr/bin/env python3
"""Run iter89 same-slice discriminating-metric stability replication."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
ITER87_SCRIPT = ROOT / "scripts" / "verify_benchmark_facing_discriminating_metric_execution_pilot.py"
EXPERIMENT_ID = "iter89_same_slice_discriminating_metric_stability_replication"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_same_slice_discriminating_metric_stability_replication.json"
NEXT_GATE = "experiments/iter90_stability_replication_adjudication_after_same_slice_run/HYPOTHESIS.md"

ITER86_ID = "iter86_discriminating_metric_backtest_on_committed_artifacts"
ITER86_EXTRACTION = ROOT / "experiments" / ITER86_ID / "proof" / "raw_metric_extraction.json"
ITER87_ID = "iter87_benchmark_facing_discriminating_metric_execution_pilot"
ITER87_EXTRACTION = ROOT / "experiments" / ITER87_ID / "proof" / "fresh_metric_extraction.json"
ITER88_ID = "iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot"
ITER88_PROOF = ROOT / "experiments" / ITER88_ID / "proof"
ITER88_SUMMARY = ITER88_PROOF / "run_summary.json"
ITER88_ADJUDICATION = ITER88_PROOF / "mixed_direction_adjudication.json"
ITER88_DECISION = ITER88_PROOF / "next_step_decision.json"
ITER88_RECEIPT = (
    ITER88_PROOF
    / "valid"
    / "receipt_external_benchmark_readiness_adjudication_after_discriminating_pilot.json"
)

METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
TASKS = ["dummy", "battlesnake", "deterministic_edit"]
TOTAL_CALL_CEILING = 96
TOTAL_SPEND_CEILING_USD = Decimal("10.00000000")
PER_ROW_CALL_LIMIT = 16
PER_ROW_SPEND_LIMIT_USD = Decimal("2.00000000")
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


def load_iter87() -> Any:
    spec = importlib.util.spec_from_file_location("iter87_discriminating_metric_runner", ITER87_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load iter87 runner: {ITER87_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


iter87 = load_iter87()
SELECTED_PAIR_IDS = iter87.SELECTED_PAIR_IDS
TELOS_PAIR_IDS = iter87.TELOS_PAIR_IDS


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
        "schema_version": "telos.same_slice_discriminating_metric_stability_replication.redaction_scan.v1",
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


def configure_execution_runner() -> None:
    iter87.EXPERIMENT_ID = EXPERIMENT_ID
    iter87.EXPERIMENT = EXPERIMENT
    iter87.PROOF = PROOF
    iter87.RAW = RAW
    iter87.VALID = VALID
    iter87.RESULT = RESULT
    iter87.RECEIPT_NAME = RECEIPT_NAME
    iter87.configure_iter83_runner()
    iter87.iter83.OUTPUT_ROOT = Path("/tmp/telos-codeclash-discriminating-metric-stability-replication")


def validate_iter88() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER88_PROOF)])
    audit = run_capture(["python3", "scripts/audit_external_benchmark_readiness_adjudication_after_discriminating_pilot.py"])
    summary = read_json(ITER88_SUMMARY)
    adjudication = read_json(ITER88_ADJUDICATION)
    decision = read_json(ITER88_DECISION)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("next_step_decision") == "replicate_same_slice"
        and summary.get("same_slice_replication_supported") is True
        and summary.get("future_provider_call_ceiling") == TOTAL_CALL_CEILING
        and decimal_value(summary.get("future_provider_spend_ceiling_usd")) == TOTAL_SPEND_CEILING_USD
        and adjudication.get("sign_flip_count") == 3
        and decision.get("decision") == "replicate_same_slice"
        and summary.get("benchmark_result_claimed") is False
        and summary.get("model_superiority_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
    )
    packet = {
        "schema_version": "telos.same_slice_discriminating_metric_stability_replication.iter88_prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter88_status": summary.get("status"),
        "iter88_clean_pass": summary.get("clean_pass"),
        "iter88_receipt_validation_returncode": receipt["returncode"],
        "iter88_audit_returncode": audit["returncode"],
        "iter88_next_step_decision": summary.get("next_step_decision"),
        "iter88_same_slice_replication_supported": summary.get("same_slice_replication_supported"),
        "iter88_sign_flip_count": adjudication.get("sign_flip_count"),
        "iter88_future_provider_call_ceiling": summary.get("future_provider_call_ceiling"),
        "iter88_future_provider_spend_ceiling_usd": summary.get("future_provider_spend_ceiling_usd"),
        "clean_prerequisites": clean,
        "paid_execution_authorized_by_iter88": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER88_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_external_benchmark_readiness_adjudication_after_discriminating_pilot.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER88_SUMMARY), "sha256": sha256_file(ITER88_SUMMARY)},
            {"path": relative(ITER88_ADJUDICATION), "sha256": sha256_file(ITER88_ADJUDICATION)},
            {"path": relative(ITER88_DECISION), "sha256": sha256_file(ITER88_DECISION)},
            {"path": relative(ITER88_RECEIPT), "sha256": sha256_file(ITER88_RECEIPT)},
        ],
    }
    blockers = [] if clean else ["iter88_readiness_adjudication_not_clean"]
    return packet, blockers


def task_delta_by_task(path: Path) -> dict[str, dict[str, Any]]:
    packet = read_json(path)
    return {str(row["task_surface"]): row for row in packet.get("task_deltas", [])}


def stability_report(extraction: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    iter86 = task_delta_by_task(ITER86_EXTRACTION)
    iter87_packet = task_delta_by_task(ITER87_EXTRACTION)
    iter89 = {str(row["task_surface"]): row for row in extraction.get("task_deltas", [])}
    comparisons: list[dict[str, Any]] = []
    matches_iter87 = 0
    matches_iter86 = 0
    nonzero_count = 0
    for task in TASKS:
        old = iter86.get(task, {})
        prior = iter87_packet.get(task, {})
        current = iter89.get(task, {})
        current_direction = current.get("direction")
        prior_direction = prior.get("direction")
        old_direction = old.get("direction")
        matches_prior = current_direction == prior_direction
        matches_old = current_direction == old_direction
        matches_iter87 += int(matches_prior)
        matches_iter86 += int(matches_old)
        nonzero_count += int(Decimal(str(current.get("delta_telos_minus_baseline", "0"))) != 0)
        comparisons.append(
            {
                "task_surface": task,
                "iter86_delta_telos_minus_baseline": old.get("delta_telos_minus_baseline"),
                "iter86_direction": old_direction,
                "iter87_delta_telos_minus_baseline": prior.get("delta_telos_minus_baseline"),
                "iter87_direction": prior_direction,
                "iter89_delta_telos_minus_baseline": current.get("delta_telos_minus_baseline"),
                "iter89_direction": current_direction,
                "iter89_matches_iter87_direction": matches_prior,
                "iter89_matches_iter86_direction": matches_old,
            }
        )
    if failures:
        classification = "quality_failure"
        subclass = "quality_failure"
    elif extraction.get("all_rows_parsed") is not True:
        classification = "blocked"
        subclass = "metric_extraction_blocked"
    elif matches_iter87 == len(TASKS):
        classification = "stable"
        subclass = "iter89_replicates_iter87_task_directions"
    else:
        classification = "unstable"
        subclass = (
            "iter89_reverts_to_iter86_task_directions"
            if matches_iter86 == len(TASKS)
            else "iter89_mixed_against_prior_directions"
        )
    return {
        "schema_version": "telos.same_slice_discriminating_metric_stability_replication.stability_report.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": METRIC_ID,
        "source_backtest_iteration": ITER86_ID,
        "source_prior_execution_iteration": ITER87_ID,
        "source_current_execution_iteration": EXPERIMENT_ID,
        "task_comparisons": comparisons,
        "task_count": len(comparisons),
        "iter89_matches_iter87_direction_count": matches_iter87,
        "iter89_matches_iter86_direction_count": matches_iter86,
        "iter89_nonzero_task_delta_count": nonzero_count,
        "stability_classification": classification,
        "stability_subclassification": subclass,
        "external_benchmark_design_authorized_by_iter89": False,
        "benchmark_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
    }


def claim_boundary(status: str, stability: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.same_slice_discriminating_metric_stability_replication.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "allowed_claim": (
            "A bounded six-row same-slice stability replication was executed and classified."
            if status == "pass"
            else "A bounded same-slice stability replication produced blocked/fail evidence."
        ),
        "stability_classification": stability["stability_classification"],
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "external_benchmark_design_authorized_by_iter89": False,
    }


def decide_status(
    *,
    iter88_blockers: list[str],
    execution: dict[str, Any],
    extraction: dict[str, Any],
    extraction_blockers: list[str],
    stability: dict[str, Any],
) -> tuple[str, list[str], list[str]]:
    blockers = list(iter88_blockers)
    blockers.extend(str(item) for item in execution.get("execution_blockers_after_metric_redefinition", []))
    blockers.extend(extraction_blockers)
    failures = [str(item) for item in execution.get("execution_failures", [])]
    if execution.get("executed_pair_ids") != SELECTED_PAIR_IDS:
        blockers.append("not_exactly_six_frozen_rows_executed")
    if set(execution.get("executed_pair_ids", [])) - set(SELECTED_PAIR_IDS):
        failures.append("unselected_row_executed")
    if int(execution.get("provider_api_calls", 0)) > TOTAL_CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if decimal_value(execution.get("provider_cost_usd")) > TOTAL_SPEND_CEILING_USD:
        failures.append("provider_spend_ceiling_exceeded")
    for row in execution.get("row_results", []):
        if int(row.get("provider_api_calls", 0)) > PER_ROW_CALL_LIMIT:
            failures.append(f"{row.get('pair_id')}_per_row_call_ceiling_exceeded")
        if decimal_value(row.get("provider_cost_usd")) > PER_ROW_SPEND_LIMIT_USD:
            failures.append(f"{row.get('pair_id')}_per_row_spend_ceiling_exceeded")
        if row.get("raw_evidence_present") is not True:
            blockers.append(f"{row.get('pair_id')}_raw_evidence_missing")
        if row.get("pair_id") in TELOS_PAIR_IDS and row.get("receipt_valid") is not True:
            blockers.append(f"{row.get('pair_id')}_receipt_not_valid")
    if extraction.get("all_rows_parsed") is not True:
        blockers.append("fresh_metric_extraction_not_clean_for_all_rows")
    if execution.get("redaction_scan_passed_from_runner") is not True:
        failures.append("runner_redaction_scan_failed")
    if execution.get("redaction_findings_from_runner") not in ([], None):
        failures.append("runner_redaction_findings_present")
    if stability.get("next_gate_pre_registered") is not True:
        blockers.append("next_gate_not_pre_registered")
    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"
    return status, blockers, failures


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter89-same-slice-discriminating-metric-stability-replication-{status}",
        "task_id": "telos:iter89_same_slice_discriminating_metric_stability_replication@iter88",
        "agent_id": "codex-local-same-slice-stability-replication-runner",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute the same six frozen CodeClash rows as iter87 and classify stability under "
            "the task-native score-share delta metric."
        ),
        "acceptance_criteria": [
            "Iter88 receipt and audit validation pass.",
            "Exactly six frozen rows execute and no unselected row executes.",
            "Provider calls stay at or below 96 and spend stays at or below $10.00.",
            "Every row has raw artifacts, cost/call accounting, and valid receipts where required.",
            "The task-native score-share metric is computed from fresh raw artifacts.",
            "Task directions are compared against iter86 and iter87.",
            "No benchmark, leaderboard, SWE-bench, model-superiority, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Summary records row execution, costs, deltas, stability classification, and claim boundaries.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/raw/",
                "notes": "Raw packet contains command transcripts and copied CodeClash artifacts.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/stability_report.json",
                "notes": "Task-direction comparison against iter86 and iter87.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-benchmark/no-model/no-SOTA boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter88 validation fails.",
            "The result must fail if any unselected row executes.",
            "The result must fail if provider calls or spend exceed a frozen ceiling.",
            "The result must block if fresh score-share extraction is missing or ambiguous.",
            "The result must fail if credential, token, project, or service-account residue is committed.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_text_artifacts(
    *,
    status: str,
    iter88: dict[str, Any],
    execution: dict[str, Any],
    extraction: dict[str, Any],
    stability: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    RESULT.write_text(
        f"""# Iteration 89 Result - Same-Slice Discriminating Metric Stability Replication

Status: `{status.upper()}`.

## Summary

This gate ran the same six frozen rows as iter87 and evaluated fresh raw artifacts under
`{METRIC_ID}`. It is a bounded stability replication only, not a benchmark, model-superiority,
leaderboard, SWE-bench, production/live-domain, or state-of-the-art claim.

- iter88 validation clean: `{str(iter88['clean_prerequisites']).lower()}`,
- selected row count: `{len(SELECTED_PAIR_IDS)}`,
- executed row count: `{execution['executed_pair_count']}`,
- per-row provider call ceiling: `{PER_ROW_CALL_LIMIT}`,
- provider API calls: `{execution['provider_api_calls']}`,
- provider call ceiling: `{TOTAL_CALL_CEILING}`,
- provider cost from CodeClash metadata: `${Decimal(execution['provider_cost_usd']):.8f}`,
- provider spend ceiling: `${TOTAL_SPEND_CEILING_USD:.2f}`,
- metric: `{METRIC_ID}`,
- fresh metric rows parsed: `{extraction['row_count']}`,
- fresh task deltas computed: `{extraction['task_delta_count']}`,
- stability classification: `{stability['stability_classification']}`,
- stability subclassification: `{stability['stability_subclassification']}`,
- iter89 directions matching iter87: `{stability['iter89_matches_iter87_direction_count']}`,
- iter89 directions matching iter86: `{stability['iter89_matches_iter86_direction_count']}`,
- next gate: `{NEXT_GATE}`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Fresh Metric Deltas

| Task surface | Baseline score share | Telos score share | Telos-minus-baseline | Direction |
| --- | --- | --- | --- | --- |
""",
        encoding="utf-8",
    )
    with RESULT.open("a", encoding="utf-8") as handle:
        for row in extraction["task_deltas"]:
            handle.write(
                f"| `{row['task_surface']}` | `{row['baseline_score_share']}` | "
                f"`{row['telos_score_share']}` | `{row['delta_telos_minus_baseline']}` | "
                f"`{row['direction']}` |\n"
            )
        handle.write(
            """
## Stability Comparison

| Task surface | Iter86 direction | Iter87 direction | Iter89 direction | Matches iter87 |
| --- | --- | --- | --- | --- |
"""
        )
        for row in stability["task_comparisons"]:
            handle.write(
                f"| `{row['task_surface']}` | `{row['iter86_direction']}` | "
                f"`{row['iter87_direction']}` | `{row['iter89_direction']}` | "
                f"`{str(row['iter89_matches_iter87_direction']).lower()}` |\n"
            )
        handle.write(
            """
## Claim Boundary

This gate may claim only a bounded six-row same-slice stability replication and its stability
classification. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

## Evidence

- `proof/iter88_prerequisite_validation.json`
- `proof/execution_accounting_report.json`
- `proof/fresh_metric_extraction.json`
- `proof/stability_report.json`
- `proof/claim_boundary.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_same_slice_discriminating_metric_stability_replication.json`
"""
        )

    command_lines = [
        f"same-slice discriminating metric stability replication: {status}",
        f"iter88_receipt_validation_returncode={iter88['iter88_receipt_validation_returncode']}",
        f"iter88_audit_returncode={iter88['iter88_audit_returncode']}",
        f"selected_pair_count={len(SELECTED_PAIR_IDS)}",
        f"executed_pair_count={execution['executed_pair_count']}",
        f"per_row_call_limit={PER_ROW_CALL_LIMIT}",
        f"provider_api_calls={execution['provider_api_calls']}",
        f"provider_call_ceiling={TOTAL_CALL_CEILING}",
        f"provider_cost_usd={execution['provider_cost_usd']}",
        f"provider_spend_ceiling_usd={decimal_string(TOTAL_SPEND_CEILING_USD)}",
        f"metric_id={METRIC_ID}",
        f"fresh_metric_rows_parsed={extraction['row_count']}",
        f"fresh_task_deltas_computed={extraction['task_delta_count']}",
        f"stability_classification={stability['stability_classification']}",
        f"stability_subclassification={stability['stability_subclassification']}",
        f"iter89_matches_iter87_direction_count={stability['iter89_matches_iter87_direction_count']}",
        f"iter89_matches_iter86_direction_count={stability['iter89_matches_iter86_direction_count']}",
        "benchmark_result_claimed=false",
        "model_superiority_claimed=false",
        "state_of_the_art_result_claimed=false",
        f"next_gate={NEXT_GATE}",
        f"blockers={','.join(blockers) if blockers else 'none'}",
        f"failures={','.join(failures) if failures else 'none'}",
    ]
    for row in extraction["task_deltas"]:
        command_lines.append(
            f"{row['task_surface']}: baseline_score_share={row['baseline_score_share']} "
            f"telos_score_share={row['telos_score_share']} "
            f"delta={row['delta_telos_minus_baseline']} direction={row['direction']}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")
    (PROOF / "review.md").write_text(
        f"""# Iteration 89 Review

The gate used the same six frozen rows as iter87 and judged the result on fresh `{METRIC_ID}`
metadata. The result is a stability replication, not a benchmark score.

- status: `{status}`,
- executed row count: `{execution['executed_pair_count']}`,
- provider API calls: `{execution['provider_api_calls']}`,
- provider cost: `${Decimal(execution['provider_cost_usd']):.8f}`,
- stability classification: `{stability['stability_classification']}`,
- stability subclassification: `{stability['stability_subclassification']}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

No benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
state-of-the-art result is claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    configure_execution_runner()
    runner_rc = iter87.iter83.main()
    iter88, iter88_blockers = validate_iter88()
    write_json(PROOF / "iter88_prerequisite_validation.json", iter88)

    runner_summary = read_json(PROOF / "run_summary.json")
    runner_report = read_json(PROOF / "protocol_effect_report.json")
    execution = iter87.build_execution_accounting(runner_report, runner_summary)
    execution["schema_version"] = (
        "telos.same_slice_discriminating_metric_stability_replication.execution_accounting.v1"
    )
    execution["experiment_id"] = EXPERIMENT_ID
    write_json(PROOF / "execution_accounting_report.json", execution)

    extraction, extraction_blockers = iter87.extract_metric_rows(runner_report)
    extraction["schema_version"] = (
        "telos.same_slice_discriminating_metric_stability_replication.fresh_metric_extraction.v1"
    )
    extraction["experiment_id"] = EXPERIMENT_ID
    write_json(PROOF / "fresh_metric_extraction.json", extraction)

    stability = stability_report(extraction, [])
    status, blockers, failures = decide_status(
        iter88_blockers=iter88_blockers,
        execution=execution,
        extraction=extraction,
        extraction_blockers=extraction_blockers,
        stability=stability,
    )
    if runner_rc != 0 and not failures:
        failures.append("underlying_execution_runner_returned_nonzero")
        status = "fail"
    stability = stability_report(extraction, failures)
    write_json(PROOF / "stability_report.json", stability)

    boundary = claim_boundary(status, stability)
    write_json(PROOF / "claim_boundary.json", boundary)
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(
        status=status,
        iter88=iter88,
        execution=execution,
        extraction=extraction,
        stability=stability,
        blockers=blockers,
        failures=failures,
    )
    scan = redaction_scan()
    if not scan["passed"] and "redaction_scan_failed" not in failures:
        failures.append("redaction_scan_failed")
        status = "fail"
        stability = stability_report(extraction, failures)
        boundary = claim_boundary(status, stability)
        write_json(PROOF / "stability_report.json", stability)
        write_json(PROOF / "claim_boundary.json", boundary)
        write_json(VALID / RECEIPT_NAME, build_receipt(status))
        write_text_artifacts(
            status=status,
            iter88=iter88,
            execution=execution,
            extraction=extraction,
            stability=stability,
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
                f"Same-slice replication classified task-direction stability as "
                f"{stability['stability_classification']}."
                if status == "pass"
                else "The same-slice stability replication published bounded blocked/fail evidence."
            ),
            "next_action": "adjudicate iter89 stability evidence before any larger benchmark design",
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/execution_accounting_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/fresh_metric_extraction.json",
                f"experiments/{EXPERIMENT_ID}/proof/stability_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary = {
        "schema_version": "telos.same_slice_discriminating_metric_stability_replication.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter88_status": iter88["iter88_status"],
        "iter88_clean_pass": iter88["iter88_clean_pass"],
        "iter88_receipt_validation_returncode": iter88["iter88_receipt_validation_returncode"],
        "iter88_audit_returncode": iter88["iter88_audit_returncode"],
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": execution["executed_pair_ids"],
        "executed_pair_count": execution["executed_pair_count"],
        "provider_api_calls": execution["provider_api_calls"],
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_cost_usd": execution["provider_cost_usd"],
        "provider_spend_ceiling_usd": decimal_string(TOTAL_SPEND_CEILING_USD),
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": decimal_string(PER_ROW_SPEND_LIMIT_USD),
        "wall_clock_seconds": execution["wall_clock_seconds"],
        "wall_clock_ceiling_seconds": execution["wall_clock_ceiling_seconds"],
        "metric_id": METRIC_ID,
        "fresh_metric_computable": extraction["all_rows_parsed"],
        "fresh_metric_rows_parsed": extraction["row_count"],
        "fresh_task_deltas_computed": extraction["task_delta_count"],
        "metric_collapsed_to_completion_boolean": extraction["metric_collapsed_to_completion_boolean"],
        "metric_non_saturated": extraction["metric_collapsed_to_completion_boolean"] is False,
        "nonzero_task_delta_count": extraction["nonzero_task_delta_count"],
        "mixed_direction_signal": extraction["mixed_direction_signal"],
        "task_deltas": extraction["task_deltas"],
        "stability_classification": stability["stability_classification"],
        "stability_subclassification": stability["stability_subclassification"],
        "iter89_matches_iter87_direction_count": stability["iter89_matches_iter87_direction_count"],
        "iter89_matches_iter86_direction_count": stability["iter89_matches_iter86_direction_count"],
        "stability_task_comparisons": stability["task_comparisons"],
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": stability["next_gate_pre_registered"],
        "runner_status": execution["runner_status"],
        "ignored_runner_blockers": execution["ignored_runner_blockers"],
        "old_verified_completion_metric_used_for_iter89_status": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "external_benchmark_design_authorized_by_iter89": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "redaction_scan_passed": scan["passed"],
        "redaction_findings": scan["findings"],
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"same-slice discriminating metric stability replication: {status}")
    print(f"selected_pair_count={len(SELECTED_PAIR_IDS)}")
    print(f"executed_pair_count={execution['executed_pair_count']}")
    print(f"provider_api_calls={execution['provider_api_calls']}")
    print(f"provider_call_ceiling={TOTAL_CALL_CEILING}")
    print(f"provider_cost_usd={execution['provider_cost_usd']}")
    print(f"provider_spend_ceiling_usd={decimal_string(TOTAL_SPEND_CEILING_USD)}")
    print(f"metric_id={METRIC_ID}")
    print(f"fresh_metric_rows_parsed={extraction['row_count']}")
    print(f"fresh_task_deltas_computed={extraction['task_delta_count']}")
    print(f"stability_classification={stability['stability_classification']}")
    print(f"stability_subclassification={stability['stability_subclassification']}")
    print(f"next_gate={NEXT_GATE}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
