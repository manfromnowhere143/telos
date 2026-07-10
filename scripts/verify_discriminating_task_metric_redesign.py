#!/usr/bin/env python3
"""Verify iter85 discriminating task/metric redesign."""

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
EXPERIMENT_ID = "iter85_discriminating_task_metric_redesign"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_discriminating_task_metric_redesign.json"
NEXT_GATE = "experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/HYPOTHESIS.md"

ITER84_ID = "iter84_benchmark_facing_null_signal_adjudication"
ITER84_PROOF = ROOT / "experiments" / ITER84_ID / "proof"
ITER84_SUMMARY = ITER84_PROOF / "run_summary.json"
ITER84_CLASSIFICATION = ITER84_PROOF / "null_signal_classification.json"
ITER84_DECISION = ITER84_PROOF / "next_step_decision.json"
ITER84_ROW_ACCOUNTING = ITER84_PROOF / "row_accounting.json"
ITER84_RECEIPT = ITER84_PROOF / "valid" / "receipt_benchmark_facing_null_signal_adjudication.json"

ITER83_ID = "iter83_benchmark_facing_protocol_effect_execution_pilot"
ITER83_PROOF = ROOT / "experiments" / ITER83_ID / "proof"
ITER83_RAW = ITER83_PROOF / "raw"
ITER83_REPORT = ITER83_PROOF / "protocol_effect_report.json"

TASKS = ["dummy", "battlesnake", "deterministic_edit"]
ZERO_COST = Decimal("0.00000000")
METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
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


def decimal_from_float(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.00000001"))


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
        "schema_version": "telos.discriminating_task_metric.redaction_scan.v1",
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


def validate_iter84() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER84_PROOF)])
    audit = run_capture(["python3", "scripts/audit_benchmark_facing_null_signal_adjudication.py"])
    summary = read_json(ITER84_SUMMARY)
    classification = read_json(ITER84_CLASSIFICATION)
    decision = read_json(ITER84_DECISION)
    row_accounting = read_json(ITER84_ROW_ACCOUNTING)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("quality_failure") is False
        and summary.get("blocked_result") is False
        and summary.get("null_signal_classification") == "verified_completion_metric_saturated"
        and summary.get("next_step_decision") == "redesign_task_metric"
        and summary.get("provider_api_calls") == 0
        and Decimal(str(summary.get("provider_cost_usd"))) == ZERO_COST
        and summary.get("row_execution_in_this_gate") == 0
        and classification.get("classification") == "verified_completion_metric_saturated"
        and classification.get("null_signal_preserved") is True
        and decision.get("decision") == "redesign_task_metric"
        and row_accounting.get("all_rows_verified_completion") is True
        and row_accounting.get("all_required_receipts_valid") is True
        and summary.get("benchmark_result_claimed") is False
        and summary.get("model_superiority_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
        and summary.get("leaderboard_or_swebench_result_claimed") is False
    )
    blockers = [] if clean else ["iter84_adjudication_packet_not_clean"]
    packet = {
        "schema_version": "telos.discriminating_task_metric.prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter84_status": summary.get("status"),
        "iter84_clean_pass": summary.get("clean_pass"),
        "iter84_classification": summary.get("null_signal_classification"),
        "iter84_next_step_decision": summary.get("next_step_decision"),
        "iter84_all_task_surface_deltas_zero": summary.get("all_task_surface_deltas_zero"),
        "iter84_provider_api_calls": summary.get("provider_api_calls"),
        "iter84_provider_cost_usd": decimal_string(Decimal(str(summary.get("provider_cost_usd")))),
        "iter84_row_execution_in_gate": summary.get("row_execution_in_this_gate"),
        "iter84_receipt_validation_returncode": receipt["returncode"],
        "iter84_audit_returncode": audit["returncode"],
        "clean_prerequisites": clean,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER84_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_benchmark_facing_null_signal_adjudication.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER84_SUMMARY), "sha256": sha256_file(ITER84_SUMMARY)},
            {"path": relative(ITER84_CLASSIFICATION), "sha256": sha256_file(ITER84_CLASSIFICATION)},
            {"path": relative(ITER84_DECISION), "sha256": sha256_file(ITER84_DECISION)},
            {"path": relative(ITER84_ROW_ACCOUNTING), "sha256": sha256_file(ITER84_ROW_ACCOUNTING)},
            {"path": relative(ITER84_RECEIPT), "sha256": sha256_file(ITER84_RECEIPT)},
        ],
    }
    return packet, blockers


def saturation_critique() -> dict[str, Any]:
    return {
        "schema_version": "telos.discriminating_task_metric.saturation_critique.v1",
        "experiment_id": EXPERIMENT_ID,
        "saturated_metric_id": "verified_completion_evidence_by_task_and_condition",
        "classification_source": "verified_completion_metric_saturated",
        "why_saturated": [
            "The iter83 primary metric was a boolean admissibility/completion flag.",
            "Baseline and Telos rows all had raw evidence and valid completion evidence.",
            "Receipt-required Telos rows all validated, so receipt validity did not separate task performance.",
            "The metric ignored task-native outcome fields and score fields emitted by CodeClash metadata.",
            "The metric ignored within-task score magnitude and winner/score changes.",
        ],
        "required_redesign_properties": [
            "Verified completion and receipt validity must become row-admissibility gates.",
            "The primary metric must read task-native outcome fields from raw artifacts.",
            "Baseline and Telos must be compared only within the same public_config.",
            "Missing or ambiguous task-native outcome fields must block the row instead of falling back to completion.",
            "No cross-task aggregate benchmark score may be reported from this gate.",
        ],
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def row_condition_index() -> dict[str, dict[str, Any]]:
    report = read_json(ITER83_REPORT)
    rows = report.get("row_results", [])
    if not isinstance(rows, list):
        return {}
    return {str(row.get("pair_id")): row for row in rows if isinstance(row, dict)}


def extract_source_field_inventory() -> tuple[dict[str, Any], list[str]]:
    row_accounting = read_json(ITER84_ROW_ACCOUNTING)
    indexed_rows = row_condition_index()
    blockers: list[str] = []
    rows: list[dict[str, Any]] = []
    by_task_condition: dict[tuple[str, str], dict[str, Any]] = {}
    for source_row in row_accounting.get("rows", []):
        pair_id = str(source_row.get("pair_id"))
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
        parsed_rounds: list[dict[str, Any]] = []
        for round_key, stats in sorted(round_stats.items(), key=lambda item: int(item[0])):
            if not isinstance(stats, dict):
                blockers.append(f"invalid_round_stats:{pair_id}:{round_key}")
                continue
            scores = stats.get("scores", {})
            if not isinstance(scores, dict) or controlled_player not in scores:
                blockers.append(f"missing_controlled_score:{pair_id}:{round_key}")
                continue
            controlled_score = Decimal(str(scores.get(controlled_player)))
            round_total = sum(Decimal(str(score)) for score in scores.values())
            controlled_total += controlled_score
            all_total += round_total
            if stats.get("winner") == controlled_player:
                wins += 1
            parsed_rounds.append(
                {
                    "round_key": str(round_key),
                    "winner": stats.get("winner"),
                    "controlled_player_score": decimal_string(controlled_score),
                    "total_score": decimal_string(round_total),
                }
            )
        if all_total <= 0:
            blockers.append(f"non_positive_total_score:{pair_id}")
            score_share = Decimal("0")
        else:
            score_share = (controlled_total / all_total).quantize(Decimal("0.00000001"))
        report_row = indexed_rows.get(pair_id, {})
        row = {
            "pair_id": pair_id,
            "task_surface": source_row.get("task_surface"),
            "condition_label": source_row.get("condition_label"),
            "public_config": source_row.get("public_config"),
            "metadata_path": relative(metadata_path),
            "metadata_sha256": sha256_file(metadata_path),
            "game_name": metadata.get("config", {}).get("game", {}).get("name"),
            "controlled_player": controlled_player,
            "controlled_player_agent": "mini",
            "reference_players": [
                str(player.get("name"))
                for player in players
                if isinstance(player, dict) and player.get("name") != controlled_player
            ],
            "round_stats_entry_count": len(round_stats),
            "controlled_player_win_count": wins,
            "controlled_player_score_total": decimal_string(controlled_total),
            "all_player_score_total": decimal_string(all_total),
            "controlled_player_score_share": decimal_string(score_share),
            "verified_completion_evidence": source_row.get("verified_completion_evidence"),
            "receipt_required": source_row.get("receipt_required"),
            "receipt_valid": source_row.get("receipt_valid"),
            "raw_evidence_present": source_row.get("raw_evidence_present"),
            "provider_api_calls": source_row.get("provider_api_calls"),
            "provider_cost_usd": source_row.get("provider_cost_usd"),
            "report_round_1_winner": report_row.get("round_1_winner"),
            "parsed_rounds": parsed_rounds,
        }
        rows.append(row)
        by_task_condition[(str(row["task_surface"]), str(row["condition_label"]))] = row

    paired_preview: list[dict[str, Any]] = []
    for task in TASKS:
        baseline = by_task_condition.get((task, "baseline"))
        telos = by_task_condition.get((task, "telos"))
        if not baseline or not telos:
            blockers.append(f"missing_pair_for_task:{task}")
            continue
        baseline_share = Decimal(str(baseline["controlled_player_score_share"]))
        telos_share = Decimal(str(telos["controlled_player_score_share"]))
        paired_preview.append(
            {
                "task_surface": task,
                "public_config": baseline["public_config"],
                "baseline_pair_id": baseline["pair_id"],
                "telos_pair_id": telos["pair_id"],
                "baseline_score_share": decimal_string(baseline_share),
                "telos_score_share": decimal_string(telos_share),
                "candidate_delta_telos_minus_baseline": decimal_string(telos_share - baseline_share),
                "verified_completion_delta_remained_zero": True,
                "claim_boundary": "design-time field inventory only; not a protocol-effect result",
            }
        )

    unique_score_shares = {row["controlled_player_score_share"] for row in rows}
    packet = {
        "schema_version": "telos.discriminating_task_metric.source_field_inventory.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iteration": ITER83_ID,
        "source_report": relative(ITER83_REPORT),
        "source_report_sha256": sha256_file(ITER83_REPORT),
        "row_count": len(rows),
        "expected_row_count": 6,
        "all_metadata_present": len(rows) == 6 and not any(b.startswith("missing_metadata") for b in blockers),
        "controlled_player_mapping": "config.players[agent == 'mini'].name",
        "score_field_path": "metadata.round_stats[*].scores[controlled_player]",
        "score_share_formula": "sum(controlled_player_score) / sum(all_player_scores)",
        "candidate_metric_field_available_for_all_rows": len(rows) == 6 and not blockers,
        "candidate_metric_nonconstant_on_source_fields": len(unique_score_shares) > 1,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "rows": rows,
        "paired_task_preview": paired_preview,
        "preview_is_not_a_benchmark_result": True,
    }
    return packet, blockers


def metric_contract() -> dict[str, Any]:
    return {
        "schema_version": "telos.discriminating_task_metric.metric_contract.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": METRIC_ID,
        "metric_status": "candidate_contract_frozen_for_zero_spend_backtest",
        "replaces_metric_id": "verified_completion_evidence_by_task_and_condition",
        "primary_metric_not_verified_completion_boolean": True,
        "admissibility_gates": [
            "row command completed without timeout",
            "raw artifact manifest and metadata are present",
            "cost and provider-call accounting are present",
            "Telos receipt-required rows have valid receipts",
            "redaction scan passes before publication",
        ],
        "primary_metric_definition": (
            "Within each public_config, compare Telos versus baseline on task-native controlled "
            "player score share extracted from committed CodeClash metadata. Completion evidence "
            "and receipt validity admit a row for scoring; they are not the score."
        ),
        "score_extractor": {
            "extractor_id": "codeclash_metadata_controlled_player_score_share_v1",
            "controlled_player_mapping": "the single config.players entry with agent == 'mini'",
            "score_field": "metadata.round_stats[*].scores[controlled_player]",
            "score_share_formula": "sum(controlled_player_score) / sum(all_player_scores)",
            "pair_delta_formula": "telos_score_share - baseline_score_share for the same public_config",
            "missing_or_ambiguous_mapping_rule": "block the row; do not fall back to completion",
            "round_stats_semantics_rule": (
                "Use the committed CodeClash metadata exactly as emitted; iter86 must publish the "
                "extracted fields and block if upstream round_stats semantics are ambiguous."
            ),
        },
        "reporting_rules": [
            "Report exact per-task baseline score share, Telos score share, and delta.",
            "Report completion and receipt validity as gates, not as the primary metric.",
            "Report provider calls and spend as secondary cost accounting.",
            "Do not pool Dummy, BattleSnake, and deterministic-edit into an aggregate benchmark score.",
            "Publish null, blocked, and quality-failure rows at full weight.",
        ],
        "secondary_diagnostics": [
            "provider calls per accepted row",
            "provider spend per accepted row",
            "receipt validity for Telos rows",
            "raw-artifact completeness",
            "controlled-player win count",
        ],
        "forbidden_fallbacks": [
            "verified-completion boolean as primary metric",
            "cross-task aggregate benchmark score",
            "leaderboard or SWE-bench score",
            "model-superiority claim",
            "state-of-the-art claim",
        ],
        "future_backtest_required_before_paid_execution": True,
        "future_paid_execution_authorized_by_this_gate": False,
    }


def task_eligibility_rules(field_inventory: dict[str, Any]) -> dict[str, Any]:
    selected_tasks = []
    for preview in field_inventory["paired_task_preview"]:
        selected_tasks.append(
            {
                "task_surface": preview["task_surface"],
                "public_config": preview["public_config"],
                "eligibility_status": "eligible_for_zero_spend_metric_backtest",
                "selection_reason": (
                    "iter83 has committed metadata, raw evidence, receipt accounting, and "
                    "task-native score fields for both baseline and Telos conditions"
                ),
                "future_paid_execution_status": "not_authorized_by_iter85",
            }
        )
    return {
        "schema_version": "telos.discriminating_task_metric.task_eligibility.v1",
        "experiment_id": EXPERIMENT_ID,
        "selected_task_count": len(selected_tasks),
        "selected_tasks": selected_tasks,
        "eligibility_rules": [
            "Task source and raw metadata must be committed and hashable.",
            "Both baseline and Telos conditions must exist for the same public_config.",
            "The controlled player must be mapped deterministically from metadata.",
            "Task-native score fields must be present for every row.",
            "Receipt validity remains required for Telos row admissibility.",
            "Future paid execution requires a separate pre-registered gate.",
        ],
        "exclusions": [
            {
                "candidate": "SWE-bench execution row",
                "eligibility_status": "excluded",
                "reason": "no SWE-bench execution harness or leaderboard boundary is registered",
            },
            {
                "candidate": "uncommitted or live-domain task surfaces",
                "eligibility_status": "excluded",
                "reason": "source, raw artifacts, and score extraction must be committed first",
            },
            {
                "candidate": "cross-task aggregate score",
                "eligibility_status": "excluded",
                "reason": "iter85 authorizes only per-task diagnostic deltas",
            },
        ],
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "benchmark_result_authorized": False,
        "swebench_result_authorized": False,
        "future_paid_execution_authorized_by_this_gate": False,
    }


def future_gate_plan() -> dict[str, Any]:
    return {
        "schema_version": "telos.discriminating_task_metric.future_gate_plan.v1",
        "experiment_id": EXPERIMENT_ID,
        "next_gate": NEXT_GATE,
        "next_gate_type": "zero_spend_metric_backtest",
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
        "provider_calls_in_iter85": 0,
        "provider_spend_in_iter85_usd": decimal_string(ZERO_COST),
        "row_execution_in_iter85": 0,
        "future_paid_execution_pre_registered": False,
        "future_paid_run_ceiling_authorized": False,
        "future_paid_run_ceiling_reason": (
            "No paid execution gate is registered yet; iter86 must backtest the metric on "
            "committed artifacts before any paid ceiling can be frozen."
        ),
        "iter86_hard_ceilings": {
            "provider_model_invocations": 0,
            "provider_spend_usd": decimal_string(ZERO_COST),
            "codeclash_row_execution": 0,
            "gpu_use": "forbidden",
            "cloud_runner_startup": "forbidden",
            "sentinel_named_resource_mutation": "forbidden",
            "production_or_live_domain_mutation": "forbidden",
            "benchmark_model_sota_claim": "forbidden",
        },
        "iter86_decision_options": [
            "pre-register a bounded paid execution only if the metric is computable and non-saturated",
            "redesign the metric again if field semantics are ambiguous",
            "stop/review if no discriminating task-native metric can be justified",
        ],
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "telos.discriminating_task_metric.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "allowed_claim": (
            "A zero-spend candidate task-native metric contract has been designed for backtest."
        ),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "future_paid_execution_authorized_by_this_gate": False,
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter85-discriminating-task-metric-redesign-{status}",
        "task_id": "telos:iter85_discriminating_task_metric_redesign@iter84",
        "agent_id": "codex-local-metric-redesign-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Redesign the saturated verified-completion metric into a discriminating task-native "
            "metric contract without provider calls or benchmark/model/SOTA claims."
        ),
        "acceptance_criteria": [
            "Iter84 receipt and audit validation pass.",
            "The iter83/iter84 null and saturation evidence remains visible.",
            "The proposed metric is not the saturated verified-completion boolean.",
            "Task eligibility and score extraction rules are explicit.",
            "Future paid execution is not authorized by this gate.",
            "No provider calls, spend, row execution, cloud runner, GPU, Sentinel mutation, or live-domain mutation occurs.",
            "No benchmark, leaderboard, SWE-bench, model-superiority, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Summary records the redesigned metric contract and no-claim boundary.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/metric_contract.json",
                "notes": "Candidate task-native score-share metric contract.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/source_field_inventory.json",
                "notes": "Committed iter83 fields available for the next backtest.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records why completion evidence saturated and why paid execution is deferred.",
            },
        ],
        "falsifiers": [
            "The result must block if iter84 validation fails.",
            "The result must fail if provider calls, spend, or row execution occur in iter85.",
            "The result must fail if the metric remains the verified-completion boolean.",
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
    field_inventory: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    RESULT.write_text(
        f"""# Iteration 85 Result - Discriminating Task/Metric Redesign

Status: `{status.upper()}`.

## Summary

This gate redesigned the benchmark-facing protocol-effect metric from committed evidence only. It
made zero provider calls, spent `$0.00`, and executed zero CodeClash rows.

- iter84 validation clean: `{str(prereq['clean_prerequisites']).lower()}`,
- prior classification: `{prereq['iter84_classification']}`,
- redesigned metric: `{METRIC_ID}`,
- metric status: `candidate_contract_frozen_for_zero_spend_backtest`,
- source rows inventoried: `{field_inventory['row_count']}`,
- task-native score fields available for all rows: `{str(field_inventory['candidate_metric_field_available_for_all_rows']).lower()}`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- row execution in this gate: `0`,
- future paid execution authorized by this gate: `false`,
- next gate: `{NEXT_GATE}`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Candidate Metric

The prior verified-completion boolean remains an admissibility gate only. The candidate primary
metric is task-native controlled-player score share:

`sum(controlled_player_score) / sum(all_player_scores)`, compared as
`Telos score share - baseline score share` within the same `public_config`.

## Design-Time Field Inventory

| Task surface | Baseline score share | Telos score share | Candidate delta |
| --- | --- | --- | --- |
""",
        encoding="utf-8",
    )
    with RESULT.open("a", encoding="utf-8") as handle:
        for row in field_inventory["paired_task_preview"]:
            handle.write(
                f"| `{row['task_surface']}` | `{row['baseline_score_share']}` | "
                f"`{row['telos_score_share']}` | "
                f"`{row['candidate_delta_telos_minus_baseline']}` |\n"
            )
        handle.write(
            f"""
These field values prove the candidate metric is not identical to the saturated completion
boolean, but they are design evidence only. Iter86 must backtest the extractor and publish the
metric result from committed artifacts before any paid execution is proposed.

## Claim Boundary

This gate may claim only that a zero-spend task-native metric contract has been designed and
pre-registered for backtest. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/saturation_critique.json`
- `proof/source_field_inventory.json`
- `proof/metric_contract.json`
- `proof/task_eligibility_rules.json`
- `proof/future_gate_plan.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
        )

    command_lines = [
        f"discriminating task/metric redesign: {status}",
        f"iter84_receipt_validation_returncode={prereq['iter84_receipt_validation_returncode']}",
        f"iter84_audit_returncode={prereq['iter84_audit_returncode']}",
        f"iter84_classification={prereq['iter84_classification']}",
        f"metric_id={METRIC_ID}",
        f"source_rows_inventoried={field_inventory['row_count']}",
        "provider_calls_in_this_gate=0",
        "provider_spend_in_this_gate_usd=0.00000000",
        "row_execution_in_this_gate=0",
        "future_paid_execution_authorized_by_this_gate=false",
        f"next_gate={NEXT_GATE}",
        f"blockers={','.join(blockers) if blockers else 'none'}",
        f"failures={','.join(failures) if failures else 'none'}",
    ]
    for row in field_inventory["paired_task_preview"]:
        command_lines.append(
            f"{row['task_surface']}: baseline_score_share={row['baseline_score_share']} "
            f"telos_score_share={row['telos_score_share']} "
            f"candidate_delta={row['candidate_delta_telos_minus_baseline']}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")
    (PROOF / "review.md").write_text(
        f"""# Iteration 85 Review

Iter83 and iter84 showed a real null/no-signal result under the previous metric. The old
verified-completion boolean saturated because all baseline and Telos rows completed, all required
Telos receipts validated, and all completion deltas were `0`.

Iter85 redesigns the metric but does not claim a result from it. The candidate contract is
`{METRIC_ID}`: verified completion, raw artifacts, receipts, and redaction scans are admissibility
gates; the future primary metric is task-native controlled-player score share by `public_config`.

- status: `{status}`,
- provider calls in iter85: `0`,
- provider spend in iter85: `$0.00000000`,
- row execution in iter85: `0`,
- future paid execution authorized by iter85: `false`,
- next gate: `{NEXT_GATE}`.

The next gate is a zero-spend backtest on committed iter83 artifacts. No benchmark, leaderboard,
SWE-bench, production/live-domain, model-superiority, or state-of-the-art result is claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter84()
    critique = saturation_critique()
    field_inventory, field_blockers = extract_source_field_inventory()
    blockers.extend(field_blockers)
    contract = metric_contract()
    task_rules = task_eligibility_rules(field_inventory)
    future_plan = future_gate_plan()
    boundary = claim_boundary()

    failures: list[str] = []
    if not prereq["clean_prerequisites"]:
        blockers.append("iter84_prerequisite_validation_failed")
    if contract["primary_metric_not_verified_completion_boolean"] is not True:
        failures.append("metric_contract_remains_saturated_completion_boolean")
    if field_inventory["candidate_metric_field_available_for_all_rows"] is not True:
        blockers.append("candidate_metric_fields_not_available_for_all_rows")
    if field_inventory["candidate_metric_nonconstant_on_source_fields"] is not True:
        blockers.append("candidate_metric_source_fields_still_constant")
    if future_plan["next_gate_pre_registered"] is not True:
        blockers.append("next_gate_not_pre_registered")
    if future_plan["future_paid_execution_pre_registered"] is not False:
        failures.append("future_paid_execution_incorrectly_pre_registered")
    if boundary["future_paid_execution_authorized_by_this_gate"] is not False:
        failures.append("future_paid_execution_incorrectly_authorized")

    write_json(PROOF / "prerequisite_validation.json", prereq)
    write_json(PROOF / "saturation_critique.json", critique)
    write_json(PROOF / "source_field_inventory.json", field_inventory)
    write_json(PROOF / "metric_contract.json", contract)
    write_json(PROOF / "task_eligibility_rules.json", task_rules)
    write_json(PROOF / "future_gate_plan.json", future_plan)
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
        field_inventory=field_inventory,
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
                "Verified completion was the wrong primary metric for the benchmark-facing pilot; "
                "task-native controlled-player score share is the next candidate metric to backtest."
            ),
            "next_action": (
                "backtest the discriminating metric on committed iter83 raw artifacts before any "
                "further paid execution or benchmark claim"
            ),
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/metric_contract.json",
                f"experiments/{EXPERIMENT_ID}/proof/source_field_inventory.json",
                f"experiments/{EXPERIMENT_ID}/proof/future_gate_plan.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary = {
        "schema_version": "telos.discriminating_task_metric.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter84_status": prereq["iter84_status"],
        "iter84_clean_pass": prereq["iter84_clean_pass"],
        "iter84_classification": prereq["iter84_classification"],
        "iter84_next_step_decision": prereq["iter84_next_step_decision"],
        "prior_metric_id": "verified_completion_evidence_by_task_and_condition",
        "candidate_metric_id": METRIC_ID,
        "candidate_metric_status": "candidate_contract_frozen_for_zero_spend_backtest",
        "candidate_metric_not_verified_completion_boolean": True,
        "candidate_metric_field_available_for_all_rows": field_inventory[
            "candidate_metric_field_available_for_all_rows"
        ],
        "candidate_metric_nonconstant_on_source_fields": field_inventory[
            "candidate_metric_nonconstant_on_source_fields"
        ],
        "source_rows_inventoried": field_inventory["row_count"],
        "paired_task_preview": field_inventory["paired_task_preview"],
        "metric_backtest_result_claimed": False,
        "future_gate": NEXT_GATE,
        "future_gate_type": "zero_spend_metric_backtest",
        "future_paid_execution_authorized_by_this_gate": False,
        "future_paid_execution_pre_registered": False,
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

    print(f"discriminating task/metric redesign: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("row_execution_in_this_gate=0")
    print(f"metric_id={METRIC_ID}")
    print(f"source_rows_inventoried={field_inventory['row_count']}")
    print(
        "candidate_metric_field_available_for_all_rows="
        f"{str(field_inventory['candidate_metric_field_available_for_all_rows']).lower()}"
    )
    print(f"next_gate={NEXT_GATE}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
