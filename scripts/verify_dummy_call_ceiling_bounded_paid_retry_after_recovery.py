#!/usr/bin/env python3
"""Run iter80 Dummy-only bounded paid retry after iter79 call-ceiling recovery."""

from __future__ import annotations

import copy
import importlib.util
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
ITER72_SCRIPT = ROOT / "scripts" / "verify_provider_compatible_expanded_paid_execution_after_slice_refreeze.py"
EXPERIMENT_ID = "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_dummy_call_ceiling_bounded_paid_retry_after_recovery.json"
ITER79_ID = "iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block"
ITER79_PROOF = ROOT / "experiments" / ITER79_ID / "proof"
ITER79_SUMMARY = ITER79_PROOF / "run_summary.json"
ITER79_PLAN = ITER79_PROOF / "recovery_plan.json"
DUMMY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
]
DETERMINISTIC_EDIT_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
BATTLESNAKE_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
BASELINE_SOURCE = (
    ROOT
    / "experiments"
    / "iter70_provider_compatible_expanded_adapter_completion"
    / "proof"
    / "recovered_overlay"
    / "configs"
    / "mini"
    / "telos_vertex_gemini_dummy_baseline_agent.yaml"
)
TELOS_SOURCE = (
    ROOT
    / "experiments"
    / "iter73_expanded_receipt_prompt_recovery_after_paid_block"
    / "proof"
    / "recovered_overlay"
    / "configs"
    / "mini"
    / "telos_vertex_gemini_dummy_receipt_enforced_agent.yaml"
)
RECOVERED_OVERLAY_DIR = PROOF / "recovered_overlay" / "configs" / "mini"
BASELINE_RECOVERED = RECOVERED_OVERLAY_DIR / "telos_vertex_gemini_dummy_baseline_agent.yaml"
TELOS_RECOVERED = RECOVERED_OVERLAY_DIR / "telos_vertex_gemini_dummy_receipt_enforced_agent.yaml"
RECOVERED_AGENT_BY_PAIR = {
    DUMMY_PAIR_IDS[0]: BASELINE_RECOVERED,
    DUMMY_PAIR_IDS[1]: TELOS_RECOVERED,
}
PER_ROW_CALL_LIMIT = 16
PER_ROW_SPEND_LIMIT_USD = 2.5
TOTAL_CALL_CEILING = 32
TOTAL_SPEND_CEILING_USD = 5.0
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


def load_iter72() -> Any:
    spec = importlib.util.spec_from_file_location("iter72_expanded_paid_runner", ITER72_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load iter72 runner: {ITER72_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


iter72 = load_iter72()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return iter72.sha256_file(path)


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def redaction_scan() -> tuple[bool, list[str]]:
    findings: list[str] = []
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return not findings, sorted(set(findings))


def configure_modules() -> None:
    iter72.EXPERIMENT_ID = EXPERIMENT_ID
    iter72.EXPERIMENT = EXPERIMENT
    iter72.PROOF = PROOF
    iter72.RAW = RAW
    iter72.VALID = VALID
    iter72.RESULT = RESULT
    iter72.SELECTED_PAIR_IDS = DUMMY_PAIR_IDS
    iter72.RETAINED_PAIR_IDS = [*DETERMINISTIC_EDIT_PAIR_IDS, *BATTLESNAKE_PAIR_IDS]
    iter72.TOTAL_CALL_CEILING = TOTAL_CALL_CEILING
    iter72.TOTAL_SPEND_CEILING_USD = TOTAL_SPEND_CEILING_USD
    iter72.PER_ROW_CALL_LIMIT = PER_ROW_CALL_LIMIT
    iter72.PER_ROW_SPEND_LIMIT_USD = PER_ROW_SPEND_LIMIT_USD
    iter72.helper.EXPERIMENT_ID = EXPERIMENT_ID
    iter72.helper.EXPERIMENT = EXPERIMENT
    iter72.helper.PROOF = PROOF
    iter72.helper.RAW = RAW
    iter72.helper.VALID = VALID
    iter72.helper.CALL_CEILING = PER_ROW_CALL_LIMIT
    iter72.helper.SPEND_CEILING = PER_ROW_SPEND_LIMIT_USD


def write_recovered_agent_overlays() -> dict[str, Any]:
    RECOVERED_OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for pair_id, source, destination in [
        (DUMMY_PAIR_IDS[0], BASELINE_SOURCE, BASELINE_RECOVERED),
        (DUMMY_PAIR_IDS[1], TELOS_SOURCE, TELOS_RECOVERED),
    ]:
        text = source.read_text(encoding="utf-8")
        if "step_limit: 8" not in text:
            raise RuntimeError(f"{relative(source)} missing step_limit: 8")
        updated = text.replace("step_limit: 8", f"step_limit: {PER_ROW_CALL_LIMIT}", 1)
        destination.write_text(updated, encoding="utf-8")
        generated.append(
            {
                "pair_id": pair_id,
                "source": relative(source),
                "source_sha256": sha256_file(source),
                "destination": relative(destination),
                "destination_sha256": sha256_file(destination),
                "previous_step_limit": 8,
                "recovered_step_limit": PER_ROW_CALL_LIMIT,
            }
        )
    packet = {
        "schema_version": "telos.dummy_call_ceiling_bounded_paid_retry.recovered_agent_overlays.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_recovery_iteration": ITER79_ID,
        "generated": generated,
        "all_recovered_step_limits_written": all(
            item["recovered_step_limit"] == PER_ROW_CALL_LIMIT for item in generated
        ),
    }
    write_json(PROOF / "recovered_agent_overlay_manifest.json", packet)
    return packet


def candidate_rows() -> list[dict[str, Any]]:
    rows = copy.deepcopy(iter72.candidate_rows())
    selected = []
    for row in rows:
        pair_id = str(row.get("pair_id"))
        if pair_id not in DUMMY_PAIR_IDS:
            continue
        adapter = row.setdefault("adapter_evidence", {})
        adapter["iter70_or_iter73_provider_agent_config_replaced_by_iter80"] = adapter.get(
            "provider_agent_config"
        )
        adapter["provider_agent_config"] = relative(RECOVERED_AGENT_BY_PAIR[pair_id])
        adapter["provider_agent_config_source_iteration"] = EXPERIMENT_ID
        adapter["provider_agent_step_limit"] = PER_ROW_CALL_LIMIT
        selected.append(row)
    return selected


def call_ceiling_binding_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    copies = manifest.get("copies", [])
    bindings = []
    for pair_id, source_path in RECOVERED_AGENT_BY_PAIR.items():
        source = relative(source_path)
        copy_entry = next(
            (
                item
                for item in copies
                if item.get("source") == source
                and item.get("destination", "").endswith(source_path.name)
            ),
            {},
        )
        bindings.append(
            {
                "pair_id": pair_id,
                "source": source,
                "source_sha256": sha256_file(source_path),
                "destination": copy_entry.get("destination"),
                "destination_sha256": copy_entry.get("destination_sha256"),
                "hash_match": copy_entry.get("hash_match"),
                "copied_or_written": copy_entry.get("copied_or_written", False),
                "materialization": copy_entry.get("materialization"),
                "previous_step_limit": 8,
                "recovered_step_limit": PER_ROW_CALL_LIMIT,
            }
        )
    return {
        "schema_version": "telos.dummy_call_ceiling_bounded_paid_retry.call_ceiling_overlay_binding.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iteration": ITER79_ID,
        "bindings": bindings,
        "all_required_call_ceiling_overlays_materialized": all(
            item["copied_or_written"] is True and item["hash_match"] is True
            for item in bindings
        ),
    }


def materialize_runtime_overlay(rows: list[dict[str, Any]], *, project_id: str, token: str) -> dict[str, Any]:
    manifest = iter72.materialize_runtime_overlay(rows, project_id=project_id, token=token)
    recovered_sources = {relative(path) for path in RECOVERED_AGENT_BY_PAIR.values()}
    for copy_entry in manifest.get("copies", []):
        if copy_entry.get("source") in recovered_sources:
            copy_entry["materialization"] = "copied_iter80_call_ceiling_recovered_dummy_overlay"
            copy_entry["source_override_reason"] = "iter79_dummy_call_ceiling_recovery"
            copy_entry["previous_step_limit"] = 8
            copy_entry["recovered_step_limit"] = PER_ROW_CALL_LIMIT
    binding = call_ceiling_binding_from_manifest(manifest)
    manifest["schema_version"] = "telos.dummy_call_ceiling_bounded_paid_retry.overlay_materialization.v1"
    manifest["call_ceiling_overlay_binding_path"] = "call_ceiling_overlay_binding.json"
    manifest["call_ceiling_overlays_all_materialized"] = binding[
        "all_required_call_ceiling_overlays_materialized"
    ]
    write_json(PROOF / "call_ceiling_overlay_binding.json", binding)
    write_json(PROOF / "overlay_materialization_manifest.json", manifest)
    return manifest


def prerequisite_validation() -> dict[str, Any]:
    iter79_summary = read_json(ITER79_SUMMARY)
    iter79_plan = read_json(ITER79_PLAN)
    iter79_receipts = run_capture(
        ["python3", "scripts/validate_receipts.py", relative(ITER79_PROOF)]
    )
    iter79_audit = run_capture(
        ["python3", "scripts/audit_dummy_row_call_ceiling_recovery_after_paid_retry_block.py"]
    )
    clean = (
        iter79_summary.get("status") == "pass"
        and iter79_summary.get("clean_pass") is True
        and iter79_summary.get("dummy_rows_classified") is True
        and iter79_summary.get("next_gate")
        == f"experiments/{EXPERIMENT_ID}/HYPOTHESIS.md"
        and iter79_plan.get("selected_pair_ids") == DUMMY_PAIR_IDS
        and int(iter79_plan.get("recommended_per_row_call_limit", -1)) == PER_ROW_CALL_LIMIT
        and int(iter79_plan.get("provider_call_ceiling", -1)) == TOTAL_CALL_CEILING
        and float(iter79_plan.get("provider_spend_ceiling_usd", -1.0))
        == TOTAL_SPEND_CEILING_USD
        and iter79_receipts["returncode"] == 0
        and iter79_audit["returncode"] == 0
    )
    return {
        "schema_version": "telos.dummy_call_ceiling_bounded_paid_retry.prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter79_status": iter79_summary.get("status"),
        "iter79_clean_pass": iter79_summary.get("clean_pass"),
        "iter79_dummy_rows_classified": iter79_summary.get("dummy_rows_classified"),
        "iter79_next_gate": iter79_summary.get("next_gate"),
        "iter79_receipt_validation_returncode": iter79_receipts["returncode"],
        "iter79_audit_returncode": iter79_audit["returncode"],
        "iter79_recovery_plan_selected_pair_ids": iter79_plan.get("selected_pair_ids"),
        "iter79_recovery_plan_per_row_call_limit": iter79_plan.get(
            "recommended_per_row_call_limit"
        ),
        "iter79_recovery_plan_provider_call_ceiling": iter79_plan.get(
            "provider_call_ceiling"
        ),
        "iter79_recovery_plan_provider_spend_ceiling_usd": iter79_plan.get(
            "provider_spend_ceiling_usd"
        ),
        "source_iter79_summary": relative(ITER79_SUMMARY),
        "source_iter79_summary_sha256": sha256_file(ITER79_SUMMARY),
        "source_iter79_recovery_plan": relative(ITER79_PLAN),
        "source_iter79_recovery_plan_sha256": sha256_file(ITER79_PLAN),
        "clean_prerequisites": clean,
        "paid_execution_allowed": clean,
    }


def primary_metric(row_results: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_pair = {row.get("pair_id"): row for row in row_results}
    metric = {
        "dummy_baseline_verified_completion_evidence": rows_by_pair.get(DUMMY_PAIR_IDS[0], {}).get(
            "verified_completion_evidence", False
        ),
        "dummy_telos_verified_completion_evidence": rows_by_pair.get(DUMMY_PAIR_IDS[1], {}).get(
            "verified_completion_evidence", False
        ),
        "deterministic_edit_rows_retained_not_rerun": True,
    }
    metric["dummy_delta_telos_minus_baseline"] = int(
        bool(metric["dummy_telos_verified_completion_evidence"])
    ) - int(bool(metric["dummy_baseline_verified_completion_evidence"]))
    return metric


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter80-dummy-call-ceiling-bounded-paid-retry-{status}",
        "task_id": "telos:iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery@iter79",
        "agent_id": "codex-local-dummy-only-bounded-paid-retry-runner",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute only the two Dummy adapter rows under the iter79 call-ceiling recovery plan."
        ),
        "acceptance_criteria": [
            "Iter79 validates as a clean recovery packet.",
            "Exactly the two selected Dummy rows execute.",
            "No deterministic-edit or BattleSnake rows rerun.",
            "Each row uses a 16-call per-row ceiling; total calls stay at or below 32.",
            "Total provider spend stays at or below $5.00.",
            "Receipt-required rows have valid Telos receipts before verified completion is accepted.",
            "No GPU, cloud runner, Sentinel mutation, live-domain mutation, or benchmark/model claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records row execution, calls, costs, receipts, blockers, and claim boundary.",
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
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/call_ceiling_overlay_binding.json",
                "notes": "Binding proves the Dummy agent overlays used the recovered 16-call ceiling.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-benchmark/no-model boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter79 validation fails.",
            "The result must fail if any unselected row executes.",
            "The result must fail if provider calls or spend exceed the frozen ceiling.",
            "The result must block if receipt-required rows lack valid receipts.",
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
    row_results: list[dict[str, Any]],
    provider_calls: int,
    provider_cost: float,
    blockers: list[str],
    failures: list[str],
    metric: dict[str, Any],
    prerequisite: dict[str, Any],
    binding: dict[str, Any],
) -> None:
    summary_sentence = (
        "The gate executed exactly the two Dummy adapter rows under the iter79 recovered 16-call ceiling."
        if row_results
        else "The gate blocked before Dummy row execution because preflight failed."
    )
    RESULT.write_text(
        f"""# Iteration 80 Result - Dummy Call-Ceiling Bounded Paid Retry After Recovery

Status: `{status.upper()}`.

## Summary

{summary_sentence}

- executed adapter row count: `{len(row_results)}`,
- deterministic-edit rows rerun: `false`,
- retained BattleSnake rows rerun: `false`,
- iter79 recovery validation clean: `{str(prerequisite['clean_prerequisites']).lower()}`,
- call-ceiling overlays materialized: `{str(binding['all_required_call_ceiling_overlays_materialized']).lower()}`,
- per-row provider call ceiling: `{PER_ROW_CALL_LIMIT}`,
- provider API calls: `{provider_calls}`,
- provider call ceiling: `{TOTAL_CALL_CEILING}`,
- provider cost from CodeClash metadata: `${provider_cost:.8f}`,
- provider spend ceiling: `${TOTAL_SPEND_CEILING_USD:.2f}`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Stratified Metrics

- Dummy baseline verified-completion evidence:
  `{str(metric['dummy_baseline_verified_completion_evidence']).lower()}`,
- Dummy Telos verified-completion evidence:
  `{str(metric['dummy_telos_verified_completion_evidence']).lower()}`,
- Dummy Telos-minus-baseline verified-completion delta:
  `{metric['dummy_delta_telos_minus_baseline']}`.

## Claim Boundary

This is a bounded two-row Dummy adapter-validation retry. It is not a benchmark result, SWE-bench
score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/recovered_agent_overlay_manifest.json`
- `proof/preflight.json`
- `proof/runtime_access_path_binding.json`
- `proof/runtime_access_path_model_config.yaml`
- `proof/overlay_materialization_manifest.json`
- `proof/call_ceiling_overlay_binding.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
""",
        encoding="utf-8",
    )
    command_lines = [
        f"dummy call-ceiling bounded paid retry: {status}",
        f"iter79_receipt_validation_returncode={prerequisite['iter79_receipt_validation_returncode']}",
        f"iter79_audit_returncode={prerequisite['iter79_audit_returncode']}",
        f"selected_pair_count={len(DUMMY_PAIR_IDS)}",
        f"executed_pair_count={len(row_results)}",
        "deterministic_edit_rows_rerun=false",
        "retained_battlesnake_rows_rerun=false",
        f"per_row_call_limit={PER_ROW_CALL_LIMIT}",
        f"provider_api_calls={provider_calls}",
        f"provider_call_ceiling={TOTAL_CALL_CEILING}",
        f"provider_cost_usd={provider_cost:.8f}",
        f"provider_spend_ceiling_usd={TOTAL_SPEND_CEILING_USD:.2f}",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"dummy_baseline_verified_completion_evidence={str(metric['dummy_baseline_verified_completion_evidence']).lower()}",
        f"dummy_telos_verified_completion_evidence={str(metric['dummy_telos_verified_completion_evidence']).lower()}",
        f"dummy_delta_telos_minus_baseline={metric['dummy_delta_telos_minus_baseline']}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    for row in row_results:
        command_lines.append(
            f"{row['pair_id']}: rc={row['command_returncode']} calls={row['provider_api_calls']} "
            f"cost={row['provider_cost_usd']:.8f} receipt_required={str(row['receipt_required']).lower()} "
            f"receipt_valid={str(row['receipt_valid']).lower()} verified={str(row['verified_completion_evidence']).lower()}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")
    (PROOF / "review.md").write_text(
        f"""# Iteration 80 Review

This gate executed only the two Dummy adapter rows selected by iter79, with the per-row global call
ceiling raised from `8` to `{PER_ROW_CALL_LIMIT}`. Deterministic-edit rows and retained BattleSnake
rows were not rerun.

- status: `{status}`,
- executed row count: `{len(row_results)}`,
- provider API calls: `{provider_calls}`,
- provider cost: `${provider_cost:.8f}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

The evidence remains Dummy-only and stratified. No benchmark, SWE-bench, leaderboard,
production/live-domain, model-superiority, or state-of-the-art result is claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    configure_modules()
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    prerequisite = prerequisite_validation()
    write_json(PROOF / "prerequisite_validation.json", prerequisite)
    recovered_manifest = write_recovered_agent_overlays()
    rows = candidate_rows()
    selected_ids = [row["pair_id"] for row in rows]
    project_available, project_id = iter72.helper.gcloud_project()
    token = iter72.helper.access_token() if project_available else None
    token_available = token is not None
    iter72.helper.DYNAMIC_PROJECT_ID = project_id
    iter72.helper.DYNAMIC_BEARER_TOKEN = token

    if project_id and token:
        overlay = materialize_runtime_overlay(rows, project_id=project_id, token=token)
    else:
        overlay = iter72.write_unmaterialized_overlay("runtime_project_or_adc_token_unavailable")
        write_json(
            PROOF / "call_ceiling_overlay_binding.json",
            {
                "schema_version": "telos.dummy_call_ceiling_bounded_paid_retry.call_ceiling_overlay_binding.v1",
                "experiment_id": EXPERIMENT_ID,
                "source_iteration": ITER79_ID,
                "bindings": [],
                "all_required_call_ceiling_overlays_materialized": False,
                "blocked_before_materialization_reason": "runtime_project_or_adc_token_unavailable",
            },
        )
    binding = read_json(PROOF / "call_ceiling_overlay_binding.json")

    codeclash_rev = run_capture(["git", "-C", str(iter72.CODECLASH_DIR), "rev-parse", "HEAD"])
    docker = run_capture(
        [str(iter72.helper.DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"],
        timeout=10,
    )
    google_auth = run_capture(
        [str(iter72.CODECLASH_DIR / ".venv" / "bin" / "python"), "-c", "import google.auth"],
        timeout=10,
    )
    preflight = {
        "schema_version": "telos.dummy_call_ceiling_bounded_paid_retry.preflight.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter79_status": prerequisite["iter79_status"],
        "iter79_clean_pass": prerequisite["iter79_clean_pass"],
        "iter79_receipt_validation_returncode": prerequisite[
            "iter79_receipt_validation_returncode"
        ],
        "iter79_audit_returncode": prerequisite["iter79_audit_returncode"],
        "codeclash_expected_commit": iter72.CODECLASH_COMMIT,
        "codeclash_actual_commit": codeclash_rev.get("stdout"),
        "codeclash_commit_matches_expected": codeclash_rev.get("stdout") == iter72.CODECLASH_COMMIT,
        "docker_ready": docker.get("returncode") == 0 and bool(docker.get("stdout")),
        "docker_server_version_present": bool(docker.get("stdout")),
        "codeclash_google_auth_import_ready": google_auth.get("returncode") == 0,
        "runtime_project_available": project_available,
        "adc_access_token_available": token_available,
        "adc_token_output_suppressed": True,
        "runtime_env_values_committed": False,
        "runtime_overlay_all_materialized": overlay.get("all_materialized"),
        "runtime_overlay_copied_hashes_match": overlay.get("copied_hashes_match"),
        "runtime_model_config_materialized": overlay.get("runtime_model_config_materialized"),
        "runtime_model_config_has_secret_values_only_in_tmp": overlay.get(
            "runtime_model_config_has_secret_values_only_in_tmp"
        ),
        "call_ceiling_overlays_all_materialized": binding.get(
            "all_required_call_ceiling_overlays_materialized"
        ),
        "selected_pair_ids": selected_ids,
        "expected_selected_pair_ids": DUMMY_PAIR_IDS,
        "deterministic_edit_pair_ids_retained_not_rerun": DETERMINISTIC_EDIT_PAIR_IDS,
        "retained_battlesnake_pair_ids_not_rerun": BATTLESNAKE_PAIR_IDS,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
    }
    write_json(PROOF / "preflight.json", preflight)

    blockers: list[str] = []
    failures: list[str] = []
    if prerequisite["clean_prerequisites"] is not True:
        blockers.append("iter79_prerequisite_validation_failed")
    if selected_ids != DUMMY_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if preflight["codeclash_commit_matches_expected"] is not True:
        blockers.append("codeclash_checkout_not_pinned")
    if preflight["docker_ready"] is not True:
        blockers.append("docker_not_ready")
    if preflight["codeclash_google_auth_import_ready"] is not True:
        blockers.append("codeclash_google_auth_import_failed")
    if preflight["runtime_project_available"] is not True:
        blockers.append("gcloud_project_unavailable")
    if preflight["adc_access_token_available"] is not True:
        blockers.append("adc_auth_unavailable")
    if preflight["runtime_overlay_all_materialized"] is not True:
        blockers.append("runtime_overlay_not_materialized")
    if preflight["runtime_overlay_copied_hashes_match"] is not True:
        blockers.append("runtime_overlay_hash_mismatch")
    if preflight["runtime_model_config_has_secret_values_only_in_tmp"] is not True:
        blockers.append("runtime_model_config_secret_boundary_not_proven")
    if preflight["call_ceiling_overlays_all_materialized"] is not True:
        blockers.append("call_ceiling_overlay_not_materialized")

    row_results: list[dict[str, Any]] = []
    if not blockers and not failures:
        for row in rows:
            pair_id = row["pair_id"]
            result = iter72.helper.run_paid_command(
                pair_id,
                row["future_execution_command"],
                project_id=project_id,
                token=token,
            )
            raw_packet = iter72.helper.copy_raw_packet(pair_id, result.get("output_dir"))
            row_result = iter72.row_metrics(row, result, raw_packet)
            row_results.append(row_result)
            calls_so_far = sum(int(item.get("provider_api_calls", 0)) for item in row_results)
            cost_so_far = sum(float(item.get("provider_cost_usd", 0.0)) for item in row_results)
            if calls_so_far > TOTAL_CALL_CEILING or cost_so_far > TOTAL_SPEND_CEILING_USD:
                failures.append("provider_ceiling_exceeded_during_execution")
                break

    provider_calls = sum(int(row.get("provider_api_calls", 0)) for row in row_results)
    provider_cost = round(sum(float(row.get("provider_cost_usd", 0.0)) for row in row_results), 8)
    if row_results and len(row_results) != 2:
        failures.append("not_exactly_two_dummy_rows_executed")
    if any(row.get("pair_id") not in DUMMY_PAIR_IDS for row in row_results):
        failures.append("unselected_row_executed")
    if provider_calls > TOTAL_CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if provider_cost > TOTAL_SPEND_CEILING_USD:
        failures.append("provider_spend_ceiling_exceeded")
    if any(int(row.get("provider_api_calls", 0)) > PER_ROW_CALL_LIMIT for row in row_results):
        failures.append("per_row_call_ceiling_exceeded")
    if any(float(row.get("provider_cost_usd", 0.0)) > PER_ROW_SPEND_LIMIT_USD for row in row_results):
        failures.append("per_row_spend_ceiling_exceeded")
    if any(row.get("command_returncode") not in (0, None) for row in row_results):
        blockers.append("provider_command_nonzero_returncode")
    for error_class in iter72.provider_error_classes(row_results):
        if error_class not in blockers:
            blockers.append(error_class)
    for row in row_results:
        if row.get("receipt_required") is True and row.get("receipt_valid") is not True:
            blockers.append(f"{row['pair_id']}_receipt_not_valid")

    scan_passed, scan_findings = redaction_scan()
    if not scan_passed:
        failures.append("redaction_scan_failed")

    metric = primary_metric(row_results)
    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"

    report = {
        "schema_version": "telos.dummy_call_ceiling_bounded_paid_retry.report.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "preflight": preflight,
        "prerequisite_validation": prerequisite,
        "recovered_agent_overlay_manifest": recovered_manifest,
        "call_ceiling_overlay_binding": binding,
        "selected_pair_ids": DUMMY_PAIR_IDS,
        "deterministic_edit_pair_ids_retained_not_rerun": DETERMINISTIC_EDIT_PAIR_IDS,
        "retained_battlesnake_pair_ids_not_rerun": BATTLESNAKE_PAIR_IDS,
        "executed_pair_ids": [row.get("pair_id") for row in row_results],
        "executed_pair_count": len(row_results),
        "row_results": row_results,
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "primary_metric": metric,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "blockers": blockers,
        "failures": failures,
    }
    write_json(PROOF / "protocol_effect_report.json", iter72.helper.redact_value(report))
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(
        status=status,
        row_results=row_results,
        provider_calls=provider_calls,
        provider_cost=provider_cost,
        blockers=blockers,
        failures=failures,
        metric=metric,
        prerequisite=prerequisite,
        binding=binding,
    )
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status if status != "fail" else "null",
            "insight": (
                "The Dummy-only call-ceiling retry completed under bounded provider ceilings."
                if status == "pass"
                else "The Dummy-only call-ceiling retry still exposed a bounded blocker before benchmark claims."
            ),
            "next_action": (
                "consolidate the expanded stratified adapter-validation evidence before any benchmark claim"
                if status == "pass"
                else "recover the named Dummy retry blocker before any broader paid execution"
            ),
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/protocol_effect_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/call_ceiling_overlay_binding.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary_paths = [
        PROOF / "prerequisite_validation.json",
        PROOF / "recovered_agent_overlay_manifest.json",
        PROOF / "preflight.json",
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "overlay_materialization_manifest.json",
        PROOF / "call_ceiling_overlay_binding.json",
        PROOF / "protocol_effect_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        VALID,
        RAW,
    ]
    summary = {
        "schema_version": "telos.dummy_call_ceiling_bounded_paid_retry.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter79_status": prerequisite["iter79_status"],
        "iter79_clean_pass": prerequisite["iter79_clean_pass"],
        "iter79_receipt_validation_returncode": prerequisite[
            "iter79_receipt_validation_returncode"
        ],
        "iter79_audit_returncode": prerequisite["iter79_audit_returncode"],
        "selected_pair_ids": DUMMY_PAIR_IDS,
        "deterministic_edit_pair_ids_retained_not_rerun": DETERMINISTIC_EDIT_PAIR_IDS,
        "retained_battlesnake_pair_ids_not_rerun": BATTLESNAKE_PAIR_IDS,
        "executed_pair_ids": [row.get("pair_id") for row in row_results],
        "executed_pair_count": len(row_results),
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "primary_metric": metric,
        "runtime_overlay_all_materialized": overlay.get("all_materialized"),
        "runtime_overlay_copied_hashes_match": overlay.get("copied_hashes_match"),
        "call_ceiling_overlays_all_materialized": binding.get(
            "all_required_call_ceiling_overlays_materialized"
        ),
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "artifact_hashes": iter72.artifact_hashes(summary_paths),
    }
    write_json(PROOF / "run_summary.json", iter72.helper.redact_value(summary))

    print(f"dummy call-ceiling bounded paid retry: {status}")
    print(f"selected_pair_count={len(DUMMY_PAIR_IDS)}")
    print(f"executed_pair_count={len(row_results)}")
    print("deterministic_edit_rows_rerun=false")
    print("retained_battlesnake_rows_rerun=false")
    print(f"per_row_call_limit={PER_ROW_CALL_LIMIT}")
    print(f"provider_api_calls={provider_calls}")
    print(f"provider_call_ceiling={TOTAL_CALL_CEILING}")
    print(f"provider_cost_usd={provider_cost:.8f}")
    print(f"provider_spend_ceiling_usd={TOTAL_SPEND_CEILING_USD:.2f}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
