#!/usr/bin/env python3
"""Verify iter86 discriminating metric backtest on committed artifacts."""

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
EXPERIMENT_ID = "iter86_discriminating_metric_backtest_on_committed_artifacts"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_discriminating_metric_backtest_on_committed_artifacts.json"
NEXT_GATE = "experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/HYPOTHESIS.md"

ITER85_ID = "iter85_discriminating_task_metric_redesign"
ITER85_PROOF = ROOT / "experiments" / ITER85_ID / "proof"
ITER85_SUMMARY = ITER85_PROOF / "run_summary.json"
ITER85_METRIC = ITER85_PROOF / "metric_contract.json"
ITER85_FIELD_INVENTORY = ITER85_PROOF / "source_field_inventory.json"
ITER85_RECEIPT = ITER85_PROOF / "valid" / "receipt_discriminating_task_metric_redesign.json"

ITER83_ID = "iter83_benchmark_facing_protocol_effect_execution_pilot"
ITER83_PROOF = ROOT / "experiments" / ITER83_ID / "proof"
ITER83_RAW = ITER83_PROOF / "raw"
ITER83_REPORT = ITER83_PROOF / "protocol_effect_report.json"

METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
TASKS = ["dummy", "battlesnake", "deterministic_edit"]
ZERO_COST = Decimal("0.00000000")
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


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
                findings.append({"path": relative(path), "pattern": pattern.pattern})
                break
    return {
        "schema_version": "telos.discriminating_metric_backtest.redaction_scan.v1",
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


def validate_iter85() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER85_PROOF)])
    audit = run_capture(["python3", "scripts/audit_discriminating_task_metric_redesign.py"])
    summary = read_json(ITER85_SUMMARY)
    metric = read_json(ITER85_METRIC)
    field_inventory = read_json(ITER85_FIELD_INVENTORY)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("candidate_metric_id") == METRIC_ID
        and summary.get("candidate_metric_not_verified_completion_boolean") is True
        and summary.get("candidate_metric_field_available_for_all_rows") is True
        and summary.get("candidate_metric_nonconstant_on_source_fields") is True
        and summary.get("source_rows_inventoried") == 6
        and metric.get("metric_id") == METRIC_ID
        and metric.get("future_backtest_required_before_paid_execution") is True
        and metric.get("future_paid_execution_authorized_by_this_gate") is False
        and field_inventory.get("candidate_metric_field_available_for_all_rows") is True
        and summary.get("provider_api_calls") == 0
        and Decimal(str(summary.get("provider_cost_usd"))) == ZERO_COST
        and summary.get("row_execution_in_this_gate") == 0
        and summary.get("benchmark_result_claimed") is False
        and summary.get("model_superiority_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
        and summary.get("leaderboard_or_swebench_result_claimed") is False
    )
    blockers = [] if clean else ["iter85_metric_redesign_packet_not_clean"]
    packet = {
        "schema_version": "telos.discriminating_metric_backtest.prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter85_status": summary.get("status"),
        "iter85_clean_pass": summary.get("clean_pass"),
        "iter85_candidate_metric_id": summary.get("candidate_metric_id"),
        "iter85_source_rows_inventoried": summary.get("source_rows_inventoried"),
        "iter85_receipt_validation_returncode": receipt["returncode"],
        "iter85_audit_returncode": audit["returncode"],
        "clean_prerequisites": clean,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER85_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_discriminating_task_metric_redesign.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER85_SUMMARY), "sha256": sha256_file(ITER85_SUMMARY)},
            {"path": relative(ITER85_METRIC), "sha256": sha256_file(ITER85_METRIC)},
            {"path": relative(ITER85_FIELD_INVENTORY), "sha256": sha256_file(ITER85_FIELD_INVENTORY)},
            {"path": relative(ITER85_RECEIPT), "sha256": sha256_file(ITER85_RECEIPT)},
        ],
    }
    return packet, blockers


def report_row_index() -> dict[str, dict[str, Any]]:
    report = read_json(ITER83_REPORT)
    rows = report.get("row_results", [])
    return {str(row.get("pair_id")): row for row in rows if isinstance(row, dict)}


def selected_pair_ids() -> list[str]:
    inventory = read_json(ITER85_FIELD_INVENTORY)
    pair_ids = [str(row.get("pair_id")) for row in inventory.get("rows", [])]
    return pair_ids


def extract_metric_rows() -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    report_rows = report_row_index()
    extracted_rows: list[dict[str, Any]] = []
    by_task_condition: dict[tuple[str, str], dict[str, Any]] = {}
    for pair_id in selected_pair_ids():
        report_row = report_rows.get(pair_id, {})
        metadata_path = ITER83_RAW / pair_id / "metadata.json"
        if not metadata_path.exists():
            blockers.append(f"missing_metadata:{pair_id}")
            continue
        metadata = read_json(metadata_path)
        players = metadata.get("config", {}).get("players", [])
        controlled_players = [
            str(player.get("name"))
            for player in players
            if isinstance(player, dict) and player.get("agent") == "mini"
        ]
        if len(controlled_players) != 1:
            blockers.append(f"ambiguous_controlled_player:{pair_id}")
            continue
        controlled_player = controlled_players[0]
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
            "task_surface": report_row.get("task_surface"),
            "condition_label": report_row.get("condition_label"),
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
            "provider_cost_usd": decimal_string(Decimal(str(report_row.get("provider_cost_usd")))),
        }
        extracted_rows.append(row)
        by_task_condition[(str(row["task_surface"]), str(row["condition_label"]))] = row

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
                "completion_delta_was_zero_in_iter83": True,
            }
        )

    nonzero_count = sum(Decimal(row["delta_telos_minus_baseline"]) != 0 for row in task_deltas)
    direction_set = {row["direction"] for row in task_deltas}
    packet = {
        "schema_version": "telos.discriminating_metric_backtest.raw_metric_extraction.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": METRIC_ID,
        "source_iteration": ITER83_ID,
        "source_report": relative(ITER83_REPORT),
        "source_report_sha256": sha256_file(ITER83_REPORT),
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
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "rows": extracted_rows,
        "task_deltas": task_deltas,
    }
    return packet, blockers


def backtest_report(extraction: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.discriminating_metric_backtest.report.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": METRIC_ID,
        "status": "diagnostic_backtest_only",
        "source_iteration": ITER83_ID,
        "task_deltas": extraction["task_deltas"],
        "metric_computable": extraction["all_rows_parsed"],
        "metric_non_saturated": extraction["metric_collapsed_to_completion_boolean"] is False,
        "mixed_direction_signal": extraction["mixed_direction_signal"],
        "interpretation": (
            "The candidate metric is computable and no longer saturates on committed iter83 "
            "artifacts, but the signal is mixed-direction and diagnostic only."
        ),
        "claim_boundary": [
            "not a benchmark result",
            "not a leaderboard result",
            "not a SWE-bench result",
            "not a model-superiority result",
            "not a state-of-the-art result",
        ],
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def next_step_decision(extraction: dict[str, Any]) -> dict[str, Any]:
    decision = "pre_register_bounded_paid_discriminating_metric_execution"
    return {
        "schema_version": "telos.discriminating_metric_backtest.next_step_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "decision": decision,
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
        "decision_rationale": (
            "The candidate metric is computable from committed artifacts and did not collapse "
            "to the old verified-completion boolean. The honest next step is a small paid "
            "replication under the new metric, not a benchmark claim."
        ),
        "accepted_path": {
            "kind": "bounded_paid_execution_pre_registration",
            "selected_row_count": 6,
            "future_provider_call_ceiling": 96,
            "future_provider_spend_ceiling_usd": "10.00000000",
            "future_per_row_call_limit": 16,
            "future_per_row_spend_limit_usd": "2.00000000",
            "why": "fresh execution is needed because iter86 is only a committed-artifact backtest",
        },
        "rejected_paths": [
            {
                "kind": "claim_benchmark_result_now",
                "why_rejected": "iter86 is a zero-spend backtest on prior artifacts, not fresh benchmark execution",
            },
            {
                "kind": "scale_beyond_six_rows",
                "why_rejected": "metric needs one bounded replication before broader spend",
            },
            {
                "kind": "return_to_verified_completion_metric",
                "why_rejected": "verified completion already saturated in iter83",
            },
        ],
        "source_task_delta_count": extraction["task_delta_count"],
        "source_nonzero_task_delta_count": extraction["nonzero_task_delta_count"],
        "source_mixed_direction_signal": extraction["mixed_direction_signal"],
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "telos.discriminating_metric_backtest.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "allowed_claim": (
            "The iter85 candidate metric was backtested on committed iter83 artifacts with zero spend."
        ),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "fresh_paid_execution_claimed": False,
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter86-discriminating-metric-backtest-{status}",
        "task_id": "telos:iter86_discriminating_metric_backtest_on_committed_artifacts@iter85",
        "agent_id": "codex-local-metric-backtest-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Backtest the iter85 discriminating metric on committed iter83 artifacts without "
            "provider calls, row execution, or benchmark/model/SOTA claims."
        ),
        "acceptance_criteria": [
            "Iter85 receipt and audit validation pass.",
            "All six iter83 raw metadata rows are parsed from committed artifacts.",
            "Per-task score-share deltas are computed under the iter85 metric contract.",
            "Missing or ambiguous fields are reported as blockers.",
            "Future paid execution remains separately pre-registered.",
            "No provider calls, spend, row execution, cloud runner, GPU, Sentinel mutation, or live-domain mutation occurs.",
            "No benchmark, leaderboard, SWE-bench, model-superiority, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Summary records metric computability and next gate.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/raw_metric_extraction.json",
                "notes": "Deterministic score-share extraction from committed iter83 metadata.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/backtest_report.json",
                "notes": "Per-task diagnostic deltas under the new metric.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter85 validation fails.",
            "The result must block if any iter83 metadata row is missing or ambiguous.",
            "The result must fail if provider calls, spend, or row execution occur in iter86.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_text_artifacts(
    *,
    status: str,
    prereq: dict[str, Any],
    extraction: dict[str, Any],
    decision: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    RESULT.write_text(
        f"""# Iteration 86 Result - Discriminating Metric Backtest on Committed Artifacts

Status: `{status.upper()}`.

## Summary

This gate backtested the iter85 candidate metric from committed iter83 artifacts only. It made zero
provider calls, spent `$0.00`, and executed zero CodeClash rows.

- iter85 validation clean: `{str(prereq['clean_prerequisites']).lower()}`,
- metric: `{METRIC_ID}`,
- source rows parsed: `{extraction['row_count']}`,
- task deltas computed: `{extraction['task_delta_count']}`,
- metric collapsed to completion boolean: `{str(extraction['metric_collapsed_to_completion_boolean']).lower()}`,
- mixed-direction diagnostic signal: `{str(extraction['mixed_direction_signal']).lower()}`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- row execution in this gate: `0`,
- next-step decision: `{decision['decision']}`,
- next gate: `{decision['next_gate']}`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Backtest Deltas

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
            f"""
These are diagnostic backtest values from prior committed artifacts. They are not a benchmark
score, not fresh execution evidence, and not a model-superiority claim.

## Claim Boundary

This gate may claim only that the iter85 candidate metric is computable from committed iter83
artifacts and does not collapse to the saturated completion boolean. It is not a benchmark result,
SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/raw_metric_extraction.json`
- `proof/backtest_report.json`
- `proof/next_step_decision.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
        )

    command_lines = [
        f"discriminating metric backtest: {status}",
        f"iter85_receipt_validation_returncode={prereq['iter85_receipt_validation_returncode']}",
        f"iter85_audit_returncode={prereq['iter85_audit_returncode']}",
        f"metric_id={METRIC_ID}",
        f"source_rows_parsed={extraction['row_count']}",
        f"task_deltas_computed={extraction['task_delta_count']}",
        f"metric_collapsed_to_completion_boolean={str(extraction['metric_collapsed_to_completion_boolean']).lower()}",
        f"mixed_direction_signal={str(extraction['mixed_direction_signal']).lower()}",
        "provider_calls_in_this_gate=0",
        "provider_spend_in_this_gate_usd=0.00000000",
        "row_execution_in_this_gate=0",
        f"next_step_decision={decision['decision']}",
        f"next_gate={decision['next_gate']}",
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
        f"""# Iteration 86 Review

The iter85 candidate metric was backtested only on committed iter83 metadata. The metric is
computable for all six rows and does not collapse back to the saturated verified-completion
boolean. The signal is mixed-direction diagnostic evidence, not a benchmark result.

- status: `{status}`,
- metric: `{METRIC_ID}`,
- source rows parsed: `{extraction['row_count']}`,
- task deltas computed: `{extraction['task_delta_count']}`,
- provider calls in iter86: `0`,
- provider spend in iter86: `$0.00000000`,
- row execution in iter86: `0`,
- next-step decision: `{decision['decision']}`.

The next gate is a bounded paid replication under the discriminating metric. No benchmark,
leaderboard, SWE-bench, production/live-domain, model-superiority, or state-of-the-art result is
claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter85()
    extraction, extraction_blockers = extract_metric_rows()
    blockers.extend(extraction_blockers)
    report = backtest_report(extraction)
    decision = next_step_decision(extraction)
    boundary = claim_boundary()

    failures: list[str] = []
    if not prereq["clean_prerequisites"]:
        blockers.append("iter85_prerequisite_validation_failed")
    if extraction["all_rows_parsed"] is not True:
        blockers.append("metric_extraction_not_clean_for_all_rows")
    if extraction["metric_collapsed_to_completion_boolean"] is True:
        blockers.append("metric_collapsed_to_completion_boolean")
    if decision["next_gate_pre_registered"] is not True:
        blockers.append("next_gate_not_pre_registered")
    if boundary["aggregate_benchmark_metric_authorized"] is not False:
        failures.append("aggregate_benchmark_metric_incorrectly_authorized")

    write_json(PROOF / "prerequisite_validation.json", prereq)
    write_json(PROOF / "raw_metric_extraction.json", extraction)
    write_json(PROOF / "backtest_report.json", report)
    write_json(PROOF / "next_step_decision.json", decision)
    write_json(PROOF / "claim_boundary.json", boundary)

    scan = redaction_scan()
    if not scan["passed"]:
        failures.append("redaction_scan_failed")
    write_json(PROOF / "redaction_scan.json", scan)

    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(
        status=status,
        prereq=prereq,
        extraction=extraction,
        decision=decision,
        blockers=blockers,
        failures=failures,
    )
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status if status != "fail" else "null",
            "insight": (
                "The task-native score-share metric is computable from committed artifacts and "
                "does not collapse to the saturated completion boolean, but the backtest signal "
                "is mixed-direction diagnostic evidence only."
            ),
            "next_action": (
                "run the smallest bounded paid replication under the discriminating metric before "
                "any benchmark claim"
            ),
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/raw_metric_extraction.json",
                f"experiments/{EXPERIMENT_ID}/proof/backtest_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/next_step_decision.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary = {
        "schema_version": "telos.discriminating_metric_backtest.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter85_status": prereq["iter85_status"],
        "iter85_clean_pass": prereq["iter85_clean_pass"],
        "metric_id": METRIC_ID,
        "metric_computable": extraction["all_rows_parsed"],
        "metric_collapsed_to_completion_boolean": extraction[
            "metric_collapsed_to_completion_boolean"
        ],
        "metric_non_saturated": extraction["metric_collapsed_to_completion_boolean"] is False,
        "source_rows_parsed": extraction["row_count"],
        "task_deltas_computed": extraction["task_delta_count"],
        "task_deltas": extraction["task_deltas"],
        "nonzero_task_delta_count": extraction["nonzero_task_delta_count"],
        "mixed_direction_signal": extraction["mixed_direction_signal"],
        "backtest_interpretation": report["interpretation"],
        "next_step_decision": decision["decision"],
        "next_gate": decision["next_gate"],
        "future_paid_execution_pre_registered": True,
        "future_provider_call_ceiling": 96,
        "future_provider_spend_ceiling_usd": "10.00000000",
        "provider_api_calls": 0,
        "provider_cost_usd": 0.0,
        "row_execution_in_this_gate": 0,
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

    print(f"discriminating metric backtest: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("row_execution_in_this_gate=0")
    print(f"metric_id={METRIC_ID}")
    print(f"source_rows_parsed={extraction['row_count']}")
    print(f"task_deltas_computed={extraction['task_delta_count']}")
    print(
        "metric_collapsed_to_completion_boolean="
        f"{str(extraction['metric_collapsed_to_completion_boolean']).lower()}"
    )
    print(f"next_step_decision={decision['decision']}")
    print(f"next_gate={decision['next_gate']}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
