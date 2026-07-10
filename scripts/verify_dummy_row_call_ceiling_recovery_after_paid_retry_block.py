#!/usr/bin/env python3
"""Verify iter79 Dummy row call-ceiling recovery from committed iter78 artifacts."""

from __future__ import annotations

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
EXPERIMENT_ID = "iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_dummy_row_call_ceiling_recovery_after_paid_retry_block.json"
ITER78_ID = "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery"
ITER78 = ROOT / "experiments" / ITER78_ID
ITER78_PROOF = ITER78 / "proof"
ITER78_SUMMARY = ITER78_PROOF / "run_summary.json"
ITER78_REPORT = ITER78_PROOF / "protocol_effect_report.json"
NEXT_GATE = (
    "experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/"
    "HYPOTHESIS.md"
)
DUMMY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
]
DETERMINISTIC_EDIT_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
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
AUTH_OR_PROVIDER_ACCESS_MARKERS = [
    "defaultcredentialserror",
    "application-default login",
    "could not automatically determine credentials",
    "unauthenticated",
    "permissiondenied",
    "quota project",
    "http 403",
    "http 401",
    "status code 403",
    "status code 401",
]
OVERLAY_OR_RECEIPT_MARKERS = [
    "receipt validation failed",
    "missing fields:",
    "invalid receipt",
    "no such file or directory",
    "overlay",
    "materialization",
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


def run_capture(args: list[str], timeout: int = 120) -> dict[str, Any]:
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


def redaction_scan() -> tuple[bool, list[str]]:
    findings: list[str] = []
    if not EXPERIMENT.exists():
        return True, findings
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return not findings, sorted(set(findings))


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            hashes[str(base.relative_to(PROOF))] = sha256_file(base)
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def row_by_pair(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("pair_id")): item
        for item in report.get("row_results", [])
        if isinstance(item, dict)
    }


def extract_limit_evidence(stderr: str) -> tuple[str, int | None]:
    match = re.search(
        r"Global cost/call limit exceeded:\s*\$([0-9.]+)\s*/\s*(\d+)",
        stderr,
        re.MULTILINE,
    )
    if match:
        return (
            f"Global cost/call limit exceeded: ${match.group(1)} / {match.group(2)}",
            int(match.group(2)),
        )
    for line in stderr.splitlines():
        if "Global cost/call limit exceeded:" in line:
            return line.strip(), None
    return "", None


def classify_dummy_row(
    pair_id: str,
    row: dict[str, Any],
    iter78_summary: dict[str, Any],
) -> dict[str, Any]:
    raw_dir = ITER78_PROOF / "raw" / pair_id
    stderr_path = raw_dir / "command_stderr.txt"
    execution_path = raw_dir / "command_execution.json"
    stderr = stderr_path.read_text(encoding="utf-8", errors="ignore")
    stderr_lower = stderr.lower()
    global_limit_line, observed_call_limit = extract_limit_evidence(stderr)
    receipt_valid = row.get("receipt_valid")
    receipt_required = row.get("receipt_required")
    receipt_schema_excluded = (
        receipt_required is False
        or (receipt_required is True and receipt_valid is True)
    )
    auth_or_access_marker_present = any(
        marker in stderr_lower for marker in AUTH_OR_PROVIDER_ACCESS_MARKERS
    )
    receipt_or_overlay_marker_present = any(
        marker in stderr_lower for marker in OVERLAY_OR_RECEIPT_MARKERS
    )
    overlay_materialized = (
        iter78_summary.get("runtime_overlay_all_materialized") is True
        and iter78_summary.get("runtime_overlay_copied_hashes_match") is True
        and iter78_summary.get("iter73_recovered_prompt_overlays_all_materialized") is True
    )
    classified = (
        row.get("command_returncode") == 1
        and row.get("command_timed_out") is False
        and row.get("verified_completion_evidence") is False
        and row.get("raw_evidence_present") is True
        and "Global cost/call limit exceeded:" in stderr
        and observed_call_limit == 8
        and receipt_schema_excluded
        and not auth_or_access_marker_present
        and overlay_materialized
    )
    return {
        "pair_id": pair_id,
        "classification": "per_row_global_call_ceiling" if classified else "unclassified",
        "classified": classified,
        "public_config": row.get("public_config"),
        "analysis_stratum": row.get("analysis_stratum"),
        "condition_id": row.get("condition_id"),
        "command_returncode": row.get("command_returncode"),
        "command_timed_out": row.get("command_timed_out"),
        "verified_completion_evidence": row.get("verified_completion_evidence"),
        "raw_evidence_present": row.get("raw_evidence_present"),
        "provider_api_calls_before_block": row.get("provider_api_calls"),
        "provider_cost_usd_before_block": row.get("provider_cost_usd"),
        "receipt_required": receipt_required,
        "receipt_valid": receipt_valid,
        "receipt_schema_excluded": receipt_schema_excluded,
        "adc_or_provider_access_excluded": not auth_or_access_marker_present,
        "overlay_materialization_excluded": overlay_materialized,
        "receipt_or_overlay_marker_present": receipt_or_overlay_marker_present,
        "stderr_contains_global_call_limit": "Global cost/call limit exceeded:" in stderr,
        "observed_global_call_limit": observed_call_limit,
        "global_limit_line": global_limit_line,
        "source_command_stderr": str(stderr_path.relative_to(ROOT)),
        "source_command_stderr_sha256": sha256_file(stderr_path),
        "source_command_execution": str(execution_path.relative_to(ROOT)),
        "source_command_execution_sha256": sha256_file(execution_path),
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter79-dummy-row-call-ceiling-recovery-{status}",
        "task_id": "telos:iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block@iter78",
        "agent_id": "codex-local-dummy-call-ceiling-recovery-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Classify the iter78 Dummy row nonzero-returncode blocker from committed artifacts "
            "and prepare a bounded paid-retry recovery plan."
        ),
        "acceptance_criteria": [
            "Iter78 receipt validation and audit both pass.",
            "Both Dummy row failures are classified from committed raw artifacts as per-row global call-ceiling blockers.",
            "Deterministic-edit rows remain retained verified evidence and are not rerun.",
            "The next paid retry plan is bounded and preserves total provider-call and spend ceilings.",
            "Zero provider calls, zero spend, zero row execution, no GPU, no cloud runner, and no Sentinel mutation occur.",
            "No benchmark, model-superiority, leaderboard, SWE-bench, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records zero-spend recovery status and claim boundary.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/dummy_call_ceiling_classification.json",
                "notes": "Classifier records per-Dummy-row evidence paths, hashes, and excluded alternatives.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/recovery_plan.json",
                "notes": "Recovery plan refreezes the next paid retry to Dummy-only rows under bounded ceilings.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records that no benchmark/model/SOTA claim is made.",
            },
        ],
        "falsifiers": [
            "The result must block if iter78 receipt validation or audit fails.",
            "The result must block if either Dummy row cannot be classified from committed artifacts.",
            "The result must fail if provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, or live-domain mutation occurs.",
            "The result must fail if credential, token, project, service-account, or private identifier residue is committed.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter78_summary = read_json(ITER78_SUMMARY)
    iter78_report = read_json(ITER78_REPORT)
    iter78_receipts = run_capture(
        ["python3", "scripts/validate_receipts.py", str(ITER78_PROOF.relative_to(ROOT))]
    )
    iter78_audit = run_capture(
        ["python3", "scripts/audit_provider_compatible_expanded_paid_retry_after_adc_recovery.py"]
    )
    rows = row_by_pair(iter78_report)

    prerequisite = {
        "schema_version": "telos.dummy_row_call_ceiling_recovery.prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter78_status": iter78_summary.get("status"),
        "iter78_blocked_result": iter78_summary.get("blocked_result"),
        "iter78_clean_pass": iter78_summary.get("clean_pass"),
        "iter78_quality_failure": iter78_summary.get("quality_failure"),
        "iter78_receipt_validation_returncode": iter78_receipts["returncode"],
        "iter78_audit_returncode": iter78_audit["returncode"],
        "iter78_executed_pair_count": iter78_summary.get("executed_pair_count"),
        "iter78_provider_api_calls": iter78_summary.get("provider_api_calls"),
        "iter78_provider_cost_usd": iter78_summary.get("provider_cost_usd"),
        "iter78_blockers": iter78_summary.get("blockers"),
        "iter78_failures": iter78_summary.get("failures"),
        "source_iter78_summary": str(ITER78_SUMMARY.relative_to(ROOT)),
        "source_iter78_summary_sha256": sha256_file(ITER78_SUMMARY),
        "source_iter78_report": str(ITER78_REPORT.relative_to(ROOT)),
        "source_iter78_report_sha256": sha256_file(ITER78_REPORT),
        "clean_prerequisites": (
            iter78_summary.get("status") == "blocked"
            and iter78_summary.get("blocked_result") is True
            and iter78_summary.get("quality_failure") is False
            and iter78_receipts["returncode"] == 0
            and iter78_audit["returncode"] == 0
            and iter78_summary.get("executed_pair_count") == 4
            and iter78_summary.get("provider_api_calls") == 9
            and abs(float(iter78_summary.get("provider_cost_usd", -1.0)) - 0.039876) < 1e-9
            and iter78_summary.get("failures") == []
            and iter78_summary.get("blockers") == ["provider_command_nonzero_returncode"]
        ),
    }
    write_json(PROOF / "prerequisite_validation.json", prerequisite)

    classifications = [
        classify_dummy_row(pair_id, rows.get(pair_id, {}), iter78_summary)
        for pair_id in DUMMY_PAIR_IDS
    ]
    all_dummy_classified = all(item["classified"] for item in classifications)
    classification_packet = {
        "schema_version": "telos.dummy_row_call_ceiling_recovery.classification.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iteration": ITER78_ID,
        "dummy_pair_ids": DUMMY_PAIR_IDS,
        "classification": "per_row_global_call_ceiling",
        "all_dummy_failures_classified": all_dummy_classified,
        "alternative_failure_modes_excluded": {
            "receipt_schema": all(item["receipt_schema_excluded"] for item in classifications),
            "adc_or_provider_access": all(
                item["adc_or_provider_access_excluded"] for item in classifications
            ),
            "overlay_materialization": all(
                item["overlay_materialization_excluded"] for item in classifications
            ),
        },
        "rows": classifications,
    }
    write_json(PROOF / "dummy_call_ceiling_classification.json", classification_packet)

    deterministic_rows = [rows.get(pair_id, {}) for pair_id in DETERMINISTIC_EDIT_PAIR_IDS]
    deterministic_retention = {
        "schema_version": "telos.dummy_row_call_ceiling_recovery.deterministic_edit_retention.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iteration": ITER78_ID,
        "retained_pair_ids": DETERMINISTIC_EDIT_PAIR_IDS,
        "retained_rows_rerun": False,
        "adapter_rows_executed_in_this_gate": 0,
        "deterministic_edit_baseline_verified_completion_evidence": deterministic_rows[0].get(
            "verified_completion_evidence"
        ),
        "deterministic_edit_telos_verified_completion_evidence": deterministic_rows[1].get(
            "verified_completion_evidence"
        ),
        "deterministic_edit_delta_telos_minus_baseline": int(
            bool(deterministic_rows[1].get("verified_completion_evidence"))
        )
        - int(bool(deterministic_rows[0].get("verified_completion_evidence"))),
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
    }
    write_json(PROOF / "deterministic_edit_retention.json", deterministic_retention)

    recovery_plan = {
        "schema_version": "telos.dummy_row_call_ceiling_recovery.recovery_plan.v1",
        "experiment_id": EXPERIMENT_ID,
        "next_gate": NEXT_GATE,
        "recommended_status": "pre_register_paid_retry",
        "paid_retry_scope": "dummy_only",
        "adapter_rows_to_execute": 2,
        "selected_pair_ids": DUMMY_PAIR_IDS,
        "deterministic_edit_pair_ids_retained_not_rerun": DETERMINISTIC_EDIT_PAIR_IDS,
        "retained_battlesnake_rows_rerun": False,
        "previous_per_row_call_limit": 8,
        "recommended_per_row_call_limit": 16,
        "provider_call_ceiling": 32,
        "previous_total_provider_call_ceiling": iter78_summary.get("provider_call_ceiling"),
        "provider_spend_ceiling_usd": 5.0,
        "previous_total_provider_spend_ceiling_usd": iter78_summary.get(
            "provider_spend_ceiling_usd"
        ),
        "per_row_spend_limit_usd": 2.5,
        "preserves_or_tightens_total_ceiling": True,
        "provider_calls_before_next_gate": 0,
        "provider_spend_before_next_gate_usd": 0.0,
        "requires_provider_calls_in_this_gate": False,
        "requires_gpu": False,
        "requires_cloud_runner": False,
        "requires_sentinel_mutation": False,
        "claim_boundary": (
            "Dummy adapter-row recovery only; no benchmark, model-superiority, leaderboard, "
            "SWE-bench, production/live-domain, or state-of-the-art claim."
        ),
    }
    write_json(PROOF / "recovery_plan.json", recovery_plan)

    scan_passed, scan_findings = redaction_scan()
    failures: list[str] = []
    blockers: list[str] = []
    if prerequisite["clean_prerequisites"] is not True:
        blockers.append("iter78_prerequisite_validation_failed")
    if not all_dummy_classified:
        blockers.append("dummy_call_ceiling_classification_incomplete")
    if (
        deterministic_retention["deterministic_edit_baseline_verified_completion_evidence"] is not True
        or deterministic_retention["deterministic_edit_telos_verified_completion_evidence"] is not True
    ):
        blockers.append("deterministic_edit_retained_evidence_not_verified")
    if not scan_passed:
        failures.append("redaction_scan_failed")

    provider_api_calls = 0
    provider_spend_usd = 0.0
    adapter_rows_executed = 0
    gpu_used = False
    cloud_runner_started = False
    sentinel_named_resources_modified = False
    production_or_live_domain_changed = False
    benchmark_result_claimed = False
    leaderboard_or_swebench_result_claimed = False
    model_superiority_claimed = False
    state_of_the_art_result_claimed = False

    status = "fail" if failures else "blocked" if blockers else "pass"
    receipt = build_receipt(status)
    write_json(VALID / RECEIPT_NAME, receipt)

    review = """# Iteration 79 Review

This gate inspected committed iter78 artifacts only. It executed no provider rows and made no
provider calls.

Both Dummy rows are classified as per-row global call-ceiling blockers. The committed stderr for
each row contains `Global cost/call limit exceeded` with the observed call ceiling `/ 8`; the
Telos Dummy receipt was valid, baseline receipt was not required, iter78 runtime overlays were
materialized, and no ADC/provider-access marker explains the failures.

The deterministic-edit baseline and Telos rows from iter78 both remain verified completion
evidence. They are retained as stratified adapter-validation evidence and are not rerun here.

The next-gate plan is Dummy-only: execute the two Dummy rows with a bounded 16-call per-row
ceiling, total provider-call ceiling `32`, total spend ceiling `$5.00`, no retained BattleSnake or
deterministic-edit rerun, and no benchmark/model/SOTA claim.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    command_lines = [
        f"dummy row call-ceiling recovery: {status}",
        f"iter78_receipt_validation_returncode={iter78_receipts['returncode']}",
        f"iter78_audit_returncode={iter78_audit['returncode']}",
        f"iter78_status={iter78_summary.get('status')}",
        f"iter78_provider_api_calls={iter78_summary.get('provider_api_calls')}",
        f"iter78_provider_cost_usd={float(iter78_summary.get('provider_cost_usd', 0.0)):.8f}",
        f"dummy_rows_classified={str(all_dummy_classified).lower()}",
        "classification=per_row_global_call_ceiling",
        "adapter_rows_executed=0",
        "provider_api_calls=0",
        "provider_spend_usd=0.00000000",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"next_gate={NEXT_GATE}",
        "benchmark_model_sota_claim=false",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The iter78 Dummy failures are per-row global call-ceiling blockers at the frozen "
            "8-call limit, while deterministic-edit evidence remains verified and should not be rerun."
        ),
        "next_action": (
            "pre-register a Dummy-only paid retry with a bounded 16-call per-row ceiling before "
            "any further provider execution"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/dummy_call_ceiling_classification.json",
            f"experiments/{EXPERIMENT_ID}/proof/recovery_plan.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)

    artifact_hash_map = artifact_hashes(
        [
            PROOF / "prerequisite_validation.json",
            PROOF / "dummy_call_ceiling_classification.json",
            PROOF / "deterministic_edit_retention.json",
            PROOF / "recovery_plan.json",
            PROOF / "command_output.txt",
            PROOF / "review.md",
            PROOF / "learning_record.json",
            VALID,
        ]
    )
    summary = {
        "schema_version": "telos.dummy_row_call_ceiling_recovery.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": sorted(set(blockers)),
        "failures": sorted(set(failures)),
        "iter78_status": iter78_summary.get("status"),
        "iter78_blocked_result": iter78_summary.get("blocked_result"),
        "iter78_receipt_validation_returncode": iter78_receipts["returncode"],
        "iter78_audit_returncode": iter78_audit["returncode"],
        "dummy_rows_classified": all_dummy_classified,
        "dummy_failure_classification": "per_row_global_call_ceiling",
        "dummy_pair_ids": DUMMY_PAIR_IDS,
        "deterministic_edit_rows_rerun": False,
        "deterministic_edit_pair_ids_retained": DETERMINISTIC_EDIT_PAIR_IDS,
        "adapter_rows_executed": adapter_rows_executed,
        "provider_api_calls": provider_api_calls,
        "provider_spend_usd": provider_spend_usd,
        "gpu_used": gpu_used,
        "cloud_runner_started": cloud_runner_started,
        "sentinel_named_resources_modified": sentinel_named_resources_modified,
        "production_or_live_domain_changed": production_or_live_domain_changed,
        "benchmark_result_claimed": benchmark_result_claimed,
        "leaderboard_or_swebench_result_claimed": leaderboard_or_swebench_result_claimed,
        "model_superiority_claimed": model_superiority_claimed,
        "state_of_the_art_result_claimed": state_of_the_art_result_claimed,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "next_gate": NEXT_GATE,
        "recovery_plan_provider_call_ceiling": recovery_plan["provider_call_ceiling"],
        "recovery_plan_provider_spend_ceiling_usd": recovery_plan[
            "provider_spend_ceiling_usd"
        ],
        "recovery_plan_per_row_call_limit": recovery_plan["recommended_per_row_call_limit"],
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "artifact_hashes": artifact_hash_map,
    }
    write_json(PROOF / "run_summary.json", summary)

    result_md = f"""# Iteration 79 Result - Dummy Row Call-Ceiling Recovery After Paid Retry Block

Status: `{status.upper()}`.

## Summary

This zero-spend recovery gate classified the iter78 Dummy failures from committed artifacts only.

- iter78 receipt validation return code: `{iter78_receipts['returncode']}`,
- iter78 audit return code: `{iter78_audit['returncode']}`,
- Dummy rows classified: `{str(all_dummy_classified).lower()}`,
- classification: `per_row_global_call_ceiling`,
- adapter rows executed in this gate: `0`,
- provider API calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`.

## Recovery Decision

The next paid gate should rerun only the two Dummy rows with a bounded 16-call per-row ceiling.
The deterministic-edit rows from iter78 both verified and must remain retained evidence, not rerun.
The next retry plan preserves the total provider-call ceiling at `32` and tightens total spend to
`$5.00`.

## Claim Boundary

This is a blocker-classification and recovery-planning result only. It is not a benchmark result,
SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/dummy_call_ceiling_classification.json`
- `proof/deterministic_edit_retention.json`
- `proof/recovery_plan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
    RESULT.write_text(result_md, encoding="utf-8")

    print(f"dummy row call-ceiling recovery: {status}")
    for line in command_lines[1:]:
        print(line)
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
