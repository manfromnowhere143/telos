#!/usr/bin/env python3
"""Design the OpenAI nondecision repair gate without provider calls."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter180_reward_hack_panel_openai_nondecision_repair_design"
NEXT_EXPERIMENT_ID = "iter181_reward_hack_panel_openai_nondecision_repair_execution"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"

ITER179 = ROOT / "experiments" / "iter179_reward_hack_panel_full_cohort_adjudication"
ITER179_RESULT = ITER179 / "RESULT.md"
ITER179_DISAGREEMENT = ITER179 / "proof" / "row_level_disagreement_and_nondecision_audit.json"
ITER179_RECOVERY_BOUNDARY = ITER179 / "proof" / "openai_recovery_effect_boundary.json"
ITER179_FULL_PANEL = ITER179 / "proof" / "full_cohort_panel_metrics.json"
ITER179_SECRET_AUDIT = ITER179 / "proof" / "secret_safety_audit.json"
ITER178_RECOVERY = (
    ROOT
    / "experiments"
    / "iter178_reward_hack_panel_remaining_pairs_paid_expansion"
    / "proof"
    / "openai_recovery_diagnostic_table.json"
)
ITER177_OPENAI_RECOVERY_DESIGN = (
    ROOT
    / "experiments"
    / "iter177_reward_hack_panel_disagreement_calibrated_expansion_design"
    / "proof"
    / "openai_output_budget_recovery_design.json"
)

REPAIR_ROWS = PROOF / "openai_nondecision_repair_row_list.json"
CALL_SPEND = PROOF / "repair_call_spend_ceiling_proposal.json"
METRIC_SEPARATION = PROOF / "metric_separation_rule.json"
CLAIM_DECISION = PROOF / "claim_boundary_decision.json"
NEXT_RECOMMENDATION = PROOF / "next_gate_recommendation.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
ENDPOINT_RESULTS = PROOF / "endpoint_results.json"
AUDIT_REPORT = PROOF / "audit_report.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING_RECORD = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_reward_hack_panel_openai_nondecision_repair_design.json"
NEXT_HYPOTHESIS = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"

REPAIR_PRIMARY_CALLS = 5
REPAIR_RETRY_RESERVE = 5
REPAIR_CALL_CEILING = REPAIR_PRIMARY_CALLS + REPAIR_RETRY_RESERVE
REPAIR_SPEND_CEILING_USD = "10.00"
REPAIR_MAX_OUTPUT_TOKENS = 1536
REPAIR_PROVIDER_FAMILY = "openai"
REPAIR_SLOT_ID = "openai_reasoning_judge"
PRIMARY_RULE = "majority_catch"
SECRET_PATTERNS = [
    ("google_oauth_token", re.compile(r"ya29\.[A-Za-z0-9._-]+")),
    ("bearer_token", re.compile(r"Bearer\s+(?!\[REDACTED_BEARER_TOKEN\])[A-Za-z0-9._~+/=-]+")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{18,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9._-]{18,}\b")),
    ("gcp_project_path", re.compile(r"projects/[A-Za-z][A-Za-z0-9-]{3,}")),
    ("gcp_project_url", re.compile(r"/projects/[A-Za-z][A-Za-z0-9-]{3,}/")),
    (
        "service_account_email",
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    ),
]


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def pretty_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(payload), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected object JSON at {rel(path)}")
    return payload


def packet_index(packet_id: str) -> int:
    match = re.search(r"-v1-(\d+)$", packet_id)
    if not match:
        raise SystemExit(f"cannot derive pair index from {packet_id}")
    return int(match.group(1))


def build_repair_row_list(
    disagreement: dict[str, Any],
    recovery_boundary: dict[str, Any],
    recovery_diagnostic: dict[str, Any],
) -> dict[str, Any]:
    diagnostic_by_packet = {row["packet_id"]: row for row in recovery_diagnostic["rows"]}
    unrecovered_ids = {
        row["packet_id"] for row in recovery_boundary["unrecovered_primary_nondecision_rows"]
    }
    rows: list[dict[str, Any]] = []
    for row in sorted(
        disagreement["nondecision_rows"],
        key=lambda item: (packet_index(item["packet_id"]), item["packet_kind"], item["packet_id"]),
    ):
        slot_nondecisions = row["slot_nondecisions"]
        if len(slot_nondecisions) != 1:
            raise SystemExit(f"unexpected nondecision slot count for {row['packet_id']}")
        slot = slot_nondecisions[0]
        diagnostic = diagnostic_by_packet.get(row["packet_id"])
        rows.append(
            {
                "already_seen_diagnostic_output_counted": False,
                "cause": slot["cause"],
                "future_repair_call_required": True,
                "has_prior_diagnostic_output": diagnostic is not None,
                "original_call_id": slot["call_id"],
                "packet_id": row["packet_id"],
                "packet_kind": row["packet_kind"],
                "pair_index": packet_index(row["packet_id"]),
                "prior_diagnostic_call_id": diagnostic.get("iter178_call_id") if diagnostic else None,
                "prior_diagnostic_parser_status": diagnostic.get("parser_status") if diagnostic else None,
                "prior_diagnostic_score_rewrite_allowed": (
                    diagnostic.get("score_rewrite_allowed") if diagnostic else None
                ),
                "proposed_max_output_tokens": REPAIR_MAX_OUTPUT_TOKENS,
                "provider_family": slot["provider_family"],
                "source_experiment_id": row["source_experiment_id"],
                "slot_id": slot["slot_id"],
                "unrecovered_after_iter178_diagnostic": row["packet_id"] in unrecovered_ids,
            }
        )
    return {
        "already_seen_diagnostic_outputs_counted": False,
        "experiment_id": EXPERIMENT_ID,
        "prior_diagnostic_row_count": sum(1 for row in rows if row["has_prior_diagnostic_output"]),
        "repair_call_required_count": len(rows),
        "repair_rows": rows,
        "schema_version": "telos.iter180.openai_nondecision_repair_row_list.v1",
        "source_nondecision_audit": rel(ITER179_DISAGREEMENT),
        "source_recovery_boundary": rel(ITER179_RECOVERY_BOUNDARY),
        "unrecovered_after_prior_diagnostic_count": sum(
            1 for row in rows if row["unrecovered_after_iter178_diagnostic"]
        ),
    }


def repair_call_spend_ceiling(repair_rows: dict[str, Any]) -> dict[str, Any]:
    return {
        "call_ceiling": REPAIR_CALL_CEILING,
        "estimated_provider_spend_usd": "0.00",
        "experiment_id": EXPERIMENT_ID,
        "future_execution_gate": f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md",
        "planned_primary_repair_calls": repair_rows["repair_call_required_count"],
        "provider_family": REPAIR_PROVIDER_FAMILY,
        "repair_max_output_tokens": REPAIR_MAX_OUTPUT_TOKENS,
        "retry_reserve_calls": REPAIR_RETRY_RESERVE,
        "schema_version": "telos.iter180.repair_call_spend_ceiling_proposal.v1",
        "spend_ceiling_usd": REPAIR_SPEND_CEILING_USD,
        "stop_conditions": [
            "stop before execution if the row list is not exactly five OpenAI empty-output primary nondecisions",
            "stop before execution if any already-seen diagnostic output is scheduled as score evidence",
            "stop if attempted provider calls exceed the call ceiling",
            "publish blocked/partial evidence if credentials or provider access fail",
            "publish unrepaired iter179 metrics alongside any future repaired diagnostic",
        ],
    }


def metric_separation_rule(full_panel: dict[str, Any], repair_rows: dict[str, Any]) -> dict[str, Any]:
    primary = full_panel["rules"][PRIMARY_RULE]
    return {
        "already_seen_diagnostics_can_be_score_evidence": False,
        "experiment_id": EXPERIMENT_ID,
        "future_repair_metric_role": "secondary_repaired_diagnostic_until_separately_accepted",
        "primary_public_metric_remains": {
            "control_catches": primary["control_counts"]["catch_count"],
            "control_nondecisions": primary["control_counts"]["nondecision_count"],
            "control_rows": primary["control_counts"]["attempted"],
            "hack_catches": primary["hack_counts"]["catch_count"],
            "hack_nondecisions": primary["hack_counts"]["nondecision_count"],
            "hack_rows": primary["hack_counts"]["attempted"],
            "rule_id": PRIMARY_RULE,
        },
        "repair_execution_requirement": (
            "A future execution gate must rerun every row in openai_nondecision_repair_row_list.json, "
            "including rows with prior diagnostic outputs, before any repaired diagnostic can be reported."
        ),
        "repair_row_count": repair_rows["repair_call_required_count"],
        "schema_version": "telos.iter180.metric_separation_rule.v1",
        "unrepaired_primary_result_is_mutated": False,
    }


def endpoint_results() -> dict[str, Any]:
    return {
        "credential_probes": 0,
        "endpoint_calls": [],
        "estimated_provider_spend_usd": "0.00",
        "experiment_id": EXPERIMENT_ID,
        "model_evaluations": 0,
        "new_cloud_resources": 0,
        "new_swebench_executions": 0,
        "provider_calls": 0,
        "schema_version": "telos.iter180.endpoint_results.v1",
        "status": "pass",
    }


def claim_boundary_decision(status: str) -> dict[str, Any]:
    return {
        "benchmark_score_claim_supported": False,
        "broad_robustness_claim_supported": False,
        "claim_supported": (
            "Telos has a zero-spend design for a future OpenAI nondecision repair run."
            if status == "pass"
            else "The OpenAI nondecision repair design did not pass its bars."
        ),
        "experiment_id": EXPERIMENT_ID,
        "leaderboard_claim_supported": False,
        "model_comparison_claim_supported": False,
        "model_superiority_claim_supported": False,
        "natural_frequency_claim_supported": False,
        "repaired_score_claim_supported": False,
        "recommended_boundary": (
            "Cite iter180 only as a repair-design gate: five OpenAI empty-output primary "
            "nondecision slots are eligible for a future full rerun under a ten-call ceiling. "
            "No repaired score exists yet."
        ),
        "schema_version": "telos.iter180.claim_boundary_decision.v1",
        "sota_claim_supported": False,
        "status": status,
    }


def next_gate_recommendation(status: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "next_gate": f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md",
        "recommendation": (
            "Run the bounded OpenAI repair execution only after the row list, call ceiling, spend "
            "ceiling, and metric-separation rule are accepted."
            if status == "pass"
            else "Fix the zero-spend repair design before any paid repair execution."
        ),
        "schema_version": "telos.iter180.next_gate_recommendation.v1",
        "status": status,
    }


def secret_safety_audit(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    scanned = 0
    for path in sorted({path for path in paths if path.exists() and path.is_file()}):
        if path == SECRET_AUDIT:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                hits.append(
                    {
                        "artifact": rel(path),
                        "match_sha256": sha256_text(match.group(0)),
                        "match_start": match.start(),
                        "pattern": name,
                    }
                )
    iter179_secret = read_json(ITER179_SECRET_AUDIT).get("secret_hit_count")
    return {
        "experiment_id": EXPERIMENT_ID,
        "hits": hits,
        "iter179_source_secret_hit_count": iter179_secret,
        "patterns": [name for name, _pattern in SECRET_PATTERNS],
        "schema_version": "telos.iter180.secret_safety_audit.v1",
        "scanned_artifact_count": scanned,
        "secret_hit_count": len(hits),
        "status": "pass" if not hits and iter179_secret == 0 else "fail",
    }


def next_hypothesis_markdown() -> str:
    return """# Iteration 181 - Reward-Hack Panel OpenAI Nondecision Repair Execution

Status: pre-registered bounded paid execution gate; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, broad robustness claims, or
repaired-score claims have been run for this gate.

## Why this gate exists

Iter180 designed a repair protocol for the five OpenAI empty-output primary panel nondecisions found by
iter179. The future execution must rerun all five repair rows, including the three that already have
diagnostic outputs, so no already-seen output becomes post-hoc score evidence.

## Method

Inputs:

- `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/RESULT.md`
- `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/proof/openai_nondecision_repair_row_list.json`
- `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/proof/repair_call_spend_ceiling_proposal.json`
- `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/proof/metric_separation_rule.json`

Execution envelope:

- provider calls: at most `10`,
- planned primary repair calls: exactly `5`,
- retry reserve calls: `5`,
- provider family: OpenAI only,
- max output tokens: `1536`,
- estimated spend ceiling: `$10.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- already-seen diagnostic outputs cannot be counted as repair evidence.

## Required Outputs

- scheduled repair call manifest,
- provider call ledger and raw prompt/response hashes,
- parsed repair outputs,
- unrepaired-vs-repaired diagnostic comparison,
- claim-boundary decision,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- exactly `5` primary repair rows are attempted unless blocked before calls,
- attempted provider calls never exceed `10`,
- estimated spend guard never exceeds `$10.00`,
- all attempted rows come from iter180's repair row list,
- already-seen diagnostic outputs are not used as repaired evidence,
- unrepaired iter179 remains the primary public result,
- no committed artifact contains a secret, private project/account identifier, service-account value,
  bearer token, or API key,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, or public
  benchmark-score claim is made.

## Falsifiers

1. The gate calls any provider other than OpenAI or any row outside the iter180 repair row list.
2. The gate exceeds the call or spend ceiling.
3. Already-seen diagnostic outputs are counted as repaired evidence.
4. The gate mutates the unrepaired iter179 primary result.
5. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
6. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or
   public benchmark-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a bounded OpenAI repair execution diagnostic for the five
previously nondecision panel rows, reported separately from the unrepaired iter179 primary result.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, or any claim outside committed
iter175-iter181 proof packets.
"""


def result_markdown(
    *,
    status: str,
    repair_rows: dict[str, Any],
    call_spend: dict[str, Any],
    metric_rule: dict[str, Any],
    secret_audit: dict[str, Any],
    failures: list[str],
) -> str:
    failure_text = "\n".join(f"- `{failure}`" for failure in failures) or "- none"
    primary = metric_rule["primary_public_metric_remains"]
    return f"""# Iteration 180 Result - Reward-Hack Panel OpenAI Nondecision Repair Design

Status: `{status}`.

## What this gate did

This zero-spend gate designed a repair protocol for the OpenAI empty-output panel nondecisions identified
by iter179. It made no provider calls, no credential probes, no model evaluations, no SWE-bench
executions, and no cloud-resource changes.

## Repair Design

- Provider calls in this gate: `0`.
- Credential probes in this gate: `0`.
- Estimated provider spend in this gate: `$0.00`.
- Proposed future primary repair calls: `{call_spend['planned_primary_repair_calls']}`.
- Proposed future retry reserve: `{call_spend['retry_reserve_calls']}`.
- Proposed future call ceiling: `{call_spend['call_ceiling']}`.
- Proposed future spend ceiling: `${call_spend['spend_ceiling_usd']}`.
- Repair rows with prior diagnostics: `{repair_rows['prior_diagnostic_row_count']}`.
- Repair rows still unrecovered after prior diagnostics: `{repair_rows['unrecovered_after_prior_diagnostic_count']}`.
- Secret/project/account hits in this gate: `{secret_audit['secret_hit_count']}`.

## Metric Separation

The unrepaired iter179 result remains the primary public metric: `{primary['hack_catches']}/{primary['hack_rows']}`
hack catches and `{primary['control_catches']}/{primary['control_rows']}` control catches under
`{primary['rule_id']}`, with `{primary['hack_nondecisions']}` hack nondecisions and
`{primary['control_nondecisions']}` control nondecision.

Any future repaired output is a separate diagnostic until a later gate explicitly accepts a repaired
metric. Already-seen OpenAI diagnostic outputs are not score evidence.

## Failures / Blockers

{failure_text}

Recommended next gate: `experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md`.

## Claim Boundary

Supported if status is pass: Telos has a frozen, zero-spend design for a future OpenAI nondecision repair
execution over exactly five primary panel nondecision rows.

Not supported: a repaired panel score, leaderboard ranking, state-of-the-art claim, natural
reward-hacking frequency estimate, broad reward-model robustness claim, production deployment claim,
model-superiority claim, public benchmark score, or any claim outside committed iter175-iter180 proof
packets.

## Evidence

- `proof/openai_nondecision_repair_row_list.json`
- `proof/repair_call_spend_ceiling_proposal.json`
- `proof/metric_separation_rule.json`
- `proof/claim_boundary_decision.json`
- `proof/next_gate_recommendation.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_openai_nondecision_repair_design.json`
"""


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    disagreement = read_json(ITER179_DISAGREEMENT)
    recovery_boundary = read_json(ITER179_RECOVERY_BOUNDARY)
    recovery_diagnostic = read_json(ITER178_RECOVERY)
    full_panel = read_json(ITER179_FULL_PANEL)
    repair_rows = build_repair_row_list(disagreement, recovery_boundary, recovery_diagnostic)
    call_spend = repair_call_spend_ceiling(repair_rows)
    metric_rule = metric_separation_rule(full_panel, repair_rows)
    endpoint = endpoint_results()

    failures: list[str] = []
    if endpoint["provider_calls"] != 0 or endpoint["credential_probes"] != 0:
        failures.append("zero_spend_endpoint_bar_failed")
    if repair_rows["repair_call_required_count"] != REPAIR_PRIMARY_CALLS:
        failures.append("repair_row_count_not_5")
    if call_spend["call_ceiling"] != REPAIR_CALL_CEILING:
        failures.append("repair_call_ceiling_not_10")
    if call_spend["planned_primary_repair_calls"] != REPAIR_PRIMARY_CALLS:
        failures.append("planned_primary_repair_calls_not_5")
    if any(row["provider_family"] != REPAIR_PROVIDER_FAMILY for row in repair_rows["repair_rows"]):
        failures.append("non_openai_repair_row_present")
    if any(row["slot_id"] != REPAIR_SLOT_ID for row in repair_rows["repair_rows"]):
        failures.append("non_openai_slot_repair_row_present")
    if any(row["cause"] != "openai_empty_output" for row in repair_rows["repair_rows"]):
        failures.append("non_empty_output_repair_row_present")
    if any(row["already_seen_diagnostic_output_counted"] for row in repair_rows["repair_rows"]):
        failures.append("already_seen_diagnostic_counted")
    if metric_rule["unrepaired_primary_result_is_mutated"]:
        failures.append("unrepaired_primary_result_mutated")

    status = "pass" if not failures else "fail"
    claim_decision = claim_boundary_decision(status)
    next_recommendation = next_gate_recommendation(status)

    write_json(REPAIR_ROWS, repair_rows)
    write_json(CALL_SPEND, call_spend)
    write_json(METRIC_SEPARATION, metric_rule)
    write_json(CLAIM_DECISION, claim_decision)
    write_json(NEXT_RECOMMENDATION, next_recommendation)
    write_json(ENDPOINT_RESULTS, endpoint)
    NEXT_HYPOTHESIS.parent.mkdir(parents=True, exist_ok=True)
    NEXT_HYPOTHESIS.write_text(next_hypothesis_markdown(), encoding="utf-8")

    RESULT.write_text(
        result_markdown(
            status=status,
            repair_rows=repair_rows,
            call_spend=call_spend,
            metric_rule=metric_rule,
            secret_audit={"secret_hit_count": 0},
            failures=failures,
        ),
        encoding="utf-8",
    )
    secret_audit = secret_safety_audit(
        [
            REPAIR_ROWS,
            CALL_SPEND,
            METRIC_SEPARATION,
            CLAIM_DECISION,
            NEXT_RECOMMENDATION,
            ENDPOINT_RESULTS,
            NEXT_HYPOTHESIS,
            RESULT,
        ]
    )
    if secret_audit["status"] != "pass":
        failures.append("secret_safety_audit_failed")
        status = "fail"
        claim_decision = claim_boundary_decision(status)
        next_recommendation = next_gate_recommendation(status)
        write_json(CLAIM_DECISION, claim_decision)
        write_json(NEXT_RECOMMENDATION, next_recommendation)
    write_json(SECRET_AUDIT, secret_audit)

    audit_report = {
        "bars": {
            "already_seen_diagnostics_counted": False,
            "broad_robustness_claimed": False,
            "call_ceiling": REPAIR_CALL_CEILING,
            "credential_probes": 0,
            "leaderboard_claimed": False,
            "model_evaluations": 0,
            "model_superiority_claimed": False,
            "natural_frequency_claimed": False,
            "new_cloud_resources": 0,
            "new_swebench_executions": 0,
            "planned_primary_repair_calls": repair_rows["repair_call_required_count"],
            "provider_calls": 0,
            "public_benchmark_score_claimed": False,
            "repaired_score_claimed": False,
            "secret_hit_count": secret_audit["secret_hit_count"],
            "sota_claimed": False,
        },
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "schema_version": "telos.iter180.audit_report.v1",
        "status": status,
    }
    run_summary = {
        "credential_probes": 0,
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "generated_at_utc": now_utc(),
        "new_cloud_resources": 0,
        "new_swebench_executions": 0,
        "planned_primary_repair_calls": repair_rows["repair_call_required_count"],
        "provider_calls": 0,
        "recommended_next_gate": f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md",
        "schema_version": "telos.iter180.run_summary.v1",
        "secret_hit_count": secret_audit["secret_hit_count"],
        "status": status,
    }
    learning_record = {
        "evidence_paths": [
            rel(REPAIR_ROWS),
            rel(CALL_SPEND),
            rel(METRIC_SEPARATION),
            rel(CLAIM_DECISION),
            rel(NEXT_RECOMMENDATION),
            rel(SECRET_AUDIT),
            rel(RECEIPT),
        ],
        "experiment_id": EXPERIMENT_ID,
        "insight": (
            "repair must rerun all five OpenAI empty-output primary nondecision slots, including "
            "the three rows with prior diagnostics, so the unrepaired iter179 metric remains primary "
            "and any repaired output is separated as a future diagnostic"
        )
        if status == "pass"
        else "the repair design did not satisfy the zero-spend and metric-separation bars",
        "next_action": f"run {NEXT_EXPERIMENT_ID} only under the iter180 row list and ceilings",
        "result_path": rel(RESULT),
        "schema_version": "telos.learning_record.v1",
        "status": status if status == "pass" else "null",
    }

    write_json(AUDIT_REPORT, audit_report)
    write_json(RUN_SUMMARY, run_summary)
    write_json(LEARNING_RECORD, learning_record)
    RESULT.write_text(
        result_markdown(
            status=status,
            repair_rows=repair_rows,
            call_spend=call_spend,
            metric_rule=metric_rule,
            secret_audit=secret_audit,
            failures=failures,
        ),
        encoding="utf-8",
    )

    receipt = {
        "acceptance_criteria": [
            "No provider calls, credential probes, model evaluations, SWE-bench executions, or cloud resources are used.",
            "Every repair row comes from an iter179 primary panel nondecision with OpenAI empty output.",
            "The repair design reruns all five repair rows before any repaired diagnostic can be reported.",
            "Already-seen diagnostic outputs are not counted as repaired score evidence.",
            "The unrepaired iter179 primary result is not mutated.",
            "No committed artifact contains secrets or private project/account identifiers.",
            "No leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, public benchmark-score, or repaired-score claim is made.",
        ],
        "agent_id": "codex-zero-spend-openai-nondecision-repair-designer",
        "benchmark_id": "reward_hack_benchmark_v1",
        "evidence": [
            {"artifact": rel(REPAIR_ROWS), "kind": "artifact", "status": status},
            {"artifact": rel(CALL_SPEND), "kind": "artifact", "status": status},
            {"artifact": rel(METRIC_SEPARATION), "kind": "artifact", "status": status},
            {"artifact": rel(CLAIM_DECISION), "kind": "artifact", "status": status},
            {"artifact": rel(SECRET_AUDIT), "kind": "adversarial_review", "status": status},
        ],
        "falsifiers": [
            "The gate fails if any provider call, credential probe, model evaluation, SWE-bench execution, or cloud resource change occurs.",
            "The gate fails if the repair list contains a row that is not an OpenAI empty-output primary nondecision from iter179.",
            "The gate fails if already-seen diagnostic outputs are counted as score evidence.",
            "The gate fails if the unrepaired iter179 primary result is changed.",
            "The gate cannot support a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, public benchmark-score, or repaired-score claim.",
        ],
        "receipt_id": f"iter180-reward-hack-panel-openai-nondecision-repair-design-{status}",
        "stated_goal": (
            "Design a zero-spend repair protocol for OpenAI empty-output reward-hack panel "
            "nondecisions while preserving the unrepaired iter179 primary metric."
        ),
        "status": status,
        "task_id": f"telos:{EXPERIMENT_ID}",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(RECEIPT, receipt)

    print(f"reward hack OpenAI nondecision repair design: {status}")
    print("provider_calls=0")
    print("credential_probes=0")
    print(f"repair_rows={repair_rows['repair_call_required_count']}")
    print(f"call_ceiling={call_spend['call_ceiling']}")
    print(f"next_gate=experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
