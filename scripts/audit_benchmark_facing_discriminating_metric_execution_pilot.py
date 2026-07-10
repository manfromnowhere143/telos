#!/usr/bin/env python3
"""Audit iter87 benchmark-facing discriminating-metric execution artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot")
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
ITER86_PREREQ = PROOF / "iter86_prerequisite_validation.json"
EXECUTION = PROOF / "execution_accounting_report.json"
EXTRACTION = PROOF / "fresh_metric_extraction.json"
METRIC_REPORT = PROOF / "discriminating_metric_report.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
PROTOCOL_REPORT = PROOF / "protocol_effect_report.json"
PREFLIGHT = PROOF / "preflight.json"
ROW_PLAN = PROOF / "selected_row_plan.json"
RECOVERED = PROOF / "recovered_agent_overlay_manifest.json"
OVERLAY = PROOF / "overlay_materialization_manifest.json"
RECEIPT = PROOF / "valid" / "receipt_benchmark_facing_discriminating_metric_execution_pilot.json"
ITER86_PROOF = Path("experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/proof")
ITER86_SUMMARY = ITER86_PROOF / "run_summary.json"
ITER86_EXTRACTION = ITER86_PROOF / "raw_metric_extraction.json"
ITER86_BACKTEST = ITER86_PROOF / "backtest_report.json"
ITER86_RECEIPT = ITER86_PROOF / "valid" / "receipt_discriminating_metric_backtest_on_committed_artifacts.json"
METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
PAIR_TO_TASK = {
    SELECTED_PAIR_IDS[0]: "dummy",
    SELECTED_PAIR_IDS[1]: "battlesnake",
    SELECTED_PAIR_IDS[2]: "deterministic_edit",
    SELECTED_PAIR_IDS[3]: "dummy",
    SELECTED_PAIR_IDS[4]: "battlesnake",
    SELECTED_PAIR_IDS[5]: "deterministic_edit",
}
PAIR_TO_CONDITION = {
    SELECTED_PAIR_IDS[0]: "baseline",
    SELECTED_PAIR_IDS[1]: "baseline",
    SELECTED_PAIR_IDS[2]: "baseline",
    SELECTED_PAIR_IDS[3]: "telos",
    SELECTED_PAIR_IDS[4]: "telos",
    SELECTED_PAIR_IDS[5]: "telos",
}
TELOS_PAIR_IDS = set(SELECTED_PAIR_IDS[3:])
PER_ROW_CALL_LIMIT = 16
TOTAL_CALL_CEILING = 96
PER_ROW_SPEND_LIMIT = Decimal("2.00000000")
TOTAL_SPEND_CEILING = Decimal("10.00000000")
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


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001")), "f")


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def audit_required_files(failures: list[str]) -> None:
    for path in [
        RESULT,
        SUMMARY,
        ITER86_PREREQ,
        EXECUTION,
        EXTRACTION,
        METRIC_REPORT,
        CLAIM_BOUNDARY,
        REDACTION,
        PROTOCOL_REPORT,
        PREFLIGHT,
        ROW_PLAN,
        RECOVERED,
        OVERLAY,
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_schemas(packets: dict[str, dict], failures: list[str]) -> None:
    expected = {
        "summary": "telos.benchmark_facing_discriminating_metric_execution.summary.v1",
        "iter86": "telos.benchmark_facing_discriminating_metric_execution.iter86_prerequisite_validation.v1",
        "execution": "telos.benchmark_facing_discriminating_metric_execution.execution_accounting.v1",
        "extraction": "telos.benchmark_facing_discriminating_metric_execution.fresh_metric_extraction.v1",
        "metric": "telos.benchmark_facing_discriminating_metric_execution.metric_report.v1",
        "boundary": "telos.benchmark_facing_discriminating_metric_execution.claim_boundary.v1",
        "redaction": "telos.benchmark_facing_discriminating_metric_execution.redaction_scan.v1",
    }
    for name, schema in expected.items():
        packet = packets[name]
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_status_and_boundaries(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    execution = packets["execution"]
    metric = packets["metric"]
    boundary = packets["boundary"]
    redaction = packets["redaction"]
    if summary.get("status") != "pass":
        failures.append("iter87 summary must pass")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    if execution.get("runner_status") != "blocked":
        failures.append("underlying verified-completion runner should remain blocked/null")
    if execution.get("ignored_runner_blockers") != ["no_interpretable_telos_minus_baseline_signal"]:
        failures.append("old null blocker must be explicitly ignored by metric redesign")
    if execution.get("old_verified_completion_metric_used_for_iter87_status") is not False:
        failures.append("iter87 must not use old verified-completion metric for status")
    if summary.get("old_verified_completion_metric_used_for_iter87_status") is not False:
        failures.append("summary must reject old verified-completion status metric")

    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
        "cross_task_surface_pooling_authorized",
        "aggregate_benchmark_metric_authorized",
    ]:
        for packet_name, packet in [
            ("summary", summary),
            ("execution", execution),
            ("metric", metric),
            ("boundary", boundary),
        ]:
            if key in packet and packet.get(key) is not False:
                failures.append(f"{packet_name} {key} must be false")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False or execution.get(key) is not False:
            failures.append(f"{key} must be false")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan must pass with no findings")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")


def audit_iter86_prerequisites(iter86: dict, failures: list[str]) -> None:
    if iter86.get("clean_prerequisites") is not True:
        failures.append("iter86 prerequisite packet must be clean")
    if iter86.get("iter86_status") != "pass" or iter86.get("iter86_clean_pass") is not True:
        failures.append("iter86 must be a clean pass")
    if iter86.get("iter86_metric_id") != METRIC_ID:
        failures.append("iter86 metric id changed")
    if iter86.get("iter86_metric_non_saturated") is not True:
        failures.append("iter86 metric must be non-saturated")
    if iter86.get("iter86_receipt_validation_returncode") != 0:
        failures.append("iter86 receipt validation must pass")
    if iter86.get("iter86_audit_returncode") != 0:
        failures.append("iter86 audit must pass")
    expected_hashes = {
        str(ITER86_SUMMARY): sha256(ITER86_SUMMARY),
        str(ITER86_EXTRACTION): sha256(ITER86_EXTRACTION),
        str(ITER86_BACKTEST): sha256(ITER86_BACKTEST),
        str(ITER86_RECEIPT): sha256(ITER86_RECEIPT),
    }
    by_path = {item.get("path"): item for item in iter86.get("source_artifacts", [])}
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter86 source hash mismatch: {path}")


def recompute_score_share(metadata: dict, pair_id: str, failures: list[str]) -> dict[str, str | int]:
    players = metadata.get("config", {}).get("players", [])
    controlled_players = [
        str(player.get("name"))
        for player in players
        if isinstance(player, dict) and player.get("agent") == "mini"
    ]
    if len(controlled_players) != 1:
        failures.append(f"{pair_id} controlled player mapping ambiguous")
        controlled_player = controlled_players[0] if controlled_players else ""
    else:
        controlled_player = controlled_players[0]
    controlled_total = Decimal("0")
    all_total = Decimal("0")
    wins = 0
    round_count = 0
    for round_key, stats in sorted(metadata.get("round_stats", {}).items(), key=lambda item: int(item[0])):
        if not isinstance(stats, dict):
            failures.append(f"{pair_id} invalid round stats {round_key}")
            continue
        scores = stats.get("scores", {})
        if not isinstance(scores, dict) or controlled_player not in scores:
            failures.append(f"{pair_id} missing controlled score {round_key}")
            continue
        controlled_score = Decimal(str(scores[controlled_player]))
        total_score = sum(Decimal(str(score)) for score in scores.values())
        controlled_total += controlled_score
        all_total += total_score
        wins += int(stats.get("winner") == controlled_player)
        round_count += 1
    score_share = Decimal("0") if all_total <= 0 else (controlled_total / all_total)
    return {
        "controlled_player": controlled_player,
        "round_count": round_count,
        "wins": wins,
        "controlled_total": decimal_string(controlled_total),
        "all_total": decimal_string(all_total),
        "score_share": decimal_string(score_share),
    }


def audit_execution_and_metric(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    execution = packets["execution"]
    extraction = packets["extraction"]
    metric = packets["metric"]
    protocol = packets["protocol"]
    preflight = packets["preflight"]
    row_plan = packets["row_plan"]
    recovered = packets["recovered"]
    overlay = packets["overlay"]

    for packet_name, packet in [
        ("summary", summary),
        ("execution", execution),
        ("protocol", protocol),
        ("preflight", preflight),
        ("row_plan", row_plan),
        ("recovered", recovered),
    ]:
        if packet.get("selected_pair_ids") != SELECTED_PAIR_IDS:
            failures.append(f"{packet_name} selected pair ids changed")
    if summary.get("executed_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("summary must execute exactly the six frozen rows")
    if execution.get("executed_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("execution must execute exactly the six frozen rows")
    if protocol.get("executed_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("protocol report must execute exactly the six frozen rows")
    if row_plan.get("row_count") != len(SELECTED_PAIR_IDS):
        failures.append("row plan row count changed")

    for packet_name, packet in [("summary", summary), ("execution", execution), ("protocol", protocol), ("preflight", preflight)]:
        if packet.get("provider_call_ceiling") != TOTAL_CALL_CEILING:
            failures.append(f"{packet_name} provider call ceiling changed")
        if decimal_value(packet.get("provider_spend_ceiling_usd")) != TOTAL_SPEND_CEILING:
            failures.append(f"{packet_name} provider spend ceiling changed")
        if packet.get("per_row_call_limit") != PER_ROW_CALL_LIMIT:
            failures.append(f"{packet_name} per-row call limit changed")
        if decimal_value(packet.get("per_row_spend_limit_usd")) != PER_ROW_SPEND_LIMIT:
            failures.append(f"{packet_name} per-row spend limit changed")
    if int(summary.get("provider_api_calls", 10**9)) > TOTAL_CALL_CEILING:
        failures.append("provider call ceiling exceeded")
    if decimal_value(summary.get("provider_cost_usd")) > TOTAL_SPEND_CEILING:
        failures.append("provider spend ceiling exceeded")
    if preflight.get("adc_access_token_available") is not True:
        failures.append("pass requires ADC token readiness")
    if preflight.get("docker_ready") is not True:
        failures.append("pass requires Docker readiness")
    if overlay.get("all_selected_agent_overlays_materialized") is not True:
        failures.append("all selected overlays must be materialized")

    extraction_rows = extraction.get("rows", [])
    if extraction.get("metric_id") != METRIC_ID or summary.get("metric_id") != METRIC_ID:
        failures.append("metric id changed")
    if extraction.get("all_rows_parsed") is not True or summary.get("fresh_metric_computable") is not True:
        failures.append("fresh metric must parse all rows")
    if extraction.get("metric_collapsed_to_completion_boolean") is not False:
        failures.append("metric must not collapse to completion boolean")
    if summary.get("metric_non_saturated") is not True or metric.get("metric_non_saturated") is not True:
        failures.append("fresh metric must be non-saturated")
    if extraction.get("row_count") != 6 or len(extraction_rows) != 6:
        failures.append("fresh extraction row count must be 6")
    if extraction.get("task_delta_count") != 3 or len(extraction.get("task_deltas", [])) != 3:
        failures.append("fresh task delta count must be 3")
    if extraction.get("task_deltas") != summary.get("task_deltas"):
        failures.append("summary/extraction task deltas mismatch")
    if extraction.get("task_deltas") != metric.get("task_deltas"):
        failures.append("metric report/extraction task deltas mismatch")
    if summary.get("nonzero_task_delta_count", 0) < 1:
        failures.append("fresh metric must include at least one nonzero task delta")
    if summary.get("mixed_direction_signal") is not True:
        failures.append("fresh metric should record mixed-direction signal")

    row_results = {row.get("pair_id"): row for row in execution.get("row_results", [])}
    extraction_by_pair = {row.get("pair_id"): row for row in extraction_rows}
    by_task_condition: dict[tuple[str, str], Decimal] = {}
    for pair_id in SELECTED_PAIR_IDS:
        raw_dir = RAW / pair_id
        row = row_results.get(pair_id, {})
        extracted = extraction_by_pair.get(pair_id, {})
        if row.get("task_surface") != PAIR_TO_TASK[pair_id]:
            failures.append(f"{pair_id} task surface mismatch")
        if extracted.get("condition_label") != PAIR_TO_CONDITION[pair_id]:
            failures.append(f"{pair_id} condition label mismatch")
        if int(row.get("provider_api_calls", 0)) > PER_ROW_CALL_LIMIT:
            failures.append(f"{pair_id} per-row call ceiling exceeded")
        if decimal_value(row.get("provider_cost_usd")) > PER_ROW_SPEND_LIMIT:
            failures.append(f"{pair_id} per-row spend ceiling exceeded")
        for required in ["command_execution.json", "command_stdout.txt", "command_stderr.txt", "raw_manifest.json", "metadata.json"]:
            if not (raw_dir / required).exists():
                failures.append(f"{pair_id} missing raw artifact {required}")
        metadata_path = raw_dir / "metadata.json"
        if metadata_path.exists():
            if extracted.get("metadata_sha256") != sha256(metadata_path):
                failures.append(f"{pair_id} metadata hash mismatch")
            recomputed = recompute_score_share(load_json(metadata_path), pair_id, failures)
            if extracted.get("controlled_player") != recomputed["controlled_player"]:
                failures.append(f"{pair_id} controlled player changed")
            if extracted.get("round_stats_entry_count") != recomputed["round_count"]:
                failures.append(f"{pair_id} round count mismatch")
            if extracted.get("controlled_player_win_count") != recomputed["wins"]:
                failures.append(f"{pair_id} win count mismatch")
            if extracted.get("controlled_player_score_total") != recomputed["controlled_total"]:
                failures.append(f"{pair_id} controlled total mismatch")
            if extracted.get("all_player_score_total") != recomputed["all_total"]:
                failures.append(f"{pair_id} all-player total mismatch")
            if extracted.get("controlled_player_score_share") != recomputed["score_share"]:
                failures.append(f"{pair_id} score-share mismatch")
            by_task_condition[(PAIR_TO_TASK[pair_id], PAIR_TO_CONDITION[pair_id])] = Decimal(
                recomputed["score_share"]
            )
        if pair_id in TELOS_PAIR_IDS:
            if row.get("receipt_required") is not True or row.get("receipt_valid") is not True:
                failures.append(f"{pair_id} Telos receipt must be valid")
        elif row.get("receipt_required") is not False:
            failures.append(f"{pair_id} baseline must not require receipt")

    for delta in extraction.get("task_deltas", []):
        task = delta.get("task_surface")
        baseline = by_task_condition.get((task, "baseline"))
        telos = by_task_condition.get((task, "telos"))
        if baseline is None or telos is None:
            failures.append(f"missing recomputed pair for task {task}")
            continue
        recomputed_delta = decimal_string(telos - baseline)
        if delta.get("delta_telos_minus_baseline") != recomputed_delta:
            failures.append(f"{task} delta mismatch")


def audit_receipt_text_and_hashes(summary: dict, failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"gate receipt invalid: {exc}")
        return
    if receipt.status != summary.get("status"):
        failures.append("gate receipt status mismatch")

    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "provider API calls: `21`",
        "provider spend ceiling: `$10.00`",
        "metric: `task_native_score_share_delta_with_receipt_gates`",
        "metric collapsed to completion boolean: `false`",
        "benchmark/model/SOTA claim: `false`",
        "not an aggregate",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "judged the result on the",
        "not on the old saturated verified-completion boolean",
        "No benchmark,",
        "state-of-the-art result is claimed",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "benchmark-facing discriminating metric execution pilot: pass",
        "selected_pair_count=6",
        "executed_pair_count=6",
        "provider_call_ceiling=96",
        "provider_spend_ceiling_usd=10.00000000",
        "metric_collapsed_to_completion_boolean=false",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
        "This is a leaderboard result",
        "Telos is SOTA",
        "Telos outperforms baseline overall",
    ]:
        if forbidden in result or forbidden in review:
            failures.append(f"claim boundary regression: {forbidden}")

    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")


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
        packets = {
            "summary": load_json(SUMMARY),
            "iter86": load_json(ITER86_PREREQ),
            "execution": load_json(EXECUTION),
            "extraction": load_json(EXTRACTION),
            "metric": load_json(METRIC_REPORT),
            "boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
            "protocol": load_json(PROTOCOL_REPORT),
            "preflight": load_json(PREFLIGHT),
            "row_plan": load_json(ROW_PLAN),
            "recovered": load_json(RECOVERED),
            "overlay": load_json(OVERLAY),
        }
        audit_schemas(packets, failures)
        audit_status_and_boundaries(packets, failures)
        audit_iter86_prerequisites(packets["iter86"], failures)
        audit_execution_and_metric(packets, failures)
        audit_receipt_text_and_hashes(packets["summary"], failures)
        audit_secrets(failures)
    if failures:
        print("iter87 benchmark-facing discriminating metric execution audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter87 benchmark-facing discriminating metric execution audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
