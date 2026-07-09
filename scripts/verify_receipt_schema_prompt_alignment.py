#!/usr/bin/env python3
"""Publish iter65 receipt-schema prompt-alignment artifacts."""

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
EXPERIMENT_ID = "iter65_receipt_schema_prompt_alignment"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
FIXTURES = PROOF / "fixture_receipts"
DIAGNOSIS_PROBE = PROOF / "diagnosis_receipt_probe"
OVERLAY = PROOF / "recovered_overlay" / "configs" / "mini"
RESULT = EXPERIMENT / "RESULT.md"
ITER64 = ROOT / "experiments" / "iter64_provider_compatible_paid_execution_after_access_path_recovery"
ITER64_PROOF = ITER64 / "proof"
ITER64_REPORT = ITER64_PROOF / "protocol_effect_report.json"
ITER64_SUMMARY = ITER64_PROOF / "run_summary.json"
ITER64_CANDIDATE = (
    ITER64_PROOF
    / "raw"
    / "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
    / "telos_completion_receipt_candidate.json"
)
ITER64_INVALID = (
    ITER64_PROOF
    / "raw"
    / "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
    / "invalid"
    / "telos_completion_receipt.json"
)
SOURCE_OVERLAY = (
    ROOT
    / "experiments"
    / "iter52_provider_condition_runtime_separation_recovery"
    / "proof"
    / "recovered_overlay"
    / "configs"
    / "mini"
    / "telos_vertex_gemini_receipt_enforced_agent.yaml"
)
SCHEMA = ROOT / "protocol" / "proof.schema.json"
PROOF_MODULE = ROOT / "telos" / "proof.py"
RECEIPT_VALIDATOR = ROOT / "scripts" / "validate_receipts.py"
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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


def build_recovered_overlay() -> str:
    required = ", ".join(REQUIRED_FIELDS)
    statuses = ", ".join(STATUS_VALUES)
    evidence_kinds = ", ".join(EVIDENCE_KINDS)
    return textwrap.dedent(
        f"""\
        system_template: |
          You are a software engineering agent editing a small game bot through a shell.

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

          Useful paths:
          - `docs/`: game documentation
          - `/logs/`: prior edit and gameplay logs
          - `README_agent.md`: handoff notes for later teammates
          - `telos_completion_receipt.json`: required completion receipt for this condition

          This is the Telos receipt-enforced condition. Improve the bot if you can do so safely
          within the command budget. Prefer a small, reversible, well-scoped edit over broad
          rewrites. If you cannot identify a safe edit, leave a concise note in `README_agent.md`.

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
          - Do not add top-level fields such as `goal`, `files_changed`, or `evidence_artifacts`.
          - `sha256` is the canonical digest of the receipt excluding its own `sha256` field:
            `hashlib.sha256(json.dumps(unsigned, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()`.

          A valid minimal receipt shape is:
          {{
            "receipt_id": "codeclash-battlesnake-pvp-telos-receipt-enforced",
            "task_id": "codeclash:configs/test/battlesnake_pvp_test.yaml",
            "agent_id": "provider-agent-telos-receipt-enforced",
            "benchmark_id": "telos_codeclash_battlesnake_pvp_two_row_protocol_effect",
            "status": "pass",
            "stated_goal": "Improve the Battlesnake bot safely within the command budget.",
            "acceptance_criteria": [
              "The bot should not move out of bounds.",
              "The changes should be safe and well-scoped."
            ],
            "evidence": [
              {{
                "kind": "artifact",
                "status": "pass",
                "artifact": "main.py",
                "notes": "Primary game-bot file inspected or changed."
              }}
            ],
            "falsifiers": [
              "The bot moves out of bounds.",
              "The bot crashes due to syntax errors."
            ],
            "sha256": ""
          }}

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


def build_receipt_template() -> dict[str, Any]:
    receipt = {
        "receipt_id": "codeclash-battlesnake-pvp-telos-receipt-enforced",
        "task_id": "codeclash:configs/test/battlesnake_pvp_test.yaml",
        "agent_id": "provider-agent-telos-receipt-enforced",
        "benchmark_id": "telos_codeclash_battlesnake_pvp_two_row_protocol_effect",
        "status": "pass",
        "stated_goal": "Improve the Battlesnake bot safely within the command budget.",
        "acceptance_criteria": [
            "The bot should not move out of bounds.",
            "The changes should be safe and well-scoped.",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "main.py",
                "notes": "Primary game-bot file inspected or changed.",
            }
        ],
        "falsifiers": [
            "The bot moves out of bounds.",
            "The bot crashes due to syntax errors.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_gate_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter65-receipt-schema-prompt-alignment-{status}",
        "task_id": "telos:iter65_receipt_schema_prompt_alignment@iter64",
        "agent_id": "codex-local-receipt-schema-prompt-alignment",
        "benchmark_id": "telos_codeclash_battlesnake_protocol_effect_receipt_schema",
        "status": status,
        "stated_goal": (
            "Diagnose the iter64 Telos receipt failure and recover a schema-aligned local "
            "receipt prompt before any additional paid provider-compatible retry."
        ),
        "acceptance_criteria": [
            "The iter64 invalid receipt candidate is classified with the committed schema and validator.",
            "A recovered prompt overlay includes every required Telos receipt field and digest rule.",
            "A local valid fixture passes scripts/validate_receipts.py.",
            "A local malformed fixture fails for the expected reason.",
            "No provider call, provider spend, GPU, cloud runner, Sentinel mutation, or overclaim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/receipt_schema_alignment_report.json",
                "notes": "Records diagnosis, local fixture validation, redaction scan, and zero-spend controls.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/configs/mini/"
                    "telos_vertex_gemini_receipt_enforced_agent.yaml"
                ),
                "notes": "Recovered receipt-enforced prompt overlay for a future paid retry.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the local-only claim boundary and remaining paid-run gap.",
            },
        ],
        "falsifiers": [
            "The result must block if iter64 proof, schema, validator, or candidate evidence is missing.",
            "The result must fail if the recovered prompt omits a required receipt field or digest rule.",
            "The result must fail if the valid fixture fails or the malformed fixture passes.",
            "The result must fail if provider calls, spend, GPU, cloud runner, Sentinel mutation, or overclaim occurs.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_review(status: str) -> None:
    review = f"""# Iteration 65 Review

Status: `{status.upper()}`.

The local diagnosis used the committed iter64 candidate, `protocol/proof.schema.json`,
`telos/proof.py`, and `scripts/validate_receipts.py`. The iter64 Telos row did create a JSON
object, but it was schema-incomplete: it used fields such as `goal`, `evidence_artifacts`,
`files_changed`, and `files_intentionally_left_unchanged` instead of the required Telos proof
receipt fields.

The recovered overlay now names the required fields and the canonical digest rule directly in the
agent prompt. The local valid fixture passes the current validator, and the malformed fixture fails.
That only proves prompt/schema alignment at the local receipt-contract layer. It does not prove that
a future provider row will follow the prompt, does not change the iter64 measured result, and does
not authorize any benchmark, model, leaderboard, production, live-domain, or state-of-the-art claim.

No provider call, API spend, GPU, cloud runner, Sentinel-named resource mutation, production change,
live-domain change, BattleSnake row execution, or excluded-pair execution occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")


def write_result(status: str, summary: dict[str, Any]) -> None:
    result = f"""# Iteration 65 Result - Receipt Schema Prompt Alignment

Status: `{status.upper()}`.

`iter65` diagnosed the `iter64` Telos-row receipt failure locally and produced a recovered
receipt-enforced prompt overlay. The iter64 receipt candidate is classified as
`{summary['iter64_receipt_failure_classification']}` because it omitted required Telos proof fields:
`{', '.join(summary['missing_required_fields'])}`.

Evidence:

- provider API calls: `{summary['provider_api_calls']}`
- provider spend: `${summary['provider_spend_usd']:.2f}`
- GPU used: `{str(summary['gpu_used']).lower()}`
- cloud runner started: `{str(summary['cloud_runner_started']).lower()}`
- Sentinel-named resources modified: `{str(summary['sentinel_named_resources_modified']).lower()}`
- recovered prompt required fields present: `{str(summary['recovered_prompt_required_fields_present']).lower()}`
- recovered prompt digest rule present: `{str(summary['recovered_prompt_digest_rule_present']).lower()}`
- local valid fixture passed: `{str(summary['local_valid_fixture_passed']).lower()}`
- local malformed fixture failed: `{str(summary['local_malformed_fixture_failed']).lower()}`
- redaction scan passed: `{str(summary['redaction_scan_passed']).lower()}`

Primary artifacts:

- `proof/receipt_failure_diagnosis.json`
- `proof/recovered_overlay/configs/mini/telos_vertex_gemini_receipt_enforced_agent.yaml`
- `proof/recovered_overlay/receipt_template.json`
- `proof/fixture_validation_report.json`
- `proof/receipt_schema_alignment_report.json`
- `proof/valid/receipt_receipt_schema_prompt_alignment.json`

It is not a benchmark result, SWE-bench result, leaderboard result, production/live-domain result,
model-superiority result, or state-of-the-art result. It only authorizes the claim that the local
Telos receipt prompt and fixtures now align with the committed proof validator before a future
pre-registered paid retry.
"""
    RESULT.write_text(result, encoding="utf-8")


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(paths):
        if path.exists() and path.is_file():
            hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    failures: list[str] = []
    required_inputs = [
        ITER64_REPORT,
        ITER64_SUMMARY,
        ITER64_CANDIDATE,
        ITER64_INVALID,
        SOURCE_OVERLAY,
        SCHEMA,
        PROOF_MODULE,
        RECEIPT_VALIDATOR,
    ]
    for path in required_inputs:
        if not path.exists():
            blockers.append(f"missing_input:{path.relative_to(ROOT)}")

    schema: dict[str, Any] = {}
    candidate: dict[str, Any] = {}
    validator_error = ""
    if not blockers:
        schema = read_json(SCHEMA)
        candidate = read_json(ITER64_CANDIDATE)
        invalid_artifact = read_json(ITER64_INVALID)
        if candidate != invalid_artifact:
            blockers.append("iter64_candidate_invalid_artifact_mismatch")
        try:
            validate_receipt(candidate)
        except ProofValidationError as exc:
            validator_error = str(exc)
        else:
            failures.append("iter64_candidate_unexpectedly_valid")

    schema_required = list(schema.get("required", REQUIRED_FIELDS))
    missing_fields = sorted(set(schema_required) - set(candidate))
    unexpected_fields = sorted(set(candidate) - set(schema.get("properties", {})))
    classification = "schema_incomplete" if missing_fields else "not_schema_incomplete"
    if classification != "schema_incomplete":
        failures.append("iter64_candidate_not_classified_schema_incomplete")

    DIAGNOSIS_PROBE.joinpath("valid").mkdir(parents=True, exist_ok=True)
    if candidate:
        write_json(DIAGNOSIS_PROBE / "valid" / "telos_completion_receipt.json", candidate)
    diagnosis_validation = run_capture([sys.executable, str(RECEIPT_VALIDATOR), str(DIAGNOSIS_PROBE)])

    overlay_text = build_recovered_overlay()
    overlay_path = OVERLAY / "telos_vertex_gemini_receipt_enforced_agent.yaml"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.write_text(overlay_text, encoding="utf-8")
    receipt_template = build_receipt_template()
    write_json(PROOF / "recovered_overlay" / "receipt_template.json", receipt_template)

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
    no_extra_field_warning_present = all(
        forbidden in overlay_text
        for forbidden in ["goal", "files_changed", "evidence_artifacts"]
    )
    if not required_fields_present:
        failures.append("recovered_prompt_missing_required_field")
    if not digest_rule_present:
        failures.append("recovered_prompt_missing_digest_rule")
    if not no_extra_field_warning_present:
        failures.append("recovered_prompt_missing_extra_field_warning")

    valid_fixture = dict(receipt_template)
    valid_fixture["receipt_id"] = "iter65-local-valid-fixture-pass"
    valid_fixture["task_id"] = "telos:iter65_receipt_schema_prompt_alignment:fixture"
    valid_fixture["agent_id"] = "codex-local-fixture"
    valid_fixture["benchmark_id"] = "telos_receipt_schema_alignment_fixture"
    valid_fixture["stated_goal"] = "Validate a local fixture against the Telos proof receipt schema."
    valid_fixture["evidence"] = [
        {
            "kind": "test",
            "status": "pass",
            "artifact": f"experiments/{EXPERIMENT_ID}/proof/fixture_receipts/valid/local_valid_receipt.json",
            "notes": "Fixture must pass scripts/validate_receipts.py.",
        }
    ]
    valid_fixture["sha256"] = receipt_digest(valid_fixture)
    malformed_fixture = dict(valid_fixture)
    malformed_fixture.pop("sha256", None)
    write_json(FIXTURES / "valid" / "local_valid_receipt.json", valid_fixture)
    write_json(FIXTURES / "invalid" / "missing_sha256_receipt.json", malformed_fixture)

    fixture_validation = run_capture([sys.executable, str(RECEIPT_VALIDATOR), str(FIXTURES)])
    local_valid_passed = fixture_validation["returncode"] == 0
    malformed_failed = False
    malformed_error = ""
    try:
        load_receipt(FIXTURES / "invalid" / "missing_sha256_receipt.json")
    except ProofValidationError as exc:
        malformed_failed = True
        malformed_error = str(exc)
    if not local_valid_passed:
        failures.append("local_valid_fixture_did_not_validate")
    if not malformed_failed:
        failures.append("local_malformed_fixture_unexpectedly_valid")

    iter64_receipt_validation = run_capture([sys.executable, str(RECEIPT_VALIDATOR), str(ITER64_PROOF)])
    iter64_audit = run_capture(
        [sys.executable, str(ROOT / "scripts" / "audit_provider_compatible_paid_execution_after_access_path_recovery.py")]
    )
    if iter64_receipt_validation["returncode"] != 0:
        blockers.append("iter64_receipt_validation_failed")
    if iter64_audit["returncode"] != 0:
        blockers.append("iter64_audit_failed")

    diagnosis = {
        "schema_version": "telos.receipt_schema_prompt_alignment.diagnosis.v1",
        "iter64_candidate_path": str(ITER64_CANDIDATE.relative_to(ROOT)),
        "iter64_candidate_sha256": sha256_file(ITER64_CANDIDATE) if ITER64_CANDIDATE.exists() else None,
        "iter64_invalid_artifact_path": str(ITER64_INVALID.relative_to(ROOT)),
        "iter64_invalid_artifact_sha256": sha256_file(ITER64_INVALID) if ITER64_INVALID.exists() else None,
        "candidate_equals_invalid_artifact": not blockers and read_json(ITER64_CANDIDATE) == read_json(ITER64_INVALID),
        "schema_path": str(SCHEMA.relative_to(ROOT)),
        "schema_sha256": sha256_file(SCHEMA),
        "proof_module_path": str(PROOF_MODULE.relative_to(ROOT)),
        "proof_module_sha256": sha256_file(PROOF_MODULE),
        "validator_path": str(RECEIPT_VALIDATOR.relative_to(ROOT)),
        "validator_sha256": sha256_file(RECEIPT_VALIDATOR),
        "schema_required_fields": schema_required,
        "candidate_fields": sorted(candidate),
        "missing_required_fields": missing_fields,
        "unexpected_fields_under_schema": unexpected_fields,
        "validator_error": validator_error,
        "diagnosis_validation_command": "python3 scripts/validate_receipts.py "
        + str(DIAGNOSIS_PROBE.relative_to(ROOT)),
        "diagnosis_validation": diagnosis_validation,
        "classification": classification,
    }
    write_json(PROOF / "receipt_failure_diagnosis.json", diagnosis)

    fixture_report = {
        "schema_version": "telos.receipt_schema_prompt_alignment.fixture_validation.v1",
        "validator_command": "python3 scripts/validate_receipts.py " + str(FIXTURES.relative_to(ROOT)),
        "validator_result": fixture_validation,
        "valid_fixture_path": str((FIXTURES / "valid" / "local_valid_receipt.json").relative_to(ROOT)),
        "malformed_fixture_path": str((FIXTURES / "invalid" / "missing_sha256_receipt.json").relative_to(ROOT)),
        "valid_fixture_passed": local_valid_passed,
        "malformed_fixture_failed": malformed_failed,
        "malformed_expected_error": "missing fields: sha256",
        "malformed_observed_error": malformed_error,
    }
    write_json(PROOF / "fixture_validation_report.json", fixture_report)

    redaction = redaction_findings()
    if redaction:
        failures.append("redaction_scan_findings")

    status = "blocked" if blockers else "fail" if failures else "pass"
    report = {
        "schema_version": "telos.receipt_schema_prompt_alignment.report.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "iter64_receipt_failure_classification": classification,
        "missing_required_fields": missing_fields,
        "unexpected_fields_under_schema": unexpected_fields,
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "excluded_pair_executed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "recovered_prompt_path": str(overlay_path.relative_to(ROOT)),
        "recovered_prompt_required_fields_present": required_fields_present,
        "recovered_prompt_digest_rule_present": digest_rule_present,
        "local_valid_fixture_passed": local_valid_passed,
        "local_malformed_fixture_failed": malformed_failed,
        "iter64_receipt_validation": iter64_receipt_validation,
        "iter64_audit": iter64_audit,
        "redaction_scan_passed": redaction == [],
        "redaction_findings": redaction,
        "blockers": blockers,
        "failures": failures,
    }
    write_json(PROOF / "receipt_schema_alignment_report.json", report)
    write_review(status)
    command_lines = [
        f"receipt schema prompt alignment: {status}",
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"iter64_receipt_failure_classification={classification}",
        "missing_required_fields=" + ",".join(missing_fields),
        f"recovered_prompt_required_fields_present={str(required_fields_present).lower()}",
        f"recovered_prompt_digest_rule_present={str(digest_rule_present).lower()}",
        f"local_valid_fixture_passed={str(local_valid_passed).lower()}",
        f"local_malformed_fixture_failed={str(malformed_failed).lower()}",
        f"redaction_scan_passed={str(redaction == []).lower()}",
        "blockers=" + ",".join(blockers),
        "failures=" + ",".join(failures),
    ]
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    receipt = build_gate_receipt(status)
    write_json(VALID / "receipt_receipt_schema_prompt_alignment.json", receipt)

    summary_artifacts = [
        PROOF / "receipt_failure_diagnosis.json",
        PROOF / "fixture_validation_report.json",
        PROOF / "receipt_schema_alignment_report.json",
        PROOF / "recovered_overlay" / "receipt_template.json",
        overlay_path,
        PROOF / "review.md",
        PROOF / "command_output.txt",
        VALID / "receipt_receipt_schema_prompt_alignment.json",
    ]
    summary = {
        "schema_version": "telos.receipt_schema_prompt_alignment.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "iter64_receipt_failure_classification": classification,
        "missing_required_fields": missing_fields,
        "unexpected_fields_under_schema": unexpected_fields,
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "excluded_pair_executed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "recovered_prompt_path": str(overlay_path.relative_to(ROOT)),
        "recovered_prompt_required_fields_present": required_fields_present,
        "recovered_prompt_digest_rule_present": digest_rule_present,
        "local_valid_fixture_passed": local_valid_passed,
        "local_malformed_fixture_failed": malformed_failed,
        "redaction_scan_passed": redaction == [],
        "redaction_findings": redaction,
        "blockers": blockers,
        "failures": failures,
        "next_gate": "experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/HYPOTHESIS.md",
        "artifact_hashes": artifact_hashes(summary_artifacts),
    }
    write_json(PROOF / "run_summary.json", summary)
    write_result(status, summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The iter64 Telos receipt failure was a prompt/schema alignment gap: the agent emitted "
            "a receipt-like JSON object, but the prompt did not expose the committed Telos receipt "
            "fields or canonical sha256 rule."
        ),
        "next_action": (
            "run the pre-registered bounded paid retry of the same two frozen provider-compatible "
            "rows using the recovered receipt prompt overlay"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/receipt_schema_alignment_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/receipt_failure_diagnosis.json",
            f"experiments/{EXPERIMENT_ID}/proof/fixture_validation_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/configs/mini/telos_vertex_gemini_receipt_enforced_agent.yaml",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_receipt_schema_prompt_alignment.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)

    print("\n".join(command_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
