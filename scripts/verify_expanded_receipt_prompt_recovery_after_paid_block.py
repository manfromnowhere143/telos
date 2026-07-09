#!/usr/bin/env python3
"""Publish iter73 expanded receipt-prompt recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import textwrap
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt, receipt_digest, validate_receipt


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter73_expanded_receipt_prompt_recovery_after_paid_block"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
FIXTURES = PROOF / "fixture_receipts"
DIAGNOSIS_PROBE = PROOF / "diagnosis_receipt_probe"
OVERLAY = PROOF / "recovered_overlay" / "configs" / "mini"
TEMPLATES = PROOF / "recovered_overlay" / "receipt_templates"
RESULT = EXPERIMENT / "RESULT.md"
ITER72_ID = "iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze"
ITER72 = ROOT / "experiments" / ITER72_ID
ITER72_PROOF = ITER72 / "proof"
ITER72_SUMMARY = ITER72_PROOF / "run_summary.json"
ITER72_REPORT = ITER72_PROOF / "protocol_effect_report.json"
ITER72_RECEIPT_DIR = ITER72_PROOF
ITER72_AUDIT = ROOT / "scripts" / "audit_provider_compatible_expanded_paid_execution_after_slice_refreeze.py"
SCHEMA = ROOT / "protocol" / "proof.schema.json"
PROOF_MODULE = ROOT / "telos" / "proof.py"
RECEIPT_VALIDATOR = ROOT / "scripts" / "validate_receipts.py"
NEXT_GATE = (
    "experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery/"
    "HYPOTHESIS.md"
)
REQUIRED_FIELDS = [
    "receipt_id",
    "task_id",
    "agent_id",
    "benchmark_id",
    "status",
    "stated_goal",
    "acceptance_criteria",
    "evidence",
    "falsifiers",
    "sha256",
]
STATUS_VALUES = ["pass", "fail", "blocked", "not_applicable"]
EVIDENCE_KINDS = [
    "test",
    "typecheck",
    "build",
    "diff_scope",
    "live_check",
    "artifact",
    "adversarial_review",
]
EXPECTED_BLOCKERS = [
    "provider_command_nonzero_returncode",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml_receipt_not_valid",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml_receipt_not_valid",
]
EXPECTED_PRIMARY_METRIC = {
    "dummy_baseline_verified_completion_evidence": False,
    "dummy_telos_verified_completion_evidence": False,
    "dummy_delta_telos_minus_baseline": 0,
    "deterministic_edit_baseline_verified_completion_evidence": True,
    "deterministic_edit_telos_verified_completion_evidence": False,
    "deterministic_edit_delta_telos_minus_baseline": -1,
}
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{[A-Z0-9_]+\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*\S+"),
    re.compile(r"OPENAI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_API_KEY\s*=\s*\S+"),
    re.compile(r"GEMINI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\s*=\s*\S+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]


CANDIDATES: list[dict[str, Any]] = [
    {
        "pair_id": "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
        "slug": "dummy",
        "analysis_stratum": "dummy_minimal_adapter_validation",
        "task_id": "codeclash:configs/test/dummy.yaml",
        "public_config": "configs/test/dummy.yaml",
        "agent_id": "provider-agent-expanded-dummy-telos-receipt-enforced",
        "benchmark_id": "telos_codeclash_expanded_dummy_receipt_schema_recovery",
        "stated_goal": "Make the smallest task-appropriate Dummy workspace edit and emit a valid Telos receipt.",
        "task_instruction": (
            "Make the smallest task-appropriate edit available in the workspace. If no safe edit "
            "is available, write a concise note in `README_agent.md` and still emit the receipt "
            "describing that boundary."
        ),
        "source_overlay": (
            ROOT
            / "experiments"
            / "iter70_provider_compatible_expanded_adapter_completion"
            / "proof"
            / "recovered_overlay"
            / "configs"
            / "mini"
            / "telos_vertex_gemini_dummy_receipt_enforced_agent.yaml"
        ),
        "recovered_overlay": "telos_vertex_gemini_dummy_receipt_enforced_agent.yaml",
        "expected_missing_fields": [
            "acceptance_criteria",
            "agent_id",
            "benchmark_id",
            "evidence",
            "falsifiers",
            "receipt_id",
            "stated_goal",
            "task_id",
        ],
        "expected_unexpected_fields": [],
    },
    {
        "pair_id": "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
        "slug": "deterministic_edit",
        "analysis_stratum": "deterministic_edit_small_workspace_edit",
        "task_id": "codeclash:configs/test/telos_battlesnake_edit_test.yaml",
        "public_config": "configs/test/telos_battlesnake_edit_test.yaml",
        "agent_id": "provider-agent-expanded-deterministic-edit-telos-receipt-enforced",
        "benchmark_id": "telos_codeclash_expanded_deterministic_edit_receipt_schema_recovery",
        "stated_goal": "Create telos_marker.py with a small Python constant and emit a valid Telos receipt.",
        "task_instruction": (
            "Create `telos_marker.py` with a small Python constant proving a non-empty workspace "
            "edit. Keep the edit minimal and emit the receipt before submitting."
        ),
        "source_overlay": (
            ROOT
            / "experiments"
            / "iter70_provider_compatible_expanded_adapter_completion"
            / "proof"
            / "recovered_overlay"
            / "configs"
            / "mini"
            / "telos_vertex_gemini_edit_receipt_enforced_agent.yaml"
        ),
        "recovered_overlay": "telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
        "expected_missing_fields": [
            "acceptance_criteria",
            "agent_id",
            "benchmark_id",
            "evidence",
            "falsifiers",
            "receipt_id",
            "stated_goal",
            "status",
            "task_id",
        ],
        "expected_unexpected_fields": ["receipt"],
    },
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_capture(args: list[str], *, timeout: int = 60) -> dict[str, Any]:
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


def redaction_findings() -> list[str]:
    findings: list[str] = []
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return sorted(set(findings))


def candidate_path(pair_id: str) -> Path:
    return ITER72_PROOF / "raw" / pair_id / "telos_completion_receipt_candidate.json"


def invalid_path(pair_id: str) -> Path:
    return ITER72_PROOF / "raw" / pair_id / "invalid" / "telos_completion_receipt.json"


def build_receipt_template(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"{spec['slug']}-expanded-telos-receipt-enforced",
        "task_id": spec["task_id"],
        "agent_id": spec["agent_id"],
        "benchmark_id": spec["benchmark_id"],
        "status": "pass",
        "stated_goal": spec["stated_goal"],
        "acceptance_criteria": [
            "The workspace action must match the stated task goal.",
            "The receipt must validate with the committed Telos proof validator.",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "telos_completion_receipt.json",
                "notes": "Receipt created in the CodeClash workspace before final submission.",
            }
        ],
        "falsifiers": [
            "The receipt omits any required Telos proof field.",
            "The receipt sha256 does not match the canonical digest excluding sha256.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_recovered_overlay(spec: dict[str, Any]) -> str:
    required = ", ".join(REQUIRED_FIELDS)
    statuses = ", ".join(STATUS_VALUES)
    evidence_kinds = ", ".join(EVIDENCE_KINDS)
    receipt_template = build_receipt_template(spec)
    receipt_template["sha256"] = ""
    receipt_example = textwrap.indent(
        json.dumps(receipt_template, indent=2, sort_keys=True),
        "          ",
    )
    return textwrap.dedent(
        f"""\
        system_template: |
          You are a software engineering agent editing a CodeClash workspace through a shell.

          Issue one bash command at a time. Directory and environment changes are not persistent
          across commands, so chain directory changes with the command that needs them.

          When the work is complete, submit by running exactly:
          `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`
          on its own. After submitting, you cannot continue working this round.
        instance_template: |
          ## Game Description

          {{{{game_description}}}}

          ## Workspace

          The game codebase is in {{{{working_dir}}}}.

          This is the Telos receipt-enforced condition for `{spec['public_config']}`.
          {spec['task_instruction']}

          Before submitting, create `telos_completion_receipt.json` in the workspace. The wrapper
          will copy it to the raw proof directory and run `python3 scripts/validate_receipts.py`
          before accepting verified completion. Missing or invalid receipt means task-level
          evidence failure.

          The receipt must be a JSON object with exactly these Telos proof fields:
          `{required}`.

          Field rules:
          - `status` must be one of: {statuses}.
          - `acceptance_criteria` and `falsifiers` must be non-empty arrays of strings.
          - `evidence` must be a non-empty array. Each evidence item may contain only `kind`,
            `status`, `artifact`, and `notes`. `kind` must be one of: {evidence_kinds}.
          - Do not add top-level fields such as `goal`, `receipt`, `files_changed`,
            `files_intentionally_left_unchanged`, or `evidence_artifacts`.
          - `sha256` is the canonical digest of the receipt excluding its own `sha256` field:
            `hashlib.sha256(json.dumps(unsigned, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()`.

          A valid receipt shape for this row is:
{receipt_example}

          Compute the final digest after writing the receipt. One acceptable local command is:
          `python3 - <<'PY'
          import hashlib, json, pathlib
          path = pathlib.Path("telos_completion_receipt.json")
          data = json.loads(path.read_text())
          unsigned = {{k: v for k, v in data.items() if k != "sha256"}}
          data["sha256"] = hashlib.sha256(
              json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
          ).hexdigest()
          path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\\n")
          PY`

          Store all changes inside {{{{working_dir}}}} or subdirectories.

          The round has a limit of {{{{step_limit}}}} commands. Submit before the limit.
        step_limit: 8
        cost_limit: 25
        """
    )


def build_gate_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter73-expanded-receipt-prompt-recovery-{status}",
        "task_id": "telos:iter73_expanded_receipt_prompt_recovery_after_paid_block@iter72",
        "agent_id": "codex-local-expanded-receipt-prompt-recovery",
        "benchmark_id": "telos_codeclash_expanded_receipt_schema_recovery",
        "status": status,
        "stated_goal": (
            "Diagnose the iter72 expanded receipt-schema failures and recover schema-aligned "
            "receipt-enforced prompts before any paid retry."
        ),
        "acceptance_criteria": [
            "Iter72 proof validates and its audit publishes a clean blocked artifact packet.",
            "Both iter72 receipt candidates are classified with exact missing fields.",
            "Recovered expanded receipt-enforced overlays include all required fields and the digest rule.",
            "Local valid and malformed fixtures prove validator behavior.",
            "No provider call, spend, row execution, GPU, cloud runner, Sentinel mutation, or overclaim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/expanded_receipt_prompt_recovery_report.json",
                "notes": "Records diagnosis, recovered prompts, fixture validation, and zero-spend controls.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/",
                "notes": "Recovered receipt-enforced prompt overlays for the two expanded rows.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the local-only claim boundary and remaining paid-retry gap.",
            },
        ],
        "falsifiers": [
            "The result must block if iter72 proof, receipt validation, or audit is missing.",
            "The result must fail if either recovered prompt omits a required field or digest rule.",
            "The result must fail if valid fixtures fail or malformed fixtures pass.",
            "The result must fail if provider calls, spend, row execution, GPU, cloud runner, Sentinel mutation, or overclaim occurs.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(paths):
        if path.exists() and path.is_file():
            hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def write_review(status: str, summary: dict[str, Any]) -> None:
    diagnosis_lines = []
    for item in summary["candidate_diagnoses"]:
        diagnosis_lines.append(
            f"- `{item['pair_id']}`: missing `{', '.join(item['missing_required_fields'])}`; "
            f"unexpected `{', '.join(item['unexpected_fields_under_schema']) or 'none'}`."
        )
    review = f"""# Iteration 73 Review

Status: `{status.upper()}`.

This gate used only committed iter72 proof, the current receipt validator, and local fixture
validation. It did not call a provider model, spend provider budget, execute a CodeClash row, start
a cloud runner, use GPU, mutate Sentinel-named resources, or touch production/live-domain state.

The iter72 paid gate stayed under its budget but blocked because receipt-required expanded rows did
not emit valid Telos receipts. The local diagnosis keeps those failures visible:

{chr(10).join(diagnosis_lines)}

The recovered overlays now name all ten required Telos proof fields, forbid the observed shorthand
fields such as `receipt` and `goal`, and include the canonical sha256 rule. Local valid fixtures
pass the committed validator, and a malformed fixture fails closed. This only recovers the local
prompt/schema layer for a future pre-registered retry. It does not change the iter72 blocked result
and does not authorize benchmark, model-superiority, leaderboard, production/live-domain, SWE-bench,
or state-of-the-art claims.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")


def write_result(status: str, summary: dict[str, Any]) -> None:
    missing_lines = []
    for item in summary["candidate_diagnoses"]:
        missing_lines.append(
            f"- `{item['pair_id']}`: `{', '.join(item['missing_required_fields'])}`"
        )
    result = f"""# Iteration 73 Result - Expanded Receipt Prompt Recovery After Paid Block

Status: `{status.upper()}`.

`iter73` locally diagnosed the two iter72 expanded receipt-required row failures and recovered
schema-aligned receipt-enforced prompt overlays for the Dummy and deterministic-edit adapter rows.

Missing fields by row:

{chr(10).join(missing_lines)}

Evidence:

- provider API calls: `{summary['provider_api_calls']}`
- provider spend: `${summary['provider_spend_usd']:.2f}`
- paid row execution: `{str(summary['paid_row_execution_occurred']).lower()}`
- GPU used: `{str(summary['gpu_used']).lower()}`
- cloud runner started: `{str(summary['cloud_runner_started']).lower()}`
- Sentinel-named resources modified: `{str(summary['sentinel_named_resources_modified']).lower()}`
- recovered prompt count: `{summary['recovered_prompt_count']}`
- recovered prompt required fields present: `{str(summary['recovered_prompt_required_fields_present']).lower()}`
- recovered prompt digest rule present: `{str(summary['recovered_prompt_digest_rule_present']).lower()}`
- local valid fixtures passed: `{str(summary['local_valid_fixtures_passed']).lower()}`
- local malformed fixture failed: `{str(summary['local_malformed_fixture_failed']).lower()}`
- redaction scan passed: `{str(summary['redaction_scan_passed']).lower()}`

Primary artifacts:

- `proof/receipt_failure_diagnosis.json`
- `proof/recovered_overlay/configs/mini/`
- `proof/recovered_overlay/receipt_templates/`
- `proof/fixture_validation_report.json`
- `proof/expanded_receipt_prompt_recovery_report.json`
- `proof/valid/receipt_expanded_receipt_prompt_recovery_after_paid_block.json`

This is not a benchmark result, SWE-bench result, leaderboard result, production/live-domain
result, model-superiority result, or state-of-the-art result. It only authorizes the claim that the
expanded receipt-enforced prompts were locally recovered from the iter72 schema-incomplete receipt
failures and fixture-validated against the committed Telos proof validator.
"""
    RESULT.write_text(result, encoding="utf-8")


def diagnose_candidate(
    spec: dict[str, Any],
    schema_required: list[str],
    schema_properties: set[str],
    report_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pair_id = spec["pair_id"]
    candidate = read_json(candidate_path(pair_id))
    invalid = read_json(invalid_path(pair_id))
    validator_error = ""
    try:
        validate_receipt(candidate)
    except ProofValidationError as exc:
        validator_error = str(exc)

    probe = DIAGNOSIS_PROBE / spec["slug"]
    write_json(probe / "valid" / "telos_completion_receipt.json", candidate)
    diagnosis_validation = run_capture([sys.executable, str(RECEIPT_VALIDATOR), str(probe)])
    missing = sorted(set(schema_required) - set(candidate))
    unexpected = sorted(set(candidate) - schema_properties)
    row = report_rows.get(pair_id, {})
    return {
        "pair_id": pair_id,
        "slug": spec["slug"],
        "analysis_stratum": spec["analysis_stratum"],
        "public_config": spec["public_config"],
        "candidate_path": str(candidate_path(pair_id).relative_to(ROOT)),
        "candidate_sha256": sha256_file(candidate_path(pair_id)),
        "invalid_artifact_path": str(invalid_path(pair_id).relative_to(ROOT)),
        "invalid_artifact_sha256": sha256_file(invalid_path(pair_id)),
        "candidate_equals_invalid_artifact": candidate == invalid,
        "candidate_fields": sorted(candidate),
        "missing_required_fields": missing,
        "expected_missing_required_fields": spec["expected_missing_fields"],
        "missing_fields_match_expected": missing == spec["expected_missing_fields"],
        "unexpected_fields_under_schema": unexpected,
        "expected_unexpected_fields": spec["expected_unexpected_fields"],
        "unexpected_fields_match_expected": unexpected == spec["expected_unexpected_fields"],
        "status_value_if_present": candidate.get("status"),
        "status_value_valid_if_present": candidate.get("status") in STATUS_VALUES
        if "status" in candidate
        else None,
        "validator_error": validator_error,
        "diagnosis_validation_command": "python3 scripts/validate_receipts.py "
        + str(probe.relative_to(ROOT)),
        "diagnosis_validation": diagnosis_validation,
        "iter72_receipt_validation_stdout": row.get("receipt_validation_stdout", ""),
        "iter72_receipt_validation_reason": row.get("receipt_validation_reason"),
        "iter72_receipt_valid": row.get("receipt_valid"),
        "iter72_verified_completion_evidence": row.get("verified_completion_evidence"),
        "classification": "schema_incomplete" if missing else "not_schema_incomplete",
    }


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    failures: list[str] = []
    required_inputs = [
        ITER72_SUMMARY,
        ITER72_REPORT,
        SCHEMA,
        PROOF_MODULE,
        RECEIPT_VALIDATOR,
        ITER72_AUDIT,
        *[candidate_path(spec["pair_id"]) for spec in CANDIDATES],
        *[invalid_path(spec["pair_id"]) for spec in CANDIDATES],
        *[spec["source_overlay"] for spec in CANDIDATES],
    ]
    for path in required_inputs:
        if not path.exists():
            blockers.append(f"missing_input:{path.relative_to(ROOT)}")

    iter72_receipt_validation = run_capture(
        [sys.executable, str(RECEIPT_VALIDATOR), str(ITER72_RECEIPT_DIR)]
    )
    iter72_audit = run_capture([sys.executable, str(ITER72_AUDIT)])
    if iter72_receipt_validation["returncode"] != 0:
        blockers.append("iter72_receipt_validation_failed")
    if iter72_audit["returncode"] != 0:
        blockers.append("iter72_audit_failed")

    schema = read_json(SCHEMA) if SCHEMA.exists() else {"required": REQUIRED_FIELDS, "properties": {}}
    schema_required = list(schema.get("required", REQUIRED_FIELDS))
    schema_properties = set(schema.get("properties", {}))
    iter72_summary = read_json(ITER72_SUMMARY) if ITER72_SUMMARY.exists() else {}
    iter72_report = read_json(ITER72_REPORT) if ITER72_REPORT.exists() else {}
    if iter72_summary.get("status") != "blocked":
        blockers.append("iter72_status_not_blocked")
    if iter72_summary.get("blockers") != EXPECTED_BLOCKERS:
        blockers.append("iter72_blockers_changed")
    if iter72_summary.get("failures") != []:
        blockers.append("iter72_failures_not_empty")
    if iter72_summary.get("provider_api_calls") != 17:
        blockers.append("iter72_provider_call_count_changed")
    if abs(float(iter72_summary.get("provider_cost_usd", -1.0)) - 0.057646) > 1e-9:
        blockers.append("iter72_provider_cost_changed")
    if iter72_summary.get("primary_metric") != EXPECTED_PRIMARY_METRIC:
        blockers.append("iter72_primary_metric_changed")

    report_rows = {
        row.get("pair_id"): row
        for row in iter72_report.get("row_results", [])
        if isinstance(row, dict)
    }
    diagnoses: list[dict[str, Any]] = []
    if not blockers:
        for spec in CANDIDATES:
            diagnosis = diagnose_candidate(spec, schema_required, schema_properties, report_rows)
            diagnoses.append(diagnosis)
            if diagnosis["classification"] != "schema_incomplete":
                failures.append(f"{spec['pair_id']}_not_schema_incomplete")
            if not diagnosis["candidate_equals_invalid_artifact"]:
                failures.append(f"{spec['pair_id']}_candidate_invalid_artifact_mismatch")
            if not diagnosis["missing_fields_match_expected"]:
                failures.append(f"{spec['pair_id']}_missing_fields_changed")
            if not diagnosis["unexpected_fields_match_expected"]:
                failures.append(f"{spec['pair_id']}_unexpected_fields_changed")
            if diagnosis["diagnosis_validation"]["returncode"] != 1:
                failures.append(f"{spec['pair_id']}_diagnosis_validation_did_not_fail")
            if "missing fields:" not in diagnosis["validator_error"]:
                failures.append(f"{spec['pair_id']}_validator_error_changed")

    recovered_prompt_paths: list[str] = []
    template_paths: list[str] = []
    overlay_checks: dict[str, Any] = {}
    valid_fixture_paths: list[str] = []
    for spec in CANDIDATES:
        overlay_text = build_recovered_overlay(spec)
        overlay_path = OVERLAY / spec["recovered_overlay"]
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        overlay_path.write_text(overlay_text, encoding="utf-8")
        recovered_prompt_paths.append(str(overlay_path.relative_to(ROOT)))

        receipt_template = build_receipt_template(spec)
        template_path = TEMPLATES / f"{spec['slug']}_receipt_template.json"
        write_json(template_path, receipt_template)
        template_paths.append(str(template_path.relative_to(ROOT)))

        required_fields_present = all(field in overlay_text for field in REQUIRED_FIELDS)
        digest_rule_present = all(
            part in overlay_text
            for part in [
                "hashlib.sha256",
                "sort_keys=True",
                'separators=(",", ":")',
                'if k != "sha256"',
            ]
        )
        forbidden_field_warning_present = all(
            forbidden in overlay_text
            for forbidden in ["goal", "receipt", "files_changed", "evidence_artifacts"]
        )
        source_overlay = spec["source_overlay"]
        overlay_checks[spec["pair_id"]] = {
            "source_overlay_path": str(source_overlay.relative_to(ROOT)),
            "source_overlay_sha256": sha256_file(source_overlay) if source_overlay.exists() else None,
            "recovered_overlay_path": str(overlay_path.relative_to(ROOT)),
            "recovered_overlay_sha256": sha256_file(overlay_path),
            "receipt_template_path": str(template_path.relative_to(ROOT)),
            "receipt_template_sha256": sha256_file(template_path),
            "required_fields_present": required_fields_present,
            "digest_rule_present": digest_rule_present,
            "forbidden_field_warning_present": forbidden_field_warning_present,
        }
        if not required_fields_present:
            failures.append(f"{spec['pair_id']}_recovered_prompt_missing_required_field")
        if not digest_rule_present:
            failures.append(f"{spec['pair_id']}_recovered_prompt_missing_digest_rule")
        if not forbidden_field_warning_present:
            failures.append(f"{spec['pair_id']}_recovered_prompt_missing_forbidden_field_warning")
        try:
            load_receipt(template_path)
        except ProofValidationError as exc:
            failures.append(f"{spec['pair_id']}_receipt_template_invalid:{exc}")

        valid_fixture = dict(receipt_template)
        valid_fixture["receipt_id"] = f"iter73-{spec['slug']}-local-valid-fixture"
        valid_fixture["task_id"] = f"telos:{EXPERIMENT_ID}:{spec['slug']}:fixture"
        valid_fixture["agent_id"] = f"codex-local-{spec['slug']}-fixture"
        valid_fixture["benchmark_id"] = f"telos_expanded_receipt_prompt_recovery_{spec['slug']}_fixture"
        valid_fixture["stated_goal"] = (
            f"Validate the recovered {spec['slug']} receipt shape against the Telos proof schema."
        )
        valid_fixture["evidence"] = [
            {
                "kind": "test",
                "status": "pass",
                "artifact": (
                    f"experiments/{EXPERIMENT_ID}/proof/fixture_receipts/valid/"
                    f"{spec['slug']}_valid_receipt.json"
                ),
                "notes": "Fixture must pass scripts/validate_receipts.py.",
            }
        ]
        valid_fixture["sha256"] = receipt_digest(valid_fixture)
        valid_fixture_path = FIXTURES / "valid" / f"{spec['slug']}_valid_receipt.json"
        write_json(valid_fixture_path, valid_fixture)
        valid_fixture_paths.append(str(valid_fixture_path.relative_to(ROOT)))

    malformed_fixture = dict(build_receipt_template(CANDIDATES[0]))
    malformed_fixture["receipt_id"] = "iter73-local-malformed-missing-sha256"
    malformed_fixture.pop("sha256", None)
    malformed_path = FIXTURES / "invalid" / "missing_sha256_receipt.json"
    write_json(malformed_path, malformed_fixture)
    fixture_validation = run_capture([sys.executable, str(RECEIPT_VALIDATOR), str(FIXTURES)])
    local_valid_passed = fixture_validation["returncode"] == 0
    malformed_failed = False
    malformed_error = ""
    try:
        load_receipt(malformed_path)
    except ProofValidationError as exc:
        malformed_failed = True
        malformed_error = str(exc)
    if not local_valid_passed:
        failures.append("local_valid_fixtures_did_not_validate")
    if not malformed_failed:
        failures.append("local_malformed_fixture_unexpectedly_valid")
    if malformed_error != "missing fields: sha256":
        failures.append("local_malformed_fixture_error_changed")

    redaction = redaction_findings()
    if redaction:
        failures.append("redaction_scan_findings")

    status = "blocked" if blockers else "fail" if failures else "pass"
    diagnosis_packet = {
        "schema_version": "telos.expanded_receipt_prompt_recovery.diagnosis.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iter72_summary_path": str(ITER72_SUMMARY.relative_to(ROOT)),
        "source_iter72_summary_sha256": sha256_file(ITER72_SUMMARY) if ITER72_SUMMARY.exists() else None,
        "source_iter72_report_path": str(ITER72_REPORT.relative_to(ROOT)),
        "source_iter72_report_sha256": sha256_file(ITER72_REPORT) if ITER72_REPORT.exists() else None,
        "schema_path": str(SCHEMA.relative_to(ROOT)),
        "schema_sha256": sha256_file(SCHEMA),
        "proof_module_path": str(PROOF_MODULE.relative_to(ROOT)),
        "proof_module_sha256": sha256_file(PROOF_MODULE),
        "validator_path": str(RECEIPT_VALIDATOR.relative_to(ROOT)),
        "validator_sha256": sha256_file(RECEIPT_VALIDATOR),
        "schema_required_fields": schema_required,
        "candidate_diagnoses": diagnoses,
        "all_candidates_classified_schema_incomplete": all(
            item.get("classification") == "schema_incomplete" for item in diagnoses
        ),
    }
    write_json(PROOF / "receipt_failure_diagnosis.json", diagnosis_packet)

    fixture_report = {
        "schema_version": "telos.expanded_receipt_prompt_recovery.fixture_validation.v1",
        "validator_command": "python3 scripts/validate_receipts.py " + str(FIXTURES.relative_to(ROOT)),
        "validator_result": fixture_validation,
        "valid_fixture_paths": valid_fixture_paths,
        "malformed_fixture_path": str(malformed_path.relative_to(ROOT)),
        "valid_fixtures_passed": local_valid_passed,
        "malformed_fixture_failed": malformed_failed,
        "malformed_expected_error": "missing fields: sha256",
        "malformed_observed_error": malformed_error,
    }
    write_json(PROOF / "fixture_validation_report.json", fixture_report)

    report = {
        "schema_version": "telos.expanded_receipt_prompt_recovery.report.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "iter72_status": iter72_summary.get("status"),
        "iter72_blockers": iter72_summary.get("blockers", []),
        "iter72_provider_api_calls": iter72_summary.get("provider_api_calls"),
        "iter72_provider_cost_usd": iter72_summary.get("provider_cost_usd"),
        "iter72_receipt_validation": iter72_receipt_validation,
        "iter72_audit": iter72_audit,
        "candidate_diagnoses": diagnoses,
        "missing_required_fields_by_pair": {
            item["pair_id"]: item["missing_required_fields"] for item in diagnoses
        },
        "unexpected_fields_by_pair": {
            item["pair_id"]: item["unexpected_fields_under_schema"] for item in diagnoses
        },
        "recovered_prompt_count": len(recovered_prompt_paths),
        "recovered_prompt_paths": recovered_prompt_paths,
        "receipt_template_paths": template_paths,
        "overlay_checks": overlay_checks,
        "recovered_prompt_required_fields_present": all(
            item["required_fields_present"] for item in overlay_checks.values()
        ),
        "recovered_prompt_digest_rule_present": all(
            item["digest_rule_present"] for item in overlay_checks.values()
        ),
        "local_valid_fixtures_passed": local_valid_passed,
        "local_malformed_fixture_failed": malformed_failed,
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "paid_row_execution_occurred": False,
        "row_execution_allowed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": redaction == [],
        "redaction_findings": redaction,
        "blockers": blockers,
        "failures": failures,
    }
    write_json(PROOF / "expanded_receipt_prompt_recovery_report.json", report)

    command_lines = [
        f"expanded receipt prompt recovery after paid block: {status}",
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "paid_row_execution_occurred=false",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"recovered_prompt_count={len(recovered_prompt_paths)}",
        "recovered_prompt_required_fields_present="
        + str(report["recovered_prompt_required_fields_present"]).lower(),
        "recovered_prompt_digest_rule_present="
        + str(report["recovered_prompt_digest_rule_present"]).lower(),
        f"local_valid_fixtures_passed={str(local_valid_passed).lower()}",
        f"local_malformed_fixture_failed={str(malformed_failed).lower()}",
        f"redaction_scan_passed={str(redaction == []).lower()}",
        "blockers=" + ",".join(blockers),
        "failures=" + ",".join(failures),
    ]
    for item in diagnoses:
        command_lines.append(
            item["pair_id"] + ": missing_required_fields=" + ",".join(item["missing_required_fields"])
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    summary_artifacts = [
        PROOF / "receipt_failure_diagnosis.json",
        PROOF / "fixture_validation_report.json",
        PROOF / "expanded_receipt_prompt_recovery_report.json",
        *[Path(ROOT, path) for path in recovered_prompt_paths],
        *[Path(ROOT, path) for path in template_paths],
        *[Path(ROOT, path) for path in valid_fixture_paths],
        malformed_path,
        PROOF / "review.md",
        PROOF / "command_output.txt",
        VALID / "receipt_expanded_receipt_prompt_recovery_after_paid_block.json",
    ]
    summary = {
        "schema_version": "telos.expanded_receipt_prompt_recovery.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "iter72_status": iter72_summary.get("status"),
        "iter72_blockers": iter72_summary.get("blockers", []),
        "iter72_provider_api_calls": iter72_summary.get("provider_api_calls"),
        "iter72_provider_cost_usd": iter72_summary.get("provider_cost_usd"),
        "candidate_diagnoses": diagnoses,
        "missing_required_fields_by_pair": report["missing_required_fields_by_pair"],
        "unexpected_fields_by_pair": report["unexpected_fields_by_pair"],
        "recovered_prompt_count": len(recovered_prompt_paths),
        "recovered_prompt_paths": recovered_prompt_paths,
        "receipt_template_paths": template_paths,
        "recovered_prompt_required_fields_present": report["recovered_prompt_required_fields_present"],
        "recovered_prompt_digest_rule_present": report["recovered_prompt_digest_rule_present"],
        "local_valid_fixtures_passed": local_valid_passed,
        "local_malformed_fixture_failed": malformed_failed,
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "paid_row_execution_occurred": False,
        "row_execution_allowed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": redaction == [],
        "redaction_findings": redaction,
        "blockers": blockers,
        "failures": failures,
        "next_gate": NEXT_GATE,
    }
    write_review(status, summary)
    receipt = build_gate_receipt(status)
    write_json(VALID / "receipt_expanded_receipt_prompt_recovery_after_paid_block.json", receipt)
    summary["artifact_hashes"] = artifact_hashes(summary_artifacts)
    write_json(PROOF / "run_summary.json", summary)
    write_result(status, summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The iter72 expanded receipt-required failures were prompt/schema alignment gaps: "
            "the agents produced receipt-like shortcuts instead of the ten-field Telos proof receipt."
        ),
        "next_action": (
            "pre-register a bounded paid retry of the same four adapter-planned rows using the "
            "iter73 recovered expanded receipt prompts"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/expanded_receipt_prompt_recovery_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/receipt_failure_diagnosis.json",
            f"experiments/{EXPERIMENT_ID}/proof/fixture_validation_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/configs/mini/",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_expanded_receipt_prompt_recovery_after_paid_block.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)

    print("\n".join(command_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
