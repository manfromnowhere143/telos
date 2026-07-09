#!/usr/bin/env python3
"""Audit iter61 Vertex quota-project binding recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter61_vertex_quota_project_binding_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "quota_project_binding_report.json"
PREFLIGHT = PROOF / "preflight.json"
RECEIPT = PROOF / "valid" / "receipt_vertex_quota_project_binding_recovery.json"
RUNTIME_BINDING = PROOF / "recovered_runtime_binding" / "quota_project_binding.json"
RUNTIME_TEMPLATE = (
    PROOF / "recovered_runtime_binding" / "telos_vertex_gemini_3_1_pro_customtools.quota-template.yaml"
)
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix in TEXT_SUFFIXES else []
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def audit_required_files(failures: list[str]) -> None:
    for path in [
        RESULT,
        SUMMARY,
        REPORT,
        PREFLIGHT,
        RECEIPT,
        RUNTIME_BINDING,
        RUNTIME_TEMPLATE,
        PROOF / "litellm_quota_probe_stdout.txt",
        PROOF / "litellm_quota_probe_stderr.txt",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_summary_and_report(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    preflight = load_json(PREFLIGHT)
    runtime = load_json(RUNTIME_BINDING)
    status = summary.get("status")
    if status not in {"pass", "blocked", "fail"}:
        failures.append(f"invalid status: {status!r}")
        return
    if report.get("status") != status:
        failures.append("report and summary status mismatch")
    if summary.get("experiment_id") != EXPERIMENT.name or report.get("experiment_id") != EXPERIMENT.name:
        failures.append("experiment id mismatch")
    if preflight.get("iter60_status") != "blocked":
        failures.append("preflight must prove iter60 was blocked")
    if preflight.get("iter60_after_vertex_location") != "global":
        failures.append("preflight must preserve iter60 global Vertex location")
    if preflight.get("iter60_redacted_consumer_invalid_present") is not True:
        failures.append("preflight must include redacted CONSUMER_INVALID evidence")
    if preflight.get("iter56_direct_rest_probe_status") != "pass":
        failures.append("preflight must cite the prior passing direct REST probe")
    if summary.get("source_path_extra_headers_supported") is not True:
        failures.append("summary must prove LiteLLM extra_headers support")
    if summary.get("minisweagent_model_kwargs_passthrough") is not True:
        failures.append("summary must prove Mini-SWE-Agent model_kwargs pass-through")
    if summary.get("runtime_quota_header") != "X-Goog-User-Project":
        failures.append("runtime quota header mismatch")
    if summary.get("quota_project_source") != "env:TELOS_VERTEX_QUOTA_PROJECT":
        failures.append("quota project source must be env-bound")
    if runtime.get("project_identifier_committed") is not False:
        failures.append("runtime binding must not commit project identifiers")
    if "${TELOS_VERTEX_QUOTA_PROJECT}" not in RUNTIME_TEMPLATE.read_text(encoding="utf-8"):
        failures.append("runtime template must keep quota project as an env placeholder")
    if summary.get("provider_model_calls", 0) > 2:
        failures.append("provider call ceiling exceeded")
    if summary.get("provider_spend_bound_usd", 999) > 0.05:
        failures.append("provider spend bound ceiling exceeded")
    for key in [
        "battle_snake_rows_executed",
        "excluded_pair_executed",
        "gpu_used",
        "sentinel_named_resources_modified",
        "cloud_runner_started",
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("redaction scan must pass with no findings")
    if status == "pass":
        if summary.get("clean_pass") is not True or summary.get("recovered_binding_accessible") is not True:
            failures.append("pass requires accessible recovered binding")
        if summary.get("provider_model_calls") != 1:
            failures.append("pass should record exactly one LiteLLM quota probe")
    if status == "blocked":
        if summary.get("clean_pass") is not False or summary.get("blocked_result") is not True:
            failures.append("blocked status booleans are inconsistent")
        if not summary.get("blockers"):
            failures.append("blocked result must name blockers")
    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_receipt_and_text(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    try:
        receipt = load_receipt(RECEIPT)
        if receipt.status != summary.get("status"):
            failures.append("receipt status mismatch")
    except ProofValidationError as exc:
        failures.append(f"receipt validation failed: {exc}")
    result = RESULT.read_text(encoding="utf-8")
    for required in [
        f"Status: `{str(summary.get('status')).upper()}`.",
        "quota-project/header binding recovery result",
        "not a protocol-effect result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")


def audit_secrets(failures: list[str]) -> None:
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like or identifier residue in {path}")
                break


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        audit_summary_and_report(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter61 Vertex quota-project binding recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter61 Vertex quota-project binding recovery audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
