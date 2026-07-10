#!/usr/bin/env python3
"""Run iter87 benchmark-facing discriminating-metric execution pilot."""

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
EXPERIMENT_ID = "iter87_benchmark_facing_discriminating_metric_execution_pilot"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_benchmark_facing_discriminating_metric_execution_pilot.json"

ITER83_SCRIPT = ROOT / "scripts" / "verify_benchmark_facing_protocol_effect_execution_pilot.py"
ITER86_ID = "iter86_discriminating_metric_backtest_on_committed_artifacts"
ITER86_PROOF = ROOT / "experiments" / ITER86_ID / "proof"
ITER86_SUMMARY = ITER86_PROOF / "run_summary.json"
ITER86_EXTRACTION = ITER86_PROOF / "raw_metric_extraction.json"
ITER86_BACKTEST = ITER86_PROOF / "backtest_report.json"
ITER86_RECEIPT = ITER86_PROOF / "valid" / "receipt_discriminating_metric_backtest_on_committed_artifacts.json"

METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
TASKS = ["dummy", "battlesnake", "deterministic_edit"]
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
PER_ROW_SPEND_LIMIT_USD = Decimal("2.00000000")
TOTAL_SPEND_CEILING_USD = Decimal("10.00000000")
WALL_CLOCK_CEILING_SECONDS = 90 * 60
IGNORED_ITER83_BLOCKERS = {"no_interpretable_telos_minus_baseline_signal"}
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


def load_iter83() -> Any:
    spec = importlib.util.spec_from_file_location("iter83_execution_runner", ITER83_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load iter83 runner: {ITER83_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


iter83 = load_iter83()


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
        "schema_version": "telos.benchmark_facing_discriminating_metric_execution.redaction_scan.v1",
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


def configure_iter83_runner() -> None:
    iter83.EXPERIMENT_ID = EXPERIMENT_ID
    iter83.EXPERIMENT = EXPERIMENT
    iter83.PROOF = PROOF
    iter83.RAW = RAW
    iter83.VALID = VALID
    iter83.RESULT = RESULT
    iter83.RECEIPT_NAME = RECEIPT_NAME
    iter83.OUTPUT_ROOT = Path("/tmp/telos-codeclash-discriminating-metric-execution-pilot")
    iter83.RECOVERED_OVERLAY_DIR = PROOF / "recovered_overlay" / "configs" / "mini"
    iter83.PAIR_TO_RECOVERED_AGENT = {
        pair_id: iter83.RECOVERED_OVERLAY_DIR / name
        for pair_id, name in iter83.PAIR_TO_AGENT_DESTINATION_NAME.items()
    }


def validate_iter86() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER86_PROOF)])
    audit = run_capture(["python3", "scripts/audit_discriminating_metric_backtest_on_committed_artifacts.py"])
    summary = read_json(ITER86_SUMMARY)
    extraction = read_json(ITER86_EXTRACTION)
    backtest = read_json(ITER86_BACKTEST)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("metric_id") == METRIC_ID
        and summary.get("metric_computable") is True
        and summary.get("metric_non_saturated") is True
        and summary.get("source_rows_parsed") == 6
        and summary.get("task_deltas_computed") == 3
        and extraction.get("all_rows_parsed") is True
        and backtest.get("metric_non_saturated") is True
        and summary.get("provider_api_calls") == 0
        and decimal_value(summary.get("provider_cost_usd")) == Decimal("0.00000000")
        and summary.get("row_execution_in_this_gate") == 0
        and summary.get("benchmark_result_claimed") is False
        and summary.get("model_superiority_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
    )
    packet = {
        "schema_version": "telos.benchmark_facing_discriminating_metric_execution.iter86_prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter86_status": summary.get("status"),
        "iter86_clean_pass": summary.get("clean_pass"),
        "iter86_metric_id": summary.get("metric_id"),
        "iter86_metric_non_saturated": summary.get("metric_non_saturated"),
        "iter86_source_rows_parsed": summary.get("source_rows_parsed"),
        "iter86_task_deltas_computed": summary.get("task_deltas_computed"),
        "iter86_receipt_validation_returncode": receipt["returncode"],
        "iter86_audit_returncode": audit["returncode"],
        "clean_prerequisites": clean,
        "paid_execution_authorized_by_iter86": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER86_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_discriminating_metric_backtest_on_committed_artifacts.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER86_SUMMARY), "sha256": sha256_file(ITER86_SUMMARY)},
            {"path": relative(ITER86_EXTRACTION), "sha256": sha256_file(ITER86_EXTRACTION)},
            {"path": relative(ITER86_BACKTEST), "sha256": sha256_file(ITER86_BACKTEST)},
            {"path": relative(ITER86_RECEIPT), "sha256": sha256_file(ITER86_RECEIPT)},
        ],
    }
    blockers = [] if clean else ["iter86_discriminating_metric_backtest_not_clean"]
    return packet, blockers


def controlled_player_from_metadata(pair_id: str, metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    players = metadata.get("config", {}).get("players", [])
    controlled_players = [
        str(player.get("name"))
        for player in players
        if isinstance(player, dict) and player.get("agent") == "mini"
    ]
    if len(controlled_players) != 1:
        return None, f"ambiguous_controlled_player:{pair_id}"
    return controlled_players[0], None


def extract_metric_rows(report: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    row_results = {
        str(row.get("pair_id")): row
        for row in report.get("row_results", [])
        if isinstance(row, dict)
    }
    extracted_rows: list[dict[str, Any]] = []
    by_task_condition: dict[tuple[str, str], dict[str, Any]] = {}
    for pair_id in SELECTED_PAIR_IDS:
        report_row = row_results.get(pair_id, {})
        metadata_path = RAW / pair_id / "metadata.json"
        if not metadata_path.exists():
            blockers.append(f"missing_metadata:{pair_id}")
            continue
        metadata = read_json(metadata_path)
        controlled_player, blocker = controlled_player_from_metadata(pair_id, metadata)
        if blocker:
            blockers.append(blocker)
            continue
        round_stats = metadata.get("round_stats", {})
        if not isinstance(round_stats, dict) or not round_stats:
            blockers.append(f"missing_round_stats:{pair_id}")
            continue
        controlled_total = Decimal("0")
        all_total = Decimal("0")
        wins = 0
        round_count = 0
        for round_key, stats in sorted(round_stats.items(), key=lambda item: int(item[0])):
            if not isinstance(stats, dict):
                blockers.append(f"invalid_round_stats:{pair_id}:{round_key}")
                continue
            scores = stats.get("scores", {})
            if not isinstance(scores, dict) or controlled_player not in scores:
                blockers.append(f"missing_controlled_score:{pair_id}:{round_key}")
                continue
            controlled_score = Decimal(str(scores.get(controlled_player)))
            total_score = sum(Decimal(str(score)) for score in scores.values())
            controlled_total += controlled_score
            all_total += total_score
            wins += int(stats.get("winner") == controlled_player)
            round_count += 1
        if all_total <= 0:
            blockers.append(f"non_positive_total_score:{pair_id}")
            score_share = Decimal("0")
        else:
            score_share = (controlled_total / all_total).quantize(Decimal("0.00000001"))
        row = {
            "pair_id": pair_id,
            "task_surface": PAIR_TO_TASK[pair_id],
            "condition_label": PAIR_TO_CONDITION[pair_id],
            "public_config": report_row.get("public_config"),
            "metadata_path": relative(metadata_path),
            "metadata_sha256": sha256_file(metadata_path),
            "controlled_player": controlled_player,
            "controlled_player_agent": "mini",
            "round_stats_entry_count": round_count,
            "controlled_player_win_count": wins,
            "controlled_player_score_total": decimal_string(controlled_total),
            "all_player_score_total": decimal_string(all_total),
            "controlled_player_score_share": decimal_string(score_share),
            "verified_completion_evidence": report_row.get("verified_completion_evidence"),
            "receipt_required": report_row.get("receipt_required"),
            "receipt_valid": report_row.get("receipt_valid"),
            "raw_evidence_present": report_row.get("raw_evidence_present"),
            "provider_api_calls": report_row.get("provider_api_calls"),
            "provider_cost_usd": decimal_string(decimal_value(report_row.get("provider_cost_usd"))),
        }
        extracted_rows.append(row)
        by_task_condition[(row["task_surface"], row["condition_label"])] = row

    task_deltas: list[dict[str, Any]] = []
    for task in TASKS:
        baseline = by_task_condition.get((task, "baseline"))
        telos = by_task_condition.get((task, "telos"))
        if not baseline or not telos:
            blockers.append(f"missing_pair_for_task:{task}")
            continue
        baseline_share = Decimal(str(baseline["controlled_player_score_share"]))
        telos_share = Decimal(str(telos["controlled_player_score_share"]))
        delta = (telos_share - baseline_share).quantize(Decimal("0.00000001"))
        task_deltas.append(
            {
                "task_surface": task,
                "public_config": baseline["public_config"],
                "baseline_pair_id": baseline["pair_id"],
                "telos_pair_id": telos["pair_id"],
                "baseline_score_share": decimal_string(baseline_share),
                "telos_score_share": decimal_string(telos_share),
                "delta_telos_minus_baseline": decimal_string(delta),
                "direction": "positive" if delta > 0 else "negative" if delta < 0 else "zero",
            }
        )

    nonzero_count = sum(Decimal(row["delta_telos_minus_baseline"]) != 0 for row in task_deltas)
    direction_set = {row["direction"] for row in task_deltas}
    packet = {
        "schema_version": "telos.benchmark_facing_discriminating_metric_execution.fresh_metric_extraction.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": METRIC_ID,
        "source_iteration": EXPERIMENT_ID,
        "source_report": relative(PROOF / "protocol_effect_report.json"),
        "source_report_sha256": sha256_file(PROOF / "protocol_effect_report.json"),
        "row_count": len(extracted_rows),
        "expected_row_count": 6,
        "task_delta_count": len(task_deltas),
        "expected_task_delta_count": 3,
        "controlled_player_mapping": "config.players[agent == 'mini'].name",
        "score_field_path": "metadata.round_stats[*].scores[controlled_player]",
        "score_share_formula": "sum(controlled_player_score) / sum(all_player_scores)",
        "pair_delta_formula": "telos_score_share - baseline_score_share for the same public_config",
        "all_rows_parsed": len(extracted_rows) == 6 and len(task_deltas) == 3 and not blockers,
        "metric_collapsed_to_completion_boolean": nonzero_count == 0,
        "nonzero_task_delta_count": nonzero_count,
        "direction_set": sorted(direction_set),
        "mixed_direction_signal": "positive" in direction_set and "negative" in direction_set,
        "aggregate_benchmark_metric_authorized": False,
        "benchmark_result_claimed": False,
        "rows": extracted_rows,
        "task_deltas": task_deltas,
    }
    return packet, blockers


def build_execution_accounting(report: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    runner_blockers = [str(item) for item in report.get("blockers", [])]
    execution_blockers = [item for item in runner_blockers if item not in IGNORED_ITER83_BLOCKERS]
    provider_calls = int(report.get("provider_api_calls", 0))
    provider_cost = decimal_value(report.get("provider_cost_usd"))
    row_results = report.get("row_results", [])
    return {
        "schema_version": "telos.benchmark_facing_discriminating_metric_execution.execution_accounting.v1",
        "experiment_id": EXPERIMENT_ID,
        "runner_reused_from": "iter83_benchmark_facing_protocol_effect_execution_pilot",
        "runner_status": report.get("status"),
        "runner_blockers": runner_blockers,
        "ignored_runner_blockers": sorted(set(runner_blockers) & IGNORED_ITER83_BLOCKERS),
        "execution_blockers_after_metric_redefinition": execution_blockers,
        "execution_failures": report.get("failures", []),
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": report.get("executed_pair_ids", []),
        "executed_pair_count": report.get("executed_pair_count"),
        "row_results": row_results,
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_cost_usd": decimal_string(provider_cost),
        "provider_spend_ceiling_usd": decimal_string(TOTAL_SPEND_CEILING_USD),
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": decimal_string(PER_ROW_SPEND_LIMIT_USD),
        "wall_clock_seconds": summary.get("wall_clock_seconds"),
        "wall_clock_ceiling_seconds": WALL_CLOCK_CEILING_SECONDS,
        "old_verified_completion_metric_used_for_iter87_status": False,
        "fresh_discriminating_metric_required": True,
        "redaction_scan_passed_from_runner": report.get("redaction_scan_passed"),
        "redaction_findings_from_runner": report.get("redaction_findings"),
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
    }


def metric_report(extraction: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.benchmark_facing_discriminating_metric_execution.metric_report.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": METRIC_ID,
        "metric_computable_from_fresh_artifacts": extraction["all_rows_parsed"],
        "metric_non_saturated": extraction["metric_collapsed_to_completion_boolean"] is False,
        "mixed_direction_signal": extraction["mixed_direction_signal"],
        "nonzero_task_delta_count": extraction["nonzero_task_delta_count"],
        "task_deltas": extraction["task_deltas"],
        "interpretation": (
            "Fresh six-row execution produced task-native score-share deltas. These values are "
            "protocol-effect pilot evidence only; they are not a benchmark score, model "
            "superiority result, leaderboard result, SWE-bench result, or SOTA result."
        ),
        "aggregate_benchmark_metric_authorized": False,
        "benchmark_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
    }


def claim_boundary(status: str) -> dict[str, Any]:
    return {
        "schema_version": "telos.benchmark_facing_discriminating_metric_execution.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "allowed_claim": (
            "A bounded six-row provider-backed protocol-effect pilot was evaluated under the "
            "task-native score-share metric."
            if status == "pass"
            else "A bounded six-row discriminating-metric pilot produced blocked/fail evidence."
        ),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
    }


def decide_status(
    *,
    iter86_blockers: list[str],
    execution: dict[str, Any],
    extraction: dict[str, Any],
    extraction_blockers: list[str],
) -> tuple[str, list[str], list[str]]:
    blockers = list(iter86_blockers)
    failures = [str(item) for item in execution.get("execution_failures", [])]
    blockers.extend(str(item) for item in execution.get("execution_blockers_after_metric_redefinition", []))

    executed_pair_ids = execution.get("executed_pair_ids", [])
    if executed_pair_ids != SELECTED_PAIR_IDS:
        blockers.append("not_exactly_six_frozen_rows_executed")
    if set(executed_pair_ids) - set(SELECTED_PAIR_IDS):
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
    if extraction["all_rows_parsed"] is not True:
        blockers.append("fresh_metric_extraction_not_clean_for_all_rows")
    blockers.extend(extraction_blockers)
    if execution.get("redaction_scan_passed_from_runner") is not True:
        failures.append("runner_redaction_scan_failed")
    if execution.get("redaction_findings_from_runner") not in ([], None):
        failures.append("runner_redaction_findings_present")

    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"
    return status, blockers, failures


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter87-benchmark-facing-discriminating-metric-execution-pilot-{status}",
        "task_id": "telos:iter87_benchmark_facing_discriminating_metric_execution_pilot@iter86",
        "agent_id": "codex-local-benchmark-facing-discriminating-metric-pilot-runner",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute the six frozen CodeClash task-condition rows under the iter87 envelope and "
            "evaluate the task-native score-share delta metric from fresh raw artifacts."
        ),
        "acceptance_criteria": [
            "Iter86 receipt and audit validation pass.",
            "Exactly six frozen rows execute and no unselected row executes.",
            "Provider calls stay at or below 96 and provider spend stays at or below $10.00.",
            "Every row has raw artifacts, cost/call accounting, redaction evidence, and receipt validation where required.",
            "The task-native score-share metric is computed from fresh committed metadata.",
            "No GPU, cloud runner, Sentinel mutation, live-domain mutation, benchmark claim, model-superiority claim, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Summary records row execution, ceilings, fresh metric extraction, and claim boundaries.",
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
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/fresh_metric_extraction.json",
                "notes": "Task-native score-share deltas computed from fresh metadata.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-benchmark/no-model/no-SOTA boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter86 validation fails.",
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
    iter86: dict[str, Any],
    execution: dict[str, Any],
    extraction: dict[str, Any],
    metric: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    RESULT.write_text(
        f"""# Iteration 87 Result - Benchmark-Facing Discriminating Metric Execution Pilot

Status: `{status.upper()}`.

## Summary

This gate ran the bounded six-row provider-backed pilot envelope and evaluated the fresh raw
artifacts under `{METRIC_ID}`. It does not make a benchmark, model-superiority, leaderboard,
SWE-bench, production/live-domain, or state-of-the-art claim.

- iter86 validation clean: `{str(iter86['clean_prerequisites']).lower()}`,
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
- metric collapsed to completion boolean: `{str(extraction['metric_collapsed_to_completion_boolean']).lower()}`,
- mixed-direction signal: `{str(metric['mixed_direction_signal']).lower()}`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Fresh Metric Deltas

| Task surface | Baseline score share | Telos score share | Telos-minus-baseline |
| --- | --- | --- | --- |
""",
        encoding="utf-8",
    )
    with RESULT.open("a", encoding="utf-8") as handle:
        for row in extraction["task_deltas"]:
            handle.write(
                f"| `{row['task_surface']}` | `{row['baseline_score_share']}` | "
                f"`{row['telos_score_share']}` | `{row['delta_telos_minus_baseline']}` |\n"
            )
        handle.write(
            """
These are bounded protocol-effect pilot values from six frozen rows. They are not an aggregate
benchmark score and do not establish model superiority or state-of-the-art status.

## Claim Boundary

This gate may claim only bounded provider-backed protocol-effect pilot evidence under a
task-native score-share metric. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

## Evidence

- `proof/iter86_prerequisite_validation.json`
- `proof/execution_accounting_report.json`
- `proof/fresh_metric_extraction.json`
- `proof/discriminating_metric_report.json`
- `proof/claim_boundary.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_benchmark_facing_discriminating_metric_execution_pilot.json`
"""
        )

    command_lines = [
        f"benchmark-facing discriminating metric execution pilot: {status}",
        f"iter86_receipt_validation_returncode={iter86['iter86_receipt_validation_returncode']}",
        f"iter86_audit_returncode={iter86['iter86_audit_returncode']}",
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
        f"metric_collapsed_to_completion_boolean={str(extraction['metric_collapsed_to_completion_boolean']).lower()}",
        f"mixed_direction_signal={str(metric['mixed_direction_signal']).lower()}",
        "benchmark_result_claimed=false",
        "model_superiority_claimed=false",
        "state_of_the_art_result_claimed=false",
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
        f"""# Iteration 87 Review

The gate used the frozen six-row provider-backed execution envelope and judged the result on the
fresh `{METRIC_ID}` extraction, not on the old saturated verified-completion boolean. The evidence
remains a bounded protocol-effect pilot.

- status: `{status}`,
- executed row count: `{execution['executed_pair_count']}`,
- provider API calls: `{execution['provider_api_calls']}`,
- provider cost: `${Decimal(execution['provider_cost_usd']):.8f}`,
- fresh metric rows parsed: `{extraction['row_count']}`,
- task deltas computed: `{extraction['task_delta_count']}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

No benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
state-of-the-art result is claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    configure_iter83_runner()
    runner_rc = iter83.main()
    iter86, iter86_blockers = validate_iter86()
    write_json(PROOF / "iter86_prerequisite_validation.json", iter86)

    runner_summary = read_json(PROOF / "run_summary.json")
    runner_report = read_json(PROOF / "protocol_effect_report.json")
    execution = build_execution_accounting(runner_report, runner_summary)
    write_json(PROOF / "execution_accounting_report.json", execution)

    extraction, extraction_blockers = extract_metric_rows(runner_report)
    write_json(PROOF / "fresh_metric_extraction.json", extraction)
    metric = metric_report(extraction)
    write_json(PROOF / "discriminating_metric_report.json", metric)

    status, blockers, failures = decide_status(
        iter86_blockers=iter86_blockers,
        execution=execution,
        extraction=extraction,
        extraction_blockers=extraction_blockers,
    )
    if runner_rc != 0 and not failures:
        failures.append("underlying_execution_runner_returned_nonzero")
        status = "fail"

    boundary = claim_boundary(status)
    write_json(PROOF / "claim_boundary.json", boundary)
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(
        status=status,
        iter86=iter86,
        execution=execution,
        extraction=extraction,
        metric=metric,
        blockers=blockers,
        failures=failures,
    )
    scan = redaction_scan()
    if not scan["passed"] and "redaction_scan_failed" not in failures:
        failures.append("redaction_scan_failed")
        status = "fail"
        boundary = claim_boundary(status)
        write_json(PROOF / "claim_boundary.json", boundary)
        write_json(VALID / RECEIPT_NAME, build_receipt(status))
        write_text_artifacts(
            status=status,
            iter86=iter86,
            execution=execution,
            extraction=extraction,
            metric=metric,
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
                "Fresh six-row provider-backed execution can be judged by task-native "
                "score-share deltas without collapsing to the old completion boolean."
                if status == "pass"
                else "The discriminating-metric execution pilot published bounded blocked/fail evidence."
            ),
            "next_action": (
                "adjudicate whether the fresh discriminating signal justifies a larger external benchmark design"
                if status == "pass"
                else "recover only the named iter87 blocker before retrying paid execution"
            ),
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/execution_accounting_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/fresh_metric_extraction.json",
                f"experiments/{EXPERIMENT_ID}/proof/discriminating_metric_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary = {
        "schema_version": "telos.benchmark_facing_discriminating_metric_execution.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter86_status": iter86["iter86_status"],
        "iter86_clean_pass": iter86["iter86_clean_pass"],
        "iter86_receipt_validation_returncode": iter86["iter86_receipt_validation_returncode"],
        "iter86_audit_returncode": iter86["iter86_audit_returncode"],
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
        "wall_clock_ceiling_seconds": WALL_CLOCK_CEILING_SECONDS,
        "metric_id": METRIC_ID,
        "fresh_metric_computable": extraction["all_rows_parsed"],
        "fresh_metric_rows_parsed": extraction["row_count"],
        "fresh_task_deltas_computed": extraction["task_delta_count"],
        "metric_collapsed_to_completion_boolean": extraction["metric_collapsed_to_completion_boolean"],
        "metric_non_saturated": extraction["metric_collapsed_to_completion_boolean"] is False,
        "nonzero_task_delta_count": extraction["nonzero_task_delta_count"],
        "mixed_direction_signal": extraction["mixed_direction_signal"],
        "task_deltas": extraction["task_deltas"],
        "runner_status": execution["runner_status"],
        "ignored_runner_blockers": execution["ignored_runner_blockers"],
        "old_verified_completion_metric_used_for_iter87_status": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
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

    print(f"benchmark-facing discriminating metric execution pilot: {status}")
    print(f"selected_pair_count={len(SELECTED_PAIR_IDS)}")
    print(f"executed_pair_count={execution['executed_pair_count']}")
    print(f"provider_api_calls={execution['provider_api_calls']}")
    print(f"provider_call_ceiling={TOTAL_CALL_CEILING}")
    print(f"provider_cost_usd={execution['provider_cost_usd']}")
    print(f"provider_spend_ceiling_usd={decimal_string(TOTAL_SPEND_CEILING_USD)}")
    print(f"metric_id={METRIC_ID}")
    print(f"fresh_metric_rows_parsed={extraction['row_count']}")
    print(f"fresh_task_deltas_computed={extraction['task_delta_count']}")
    print(
        "metric_collapsed_to_completion_boolean="
        f"{str(extraction['metric_collapsed_to_completion_boolean']).lower()}"
    )
    print(f"mixed_direction_signal={str(extraction['mixed_direction_signal']).lower()}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
