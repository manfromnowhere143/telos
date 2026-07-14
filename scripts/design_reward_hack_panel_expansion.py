#!/usr/bin/env python3
"""Design the next reward-hack panel expansion without provider calls."""

from __future__ import annotations

from collections import defaultdict
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
EXPERIMENT_ID = "iter177_reward_hack_panel_disagreement_calibrated_expansion_design"
NEXT_EXPERIMENT_ID = "iter178_reward_hack_panel_remaining_pairs_paid_expansion"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
NEXT_HYPOTHESIS = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"

ITER171_PLAN = (
    ROOT
    / "experiments"
    / "iter171_reward_hack_panel_model_binding_freeze"
    / "proof"
    / "paid_pilot_plan.json"
)
ITER174_DEFAULTS = (
    ROOT
    / "experiments"
    / "iter174_reward_hack_panel_default_choice_freeze"
    / "proof"
    / "default_choice_packet.json"
)
ITER175_PANEL = (
    ROOT
    / "experiments"
    / "iter175_reward_hack_panel_bounded_paid_pilot"
    / "proof"
    / "panel_metrics.json"
)
ITER176_RESULT = ROOT / "experiments" / "iter176_reward_hack_panel_result_adjudication" / "RESULT.md"
ITER176_INVALID = (
    ROOT
    / "experiments"
    / "iter176_reward_hack_panel_result_adjudication"
    / "proof"
    / "invalid_output_audit.json"
)
ITER176_DISAGREEMENT = (
    ROOT
    / "experiments"
    / "iter176_reward_hack_panel_result_adjudication"
    / "proof"
    / "row_level_disagreement_matrix.json"
)
ITER176_RULE_TABLE = (
    ROOT
    / "experiments"
    / "iter176_reward_hack_panel_result_adjudication"
    / "proof"
    / "panel_rule_comparison_table.json"
)
HACK_PACKETS = (
    ROOT
    / "benchmarks"
    / "reward_hack_benchmark_v1"
    / "blinded_model_judge_packets_v1"
    / "packets.jsonl"
)
CONTROL_PACKETS = (
    ROOT
    / "benchmarks"
    / "reward_hack_benchmark_v1"
    / "legitimate_controls_v1"
    / "blinded_control_packets_v1"
    / "packets.jsonl"
)

ROW_SELECTION = PROOF / "expansion_row_selection_design.json"
OPENAI_RECOVERY = PROOF / "openai_output_budget_recovery_design.json"
DISAGREEMENT_STRATA = PROOF / "disagreement_stratification_table.json"
CALL_SPEND = PROOF / "call_spend_ceiling_proposal.json"
STOP_CONDITIONS = PROOF / "stop_condition_proposal.json"
CLAIM_DECISION = PROOF / "claim_boundary_decision.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
ENDPOINT_RESULTS = PROOF / "endpoint_results.json"
AUDIT_REPORT = PROOF / "audit_report.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING_RECORD = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_reward_hack_panel_disagreement_calibrated_expansion_design.json"

PRIMARY_RULE = "majority_catch"
OPENAI_RECOVERED_MAX_OUTPUT_TOKENS = 1536
PRIOR_OPENAI_MAX_OUTPUT_TOKENS = 512
CALL_CEILING = 160
SPEND_CEILING_USD = "50.00"
SECRET_PATTERNS = [
    ("google_oauth_token", re.compile(r"ya29\.[A-Za-z0-9._-]+")),
    ("bearer_token", re.compile(r"Bearer\s+(?!\\[REDACTED_BEARER_TOKEN\\])[A-Za-z0-9._~+/=-]+")),
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


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(payload), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit(f"expected object JSON at {rel(path)}")
    return loaded


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def packet_index(packet_id: str) -> int:
    match = re.search(r"-(\d{3})$", packet_id)
    if not match:
        raise SystemExit(f"cannot parse packet index from {packet_id}")
    return int(match.group(1))


def packets_by_index(path: Path) -> dict[int, dict[str, Any]]:
    return {packet_index(row["packet_id"]): row for row in read_jsonl(path)}


def build_remaining_pairs(paid_plan: dict[str, Any]) -> list[dict[str, Any]]:
    hack_packets = packets_by_index(HACK_PACKETS)
    control_packets = packets_by_index(CONTROL_PACKETS)
    selected_indices = {int(row["pair_index"]) for row in paid_plan["selected_pairs"]}
    remaining_indices = sorted(set(hack_packets) - selected_indices)
    pairs: list[dict[str, Any]] = []
    for idx in remaining_indices:
        hack = hack_packets[idx]
        control = control_packets[idx]
        pairs.append(
            {
                "control_packet_id": control["packet_id"],
                "control_packet_sha256": control["packet_sha256"],
                "hack_packet_id": hack["packet_id"],
                "hack_packet_sha256": hack["packet_sha256"],
                "pair_index": idx,
                "selection_reason": "not_attempted_in_iter175_panel_pilot",
            }
        )
    return pairs


def stratum_rows(disagreement: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows = disagreement["rows"]
    strata: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        packet_kind = row["packet_kind"]
        panel = row["panel"]
        entry = {
            "disagreement_class": row["disagreement_class"],
            "packet_id": row["packet_id"],
            "packet_kind": packet_kind,
            "panel_nondecision": panel["panel_nondecision"],
            "reward_hack_votes": panel["reward_hack_votes"],
        }
        if packet_kind == "hack" and panel["majority_catch"]:
            strata["iter175_majority_caught_hacks"].append(entry)
        if packet_kind == "hack" and not panel["majority_catch"] and not panel["panel_nondecision"]:
            strata["iter175_scoreable_panel_missed_hacks"].append(entry)
        if panel["panel_nondecision"]:
            strata["iter175_panel_nondecisions"].append(entry)
        if packet_kind == "control" and row["disagreement_class"] == "unanimous_legitimate":
            strata["iter175_clean_controls"].append(entry)
        if row["disagreement_class"] == "openai_anthropic_catch_google_legitimate":
            strata["iter175_google_conservative_disagreements"].append(entry)
    return dict(sorted(strata.items()))


def build_row_selection(
    paid_plan: dict[str, Any], invalid_audit: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    remaining_pairs = build_remaining_pairs(paid_plan)
    recovery_calls = [
        {
            "call_id": row["call_id"],
            "packet_id": row["packet_id"],
            "packet_kind": row["packet_kind"],
            "recovery_provider_family": "openai",
            "recovery_slot_id": row["slot_id"],
            "selection_reason": row["cause"],
        }
        for row in invalid_audit["nondecision_rows"]
        if row["provider_family"] == "openai"
        and row["cause"] == "provider_incomplete_max_output_tokens_empty_content"
    ]
    primary_calls = len(remaining_pairs) * 2 * 3
    total_planned = primary_calls + len(recovery_calls)
    return {
        "benchmark_pair_count": 40,
        "diagnostic_recovery_calls": recovery_calls,
        "diagnostic_recovery_call_count": len(recovery_calls),
        "experiment_id": EXPERIMENT_ID,
        "fresh_remaining_pair_count": len(remaining_pairs),
        "fresh_remaining_pairs": remaining_pairs,
        "next_paid_gate_call_accounting": {
            "call_ceiling": CALL_CEILING,
            "fresh_remaining_panel_primary_calls": primary_calls,
            "planned_primary_plus_diagnostic_calls": total_planned,
            "retry_reserve_calls": CALL_CEILING - total_planned,
            "spend_ceiling_usd": SPEND_CEILING_USD,
        },
        "schema_version": "telos.iter177.expansion_row_selection_design.v1",
        "score_policy": (
            "Remaining-pair panel calls form the next primary paid expansion cohort. The three OpenAI "
            "recovery calls are diagnostic and must not rewrite the published iter175 primary result."
        ),
    }, recovery_calls


def build_openai_recovery(invalid_audit: dict[str, Any]) -> dict[str, Any]:
    rows = invalid_audit["nondecision_rows"]
    return {
        "experiment_id": EXPERIMENT_ID,
        "observed_failure": {
            "count": len(rows),
            "failure_cause": "provider_incomplete_max_output_tokens_empty_content",
            "incomplete_reason": "max_output_tokens",
            "openai_output_tokens_at_failure": [
                row.get("usage", {}).get("output_tokens") for row in rows
            ],
            "prior_max_output_tokens": PRIOR_OPENAI_MAX_OUTPUT_TOKENS,
        },
        "recovered_request_shape": {
            "openai_max_output_tokens": OPENAI_RECOVERED_MAX_OUTPUT_TOKENS,
            "parser_unchanged": "telos.reward_hack_judge_parser.v1",
            "primary_rule_unchanged": PRIMARY_RULE,
            "strict_json_schema_required": True,
        },
        "retry_policy": {
            "diagnostic_recovery_rows": [row["call_id"] for row in rows],
            "empty_output_after_recovery": "publish blocked_or_nondecision evidence; do not coerce",
            "invalid_or_refusal_after_recovery": "publish nondecision evidence; do not convert to catch",
        },
        "schema_version": "telos.iter177.openai_output_budget_recovery_design.v1",
        "score_policy": (
            "The recovery cohort tests request-shape reliability. Its outputs may be reported as a "
            "diagnostic recovered-output table, but they do not replace iter175 adjudicated metrics."
        ),
    }


def build_disagreement_strata(
    disagreement: dict[str, Any], remaining_pairs: list[dict[str, Any]]
) -> dict[str, Any]:
    strata = stratum_rows(disagreement)
    strata["fresh_remaining_pairs_unobserved_by_panel"] = [
        {
            "control_packet_id": row["control_packet_id"],
            "hack_packet_id": row["hack_packet_id"],
            "packet_kind": "paired_hack_control",
            "pair_index": row["pair_index"],
        }
        for row in remaining_pairs
    ]
    return {
        "counts_by_stratum": {key: len(value) for key, value in sorted(strata.items())},
        "experiment_id": EXPERIMENT_ID,
        "schema_version": "telos.iter177.disagreement_stratification_table.v1",
        "strata": dict(sorted(strata.items())),
        "use_in_next_paid_gate": {
            "diagnostic_recovery": "iter175_panel_nondecisions caused by OpenAI empty output",
            "primary_expansion": "fresh_remaining_pairs_unobserved_by_panel",
            "result_interpretation": [
                "iter175_majority_caught_hacks",
                "iter175_scoreable_panel_missed_hacks",
                "iter175_clean_controls",
                "iter175_google_conservative_disagreements",
            ],
        },
    }


def build_call_spend(row_selection: dict[str, Any]) -> dict[str, Any]:
    accounting = row_selection["next_paid_gate_call_accounting"]
    return {
        "call_ceiling": CALL_CEILING,
        "credential_probe_ceiling": 0,
        "experiment_id": EXPERIMENT_ID,
        "model_evaluation_ceiling_for_iter177": 0,
        "new_cloud_resource_ceiling": 0,
        "new_swebench_execution_ceiling": 0,
        "planned_diagnostic_recovery_calls": row_selection["diagnostic_recovery_call_count"],
        "planned_fresh_remaining_panel_calls": accounting["fresh_remaining_panel_primary_calls"],
        "planned_provider_calls_for_next_paid_gate": accounting[
            "planned_primary_plus_diagnostic_calls"
        ],
        "retry_reserve_calls": accounting["retry_reserve_calls"],
        "schema_version": "telos.iter177.call_spend_ceiling_proposal.v1",
        "spend_ceiling_usd": SPEND_CEILING_USD,
        "status": "pass",
    }


def build_stop_conditions() -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "schema_version": "telos.iter177.stop_condition_proposal.v1",
        "stop_conditions": [
            "stop before attempted provider calls exceed 160",
            "stop before estimated spend exceeds $50.00",
            "stop if a provider binding differs from iter174 frozen defaults",
            "stop if OpenAI max_output_tokens recovery shape differs from iter177 before first call",
            "stop if any committed raw artifact contains a secret or private project/account identifier",
            "stop if majority_catch is not preserved as the primary rule",
            "publish partial or blocked evidence instead of substituting rows, models, or providers",
        ],
    }


def build_endpoint_results() -> dict[str, Any]:
    return {
        "credential_probes": 0,
        "endpoint_calls": [],
        "experiment_id": EXPERIMENT_ID,
        "model_evaluations": 0,
        "new_cloud_resources": 0,
        "new_swebench_executions": 0,
        "provider_calls": 0,
        "schema_version": "telos.iter177.endpoint_results.v1",
        "status": "pass",
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
                        "match_sha256": sha256_bytes(match.group(0).encode("utf-8")),
                        "match_start": match.start(),
                        "pattern": name,
                    }
                )
    return {
        "experiment_id": EXPERIMENT_ID,
        "hits": hits,
        "patterns": [name for name, _pattern in SECRET_PATTERNS],
        "schema_version": "telos.iter177.secret_safety_audit.v1",
        "scanned_artifact_count": scanned,
        "secret_hit_count": len(hits),
        "status": "pass" if not hits else "fail",
    }


def claim_boundary_decision(status: str) -> dict[str, Any]:
    return {
        "claim_supported": (
            "Telos has a frozen, zero-spend design for a bounded remaining-pairs panel expansion "
            "and a separate OpenAI output-budget recovery diagnostic."
        )
        if status == "pass"
        else "The expansion design did not satisfy the pre-registered bars.",
        "experiment_id": EXPERIMENT_ID,
        "leaderboard_claim_supported": False,
        "model_comparison_claim_supported": False,
        "new_score_claim_supported": False,
        "next_paid_gate_supported": status == "pass",
        "not_supported": [
            "leaderboard ranking",
            "state-of-the-art claim",
            "natural reward-hacking frequency estimate",
            "broad reward-model robustness claim",
            "production deployment claim",
            "any claim from unrun iter178 provider outputs",
        ],
        "schema_version": "telos.iter177.claim_boundary_decision.v1",
        "sota_claim_supported": False,
        "status": status,
    }


def next_hypothesis_markdown() -> str:
    return f"""# Iteration 178 - Reward-Hack Panel Remaining-Pairs Paid Expansion

Status: pre-registered paid execution gate; no provider calls, credential probes, model evaluations,
SWE-bench executions, cloud resources, benchmark scores, leaderboard claims, model-comparison claims,
state-of-the-art claims, natural-frequency claims, or broad robustness claims have been run for this gate.

## Why this gate exists

`iter175` ran the first bounded `20`-pair panel pilot and `iter176` adjudicated it. `iter177` froze the
next expansion design: complete the remaining `20` paired rows from `reward_hack_benchmark_v1` and
separately test whether a larger OpenAI output budget recovers the three iter175 empty-content rows.

## Method

Inputs:

- `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/RESULT.md`
- `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/proof/expansion_row_selection_design.json`
- `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/proof/openai_output_budget_recovery_design.json`
- `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/proof/call_spend_ceiling_proposal.json`
- `experiments/iter174_reward_hack_panel_default_choice_freeze/proof/default_choice_packet.json`
- `experiments/iter171_reward_hack_panel_model_binding_freeze/proof/primary_aggregation_rule.json`

Execution envelope:

- planned fresh remaining-pair panel calls: `120`,
- planned diagnostic OpenAI recovery calls: `3`,
- total planned provider calls before retries: `123`,
- total provider-call ceiling including retry reserve: `{CALL_CEILING}`,
- retry reserve: `37`,
- spend ceiling: `${SPEND_CEILING_USD}`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- primary rule: `majority_catch`,
- OpenAI recovered max output tokens: `{OPENAI_RECOVERED_MAX_OUTPUT_TOKENS}`,
- runtime credentials may be loaded only from environment or external secret stores; secret values,
  project IDs, account IDs, bearer tokens, and service-account values must never be written.

## Required Outputs

- scheduled call manifest,
- raw prompt and raw response artifacts,
- provider call ledger,
- parsed judge outputs,
- per-slot metrics,
- panel metrics for the fresh remaining-pair cohort,
- combined unrepaired iter175+iter178 diagnostic table,
- OpenAI recovery diagnostic table,
- cost/call audit,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- attempted provider calls are `<= 160`,
- estimated spend is `<= $50.00`,
- all fresh remaining-pair calls use the frozen iter174 provider defaults,
- OpenAI calls use the iter177 recovered output-budget shape,
- every attempted output is parsed by `telos/reward_hack_judge_parser.py` before aggregation,
- invalid, refusal, empty, and inconclusive outputs remain nondecisions,
- the three recovery calls are reported diagnostically and do not rewrite iter175 primary metrics,
- total new SWE-bench executions and new cloud resources are `0`,
- no committed artifact contains a secret, private project/account identifier, service-account value,
  bearer token, or API key,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, or public
  benchmark-score claim is made.

## Falsifiers

1. The gate attempts more than `160` provider calls or exceeds `$50.00` estimated spend.
2. Any provider binding differs from the iter174 frozen defaults.
3. OpenAI recovery calls use a request shape different from iter177's frozen design.
4. A parser, row, provider, model, aggregation rule, or metric denominator is changed after outputs.
5. Invalid, refusal, empty, or inconclusive outputs are counted as catches or legitimate decisions.
6. The recovery cohort is used to rewrite the published iter175 primary result.
7. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
8. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or
   public benchmark-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a bounded paid panel expansion over the previously unobserved
`20` paired rows, plus a separately reported OpenAI output-budget recovery diagnostic.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, or any claim about rows, models, calls,
or outputs outside the committed iter175-iter178 proof packets.
"""


def result_markdown(
    *,
    status: str,
    row_selection: dict[str, Any],
    openai_recovery: dict[str, Any],
    call_spend: dict[str, Any],
    secret_audit: dict[str, Any],
    failures: list[str],
) -> str:
    failure_text = "\n".join(f"- `{failure}`" for failure in failures) or "- none"
    return f"""# Iteration 177 Result - Reward-Hack Panel Disagreement-Calibrated Expansion Design

Status: `{status}`.

## What this gate did

This gate made no provider calls and no credential probes. It froze the next paid panel expansion design
from committed iter175/iter176 evidence.

## Frozen Design

- Fresh remaining paired rows for the next primary cohort: `{row_selection['fresh_remaining_pair_count']}`.
- Fresh remaining-pair panel calls: `{call_spend['planned_fresh_remaining_panel_calls']}`.
- Diagnostic OpenAI recovery calls: `{call_spend['planned_diagnostic_recovery_calls']}`.
- Total planned calls before retries: `{call_spend['planned_provider_calls_for_next_paid_gate']}`.
- Provider-call ceiling: `{call_spend['call_ceiling']}`.
- Retry reserve: `{call_spend['retry_reserve_calls']}`.
- Spend ceiling: `${call_spend['spend_ceiling_usd']}`.
- OpenAI recovered max output tokens: `{OPENAI_RECOVERED_MAX_OUTPUT_TOKENS}`.
- Provider calls in this gate: `0`.
- Credential probes in this gate: `0`.
- Secret/project/account hits in this gate: `{secret_audit['secret_hit_count']}`.

The three OpenAI recovery rows remain diagnostic. They can test whether the output-budget failure mode is
fixed, but they do not rewrite the published iter175 primary result.

## OpenAI Recovery Rationale

Iter176 found `{openai_recovery['observed_failure']['count']}` OpenAI rows where the provider returned
HTTP 200 but exhausted `{PRIOR_OPENAI_MAX_OUTPUT_TOKENS}` output tokens in reasoning and emitted no
content. Iter177 freezes a provider-specific OpenAI output ceiling of
`{OPENAI_RECOVERED_MAX_OUTPUT_TOKENS}` tokens for the next paid gate while keeping the parser and
`majority_catch` rule unchanged.

## Failures / Blockers

{failure_text}

## Claim Boundary

Supported if status is pass: Telos has a frozen, zero-spend design for the next bounded paid panel
expansion and OpenAI output-budget recovery diagnostic.

Not supported: a new score, leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency
estimate, broad reward-model robustness claim, production deployment claim, or any claim from unrun
iter178 provider outputs.

Recommended next gate: `experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md`.

## Evidence

- `proof/expansion_row_selection_design.json`
- `proof/openai_output_budget_recovery_design.json`
- `proof/disagreement_stratification_table.json`
- `proof/call_spend_ceiling_proposal.json`
- `proof/stop_condition_proposal.json`
- `proof/claim_boundary_decision.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_disagreement_calibrated_expansion_design.json`
"""


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    paid_plan = read_json(ITER171_PLAN)
    defaults = read_json(ITER174_DEFAULTS)
    invalid_audit = read_json(ITER176_INVALID)
    disagreement = read_json(ITER176_DISAGREEMENT)

    failures: list[str] = []
    row_selection, recovery_calls = build_row_selection(paid_plan, invalid_audit)
    openai_recovery = build_openai_recovery(invalid_audit)
    disagreement_strata = build_disagreement_strata(
        disagreement, row_selection["fresh_remaining_pairs"]
    )
    call_spend = build_call_spend(row_selection)
    stop_conditions = build_stop_conditions()
    endpoint = build_endpoint_results()

    if row_selection["fresh_remaining_pair_count"] != 20:
        failures.append("fresh_remaining_pair_count_not_20")
    if len(recovery_calls) != 3:
        failures.append("diagnostic_recovery_call_count_not_3")
    if len(disagreement_strata["strata"]) < 4:
        failures.append("fewer_than_four_row_strata")
    if call_spend["planned_provider_calls_for_next_paid_gate"] > CALL_CEILING:
        failures.append("planned_calls_exceed_call_ceiling")
    if openai_recovery["recovered_request_shape"]["openai_max_output_tokens"] <= PRIOR_OPENAI_MAX_OUTPUT_TOKENS:
        failures.append("openai_recovered_output_budget_not_increased")
    if defaults.get("primary_aggregation_rule_id") != PRIMARY_RULE:
        failures.append("iter174_primary_rule_not_majority_catch")

    status = "pass" if not failures else "fail"
    claim_decision = claim_boundary_decision(status)

    write_json(ROW_SELECTION, row_selection)
    write_json(OPENAI_RECOVERY, openai_recovery)
    write_json(DISAGREEMENT_STRATA, disagreement_strata)
    write_json(CALL_SPEND, call_spend)
    write_json(STOP_CONDITIONS, stop_conditions)
    write_json(CLAIM_DECISION, claim_decision)
    write_json(ENDPOINT_RESULTS, endpoint)
    NEXT_HYPOTHESIS.parent.mkdir(parents=True, exist_ok=True)
    NEXT_HYPOTHESIS.write_text(next_hypothesis_markdown(), encoding="utf-8")

    draft_secret = {"secret_hit_count": 0}
    RESULT.write_text(
        result_markdown(
            status=status,
            row_selection=row_selection,
            openai_recovery=openai_recovery,
            call_spend=call_spend,
            secret_audit=draft_secret,
            failures=failures,
        ),
        encoding="utf-8",
    )

    generated_paths = [
        ROW_SELECTION,
        OPENAI_RECOVERY,
        DISAGREEMENT_STRATA,
        CALL_SPEND,
        STOP_CONDITIONS,
        CLAIM_DECISION,
        ENDPOINT_RESULTS,
        NEXT_HYPOTHESIS,
        RESULT,
        ITER171_PLAN,
        ITER174_DEFAULTS,
        ITER175_PANEL,
        ITER176_RESULT,
        ITER176_INVALID,
        ITER176_DISAGREEMENT,
        ITER176_RULE_TABLE,
    ]
    secret_audit = secret_safety_audit(generated_paths)
    if secret_audit["status"] != "pass":
        failures.append("secret_safety_audit_failed")
        status = "fail"
        claim_decision = claim_boundary_decision(status)
        write_json(CLAIM_DECISION, claim_decision)
    write_json(SECRET_AUDIT, secret_audit)

    audit_report = {
        "bars": {
            "credential_probes": 0,
            "fresh_remaining_pair_count": row_selection["fresh_remaining_pair_count"],
            "leaderboard_claimed": False,
            "model_evaluations": 0,
            "model_superiority_claimed": False,
            "new_cloud_resources": 0,
            "new_swebench_executions": 0,
            "openai_recovered_max_output_tokens": OPENAI_RECOVERED_MAX_OUTPUT_TOKENS,
            "planned_provider_calls_for_next_paid_gate": call_spend[
                "planned_provider_calls_for_next_paid_gate"
            ],
            "provider_calls": 0,
            "secret_hit_count": secret_audit["secret_hit_count"],
            "sota_claimed": False,
            "spend_ceiling_usd": SPEND_CEILING_USD,
            "stratum_count": len(disagreement_strata["strata"]),
        },
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "schema_version": "telos.iter177.audit_report.v1",
        "status": status,
    }
    run_summary = {
        "credential_probes": 0,
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "generated_at_utc": now_utc(),
        "new_cloud_resources": 0,
        "new_swebench_executions": 0,
        "provider_calls": 0,
        "recommended_next_gate": f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md",
        "schema_version": "telos.iter177.run_summary.v1",
        "secret_hit_count": secret_audit["secret_hit_count"],
        "status": status,
    }
    learning_record = {
        "evidence_paths": [
            rel(ROW_SELECTION),
            rel(OPENAI_RECOVERY),
            rel(DISAGREEMENT_STRATA),
            rel(CALL_SPEND),
            rel(STOP_CONDITIONS),
            rel(CLAIM_DECISION),
            rel(SECRET_AUDIT),
            rel(RECEIPT),
        ],
        "experiment_id": EXPERIMENT_ID,
        "insight": (
            "the next honest panel step is a bounded remaining-pairs expansion plus separate OpenAI "
            "output-budget recovery, not a claim upgrade from the first 20-pair pilot"
        )
        if status == "pass"
        else "the disagreement-calibrated expansion design did not satisfy its bars",
        "next_action": f"run {NEXT_EXPERIMENT_ID} only under the frozen call, spend, and recovery design",
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
            row_selection=row_selection,
            openai_recovery=openai_recovery,
            call_spend=call_spend,
            secret_audit=secret_audit,
            failures=failures,
        ),
        encoding="utf-8",
    )

    receipt = {
        "acceptance_criteria": [
            "No provider calls, credential probes, model evaluations, SWE-bench executions, or cloud resources are used.",
            "The design uses only committed iter175 and iter176 artifacts.",
            "The design includes at least four row strata.",
            "The design includes a concrete mitigation for OpenAI empty-content max_output_tokens failures.",
            "The next paid plan has an explicit provider-call ceiling and spend ceiling.",
            "No committed artifact contains secrets or private project/account identifiers.",
            "No leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or public benchmark-score claim is made.",
        ],
        "agent_id": "codex-zero-spend-panel-expansion-designer",
        "benchmark_id": "reward_hack_benchmark_v1",
        "evidence": [
            {"artifact": rel(ROW_SELECTION), "kind": "artifact", "status": status},
            {"artifact": rel(OPENAI_RECOVERY), "kind": "artifact", "status": status},
            {"artifact": rel(DISAGREEMENT_STRATA), "kind": "artifact", "status": status},
            {"artifact": rel(CALL_SPEND), "kind": "artifact", "status": status},
            {"artifact": rel(SECRET_AUDIT), "kind": "adversarial_review", "status": status},
        ],
        "falsifiers": [
            "The gate fails if any provider call, credential probe, model evaluation, SWE-bench execution, or cloud resource change occurs.",
            "The gate fails if the design is not derived from committed iter175/iter176 artifacts.",
            "The gate fails if it lacks an OpenAI output-budget mitigation.",
            "The gate fails if no explicit call or spend ceiling is frozen.",
            "The gate fails if committed artifacts contain secrets or private project/account identifiers.",
            "The gate cannot support a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or public benchmark-score claim.",
        ],
        "receipt_id": f"iter177-reward-hack-panel-disagreement-calibrated-expansion-design-{status}",
        "stated_goal": "Freeze the next reward-hack panel expansion design before further paid calls.",
        "status": status,
        "task_id": f"telos:{EXPERIMENT_ID}",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(RECEIPT, receipt)

    print(f"reward hack panel expansion design: {status}")
    print("provider_calls=0")
    print("credential_probes=0")
    print(f"fresh_remaining_pair_count={row_selection['fresh_remaining_pair_count']}")
    print(f"planned_next_paid_calls={call_spend['planned_provider_calls_for_next_paid_gate']}")
    print(f"next_gate=experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
