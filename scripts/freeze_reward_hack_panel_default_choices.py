#!/usr/bin/env python3
"""Freeze iter174 reward-hack panel defaults without provider calls."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter174_reward_hack_panel_default_choice_freeze"
NEXT_EXPERIMENT_ID = "iter175_reward_hack_panel_bounded_paid_pilot"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"

ITER173 = ROOT / "experiments" / "iter173_reward_hack_panel_public_binding_menu"
ITER173_RESULT = ITER173 / "RESULT.md"
PUBLIC_MENU = ITER173 / "proof" / "public_binding_menu.json"
CHOICE_TEMPLATE = ITER173 / "proof" / "operator_choice_template.json"
ITER173_READINESS = ITER173 / "proof" / "readiness_decision.json"
SOURCE_ALIGNMENT = ITER173 / "proof" / "source_alignment.json"
PRIMARY_RULE = (
    ROOT
    / "experiments"
    / "iter171_reward_hack_panel_model_binding_freeze"
    / "proof"
    / "primary_aggregation_rule.json"
)
PAID_PLAN = (
    ROOT
    / "experiments"
    / "iter171_reward_hack_panel_model_binding_freeze"
    / "proof"
    / "paid_pilot_plan.json"
)

DEFAULT_PACKET = PROOF / "default_choice_packet.json"
MEMBERSHIP_AUDIT = PROOF / "menu_membership_audit.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
READINESS = PROOF / "readiness_decision.json"
AUDIT = PROOF / "audit_report.json"
ENDPOINT = PROOF / "endpoint_results.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_reward_hack_panel_default_choice_freeze.json"

CALL_CEILING = 160
SPEND_CEILING_USD = Decimal("50.00")

SECRET_PATTERNS = [
    ("google_oauth_token", re.compile(r"ya29\.[A-Za-z0-9._-]+")),
    ("bearer_token", re.compile(r"Bearer\s+(?!\[REDACTED_BEARER_TOKEN\])[A-Za-z0-9._~+/=-]+")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{18,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9._-]{18,}\b")),
    ("gcp_project_path", re.compile(r"projects/[A-Za-z][A-Za-z0-9-]{5,}")),
    (
        "service_account_email",
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    ),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def stable_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_hash(payload: Any) -> str:
    return sha256_bytes(stable_bytes(payload))


def read_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit(f"expected object JSON at {rel(path)}")
    return loaded


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def candidate_by_id(slot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        candidate["candidate_id"]: candidate
        for candidate in slot.get("candidates", [])
        if isinstance(candidate, dict) and isinstance(candidate.get("candidate_id"), str)
    }


def allowed_choices_by_slot(template: dict[str, Any]) -> dict[str, set[str]]:
    allowed: dict[str, set[str]] = {}
    for slot in template.get("slots", []):
        if isinstance(slot, dict) and isinstance(slot.get("slot_id"), str):
            allowed[slot["slot_id"]] = set(slot.get("choose_one_candidate_id_from_menu", []))
    return allowed


def freeze_default_choices(menu: dict[str, Any], template: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    failures: list[str] = []
    choices: list[dict[str, Any]] = []
    allowed = allowed_choices_by_slot(template)
    for slot in menu.get("slot_menus", []):
        slot_id = slot.get("slot_id")
        recommended_id = slot.get("recommended_candidate_id")
        candidates = candidate_by_id(slot)
        candidate = candidates.get(recommended_id)
        if candidate is None:
            failures.append(f"{slot_id}: recommended candidate missing from public menu")
            continue
        if recommended_id not in allowed.get(slot_id, set()):
            failures.append(f"{slot_id}: recommended candidate missing from choice template")
        choices.append(
            {
                "slot_id": slot_id,
                "provider_family": slot.get("provider_family"),
                "chosen_candidate_id": recommended_id,
                "choice_basis": "iter173_recommended_candidate_id_pre_output_default",
                "exact_model_id": candidate["exact_model_id"],
                "api_family": candidate["api_family"],
                "api_route": candidate["api_route"],
                "credential_source_route": candidate["credential_source_route"],
                "private_identifier_policy": candidate["private_identifier_policy"],
                "structured_output_mode": candidate["structured_output_mode"],
                "source_urls": candidate["source_urls"],
                "source_candidate_sha256": stable_hash(candidate),
                "frozen_before_provider_outputs": True,
                "post_output_substitution_allowed": False,
                "credential_material_committed": False,
                "private_project_or_account_identifier_committed": False,
            }
        )
    return choices, failures


def default_choice_packet(
    *,
    menu: dict[str, Any],
    primary_rule: dict[str, Any],
    paid_plan: dict[str, Any],
    template: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    choices, choice_failures = freeze_default_choices(menu, template)
    call_accounting = paid_plan["call_accounting"]
    packet = {
        "schema_version": "telos.iter174.default_choice_packet.v1",
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": now_utc(),
        "source_experiment_id": "iter173_reward_hack_panel_public_binding_menu",
        "default_choice_policy": (
            "Freeze the iter173 recommended candidate for each slot. Alternatives require a new "
            "zero-spend choice-freeze gate before outputs are observed."
        ),
        "frozen_before_provider_outputs": True,
        "execution_authorized_by_iter174": False,
        "provider_calls_performed_by_iter174": 0,
        "credential_probes_performed_by_iter174": 0,
        "model_evaluations_performed_by_iter174": 0,
        "primary_aggregation_rule_id": primary_rule["primary_rule_id"],
        "primary_rule_selected_before_outputs": primary_rule["selected_before_outputs"],
        "panel_primary_catch_condition": primary_rule["primary_catch_condition"],
        "paid_pilot_call_accounting": {
            "selected_pair_count_for_bounded_pilot": call_accounting[
                "selected_pair_count_for_bounded_pilot"
            ],
            "selected_packet_count_for_bounded_pilot": call_accounting[
                "selected_packet_count_for_bounded_pilot"
            ],
            "panel_slot_count": call_accounting["panel_slot_count"],
            "planned_primary_calls": call_accounting["planned_primary_calls"],
            "retry_reserve_calls": call_accounting["retry_reserve_calls"],
            "planned_calls_plus_retry_reserve": call_accounting[
                "planned_calls_plus_retry_reserve"
            ],
            "current_call_ceiling": call_accounting["current_call_ceiling"],
        },
        "paid_pilot_spend_ceiling_usd": paid_plan["spend_accounting"]["spend_ceiling_usd"],
        "selected_pairs_sha256": stable_hash(paid_plan["selected_pairs"]),
        "retry_policy": paid_plan["retry_policy"],
        "stop_conditions": paid_plan["stop_conditions"],
        "frozen_default_choices": choices,
        "claim_boundary": (
            "Default choice freeze only. This artifact does not contain provider outputs, scores, "
            "leaderboard claims, or paid-execution authorization."
        ),
    }
    return packet, choice_failures


def menu_membership_audit(
    *,
    packet: dict[str, Any],
    menu: dict[str, Any],
    template: dict[str, Any],
    choice_failures: list[str],
) -> dict[str, Any]:
    failures = list(choice_failures)
    slot_ids = [slot["slot_id"] for slot in menu.get("slot_menus", [])]
    frozen_slot_ids = [choice["slot_id"] for choice in packet["frozen_default_choices"]]
    if sorted(slot_ids) != sorted(frozen_slot_ids):
        failures.append("frozen_choice_slot_set_mismatch")

    allowed = allowed_choices_by_slot(template)
    menu_slots = {slot["slot_id"]: slot for slot in menu.get("slot_menus", [])}
    membership_rows: list[dict[str, Any]] = []
    for choice in packet["frozen_default_choices"]:
        slot = menu_slots.get(choice["slot_id"])
        candidate = candidate_by_id(slot or {}).get(choice["chosen_candidate_id"])
        row_failures: list[str] = []
        if choice["chosen_candidate_id"] not in allowed.get(choice["slot_id"], set()):
            row_failures.append("not_allowed_by_operator_choice_template")
        if candidate is None:
            row_failures.append("not_found_in_public_menu")
        else:
            for field in [
                "exact_model_id",
                "api_family",
                "api_route",
                "credential_source_route",
                "private_identifier_policy",
                "structured_output_mode",
                "source_urls",
            ]:
                if choice[field] != candidate[field]:
                    row_failures.append(f"{field}_mismatch")
        if row_failures:
            failures.extend(f"{choice['slot_id']}: {failure}" for failure in row_failures)
        membership_rows.append(
            {
                "slot_id": choice["slot_id"],
                "chosen_candidate_id": choice["chosen_candidate_id"],
                "source_candidate_sha256": choice["source_candidate_sha256"],
                "status": "pass" if not row_failures else "fail",
                "failures": row_failures,
            }
        )
    return {
        "schema_version": "telos.iter174.menu_membership_audit.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "slot_count": len(slot_ids),
        "frozen_choice_count": len(packet["frozen_default_choices"]),
        "membership_rows": membership_rows,
    }


def secret_safety_audit(artifacts: dict[str, Any]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for artifact, payload in artifacts.items():
        text = json.dumps(payload, sort_keys=True)
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                hits.append(
                    {
                        "artifact": artifact,
                        "pattern": name,
                        "match_start": match.start(),
                        "match_sha256": sha256_bytes(match.group(0).encode("utf-8")),
                    }
                )
    return {
        "schema_version": "telos.iter174.secret_safety_audit.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not hits else "fail",
        "scanned_artifact_count": len(artifacts),
        "secret_hit_count": len(hits),
        "patterns": [name for name, _pattern in SECRET_PATTERNS],
        "hits": hits,
    }


def readiness_decision(
    *,
    membership: dict[str, Any],
    secret_audit: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    if membership["status"] != "pass":
        blocked_reasons.append("menu_membership_audit_failed")
    if secret_audit["status"] != "pass":
        blocked_reasons.append("secret_safety_audit_failed")
    if packet["primary_aggregation_rule_id"] != "majority_catch":
        blocked_reasons.append("primary_rule_changed")
    if not packet["primary_rule_selected_before_outputs"]:
        blocked_reasons.append("primary_rule_not_selected_before_outputs")
    call_accounting = packet["paid_pilot_call_accounting"]
    if call_accounting["planned_calls_plus_retry_reserve"] > CALL_CEILING:
        blocked_reasons.append("planned_call_ceiling_exceeded")
    if Decimal(packet["paid_pilot_spend_ceiling_usd"]) > SPEND_CEILING_USD:
        blocked_reasons.append("spend_ceiling_exceeded")
    return {
        "schema_version": "telos.iter174.readiness_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "readiness_decision": (
            "ready_for_bounded_paid_pilot_hypothesis"
            if not blocked_reasons
            else "blocked_with_reasons"
        ),
        "ready_for_bounded_paid_pilot_hypothesis": not blocked_reasons,
        "ready_for_paid_pilot_execution": False,
        "execution_authorized_by_iter174": False,
        "blocked_reasons": blocked_reasons,
        "recommended_next_gate": {
            "experiment_id": NEXT_EXPERIMENT_ID,
            "gate_type": "bounded paid panel pilot hypothesis and execution gate",
            "provider_call_ceiling": CALL_CEILING,
            "spend_ceiling_usd": f"{SPEND_CEILING_USD:.2f}",
            "new_swebench_execution_ceiling": 0,
            "new_cloud_resource_ceiling": 0,
        },
    }


def audit_report(
    *,
    packet: dict[str, Any],
    membership: dict[str, Any],
    secret_audit: dict[str, Any],
    ready: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    if membership["status"] != "pass":
        failures.append("menu_membership_audit_failed")
    if secret_audit["status"] != "pass":
        failures.append("secret_safety_audit_failed")
    if ready["readiness_decision"] != "ready_for_bounded_paid_pilot_hypothesis":
        failures.append("not_ready_for_bounded_paid_pilot_hypothesis")
    if packet["execution_authorized_by_iter174"]:
        failures.append("paid_execution_authorized_by_zero_spend_gate")
    if packet["provider_calls_performed_by_iter174"] != 0:
        failures.append("provider_calls_performed")
    if packet["credential_probes_performed_by_iter174"] != 0:
        failures.append("credential_probes_performed")
    if packet["model_evaluations_performed_by_iter174"] != 0:
        failures.append("model_evaluations_performed")
    return {
        "schema_version": "telos.iter174.audit_report.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "bars": {
            "provider_calls": 0,
            "credential_probes": 0,
            "model_evaluations": 0,
            "new_swebench_executions": 0,
            "new_cloud_resources": 0,
            "slot_count": membership["slot_count"],
            "frozen_choice_count": membership["frozen_choice_count"],
            "primary_aggregation_rule_id": packet["primary_aggregation_rule_id"],
            "planned_calls_plus_retry_reserve": packet["paid_pilot_call_accounting"][
                "planned_calls_plus_retry_reserve"
            ],
            "future_paid_provider_call_ceiling": CALL_CEILING,
            "future_paid_spend_ceiling_usd": f"{SPEND_CEILING_USD:.2f}",
            "secret_hit_count": secret_audit["secret_hit_count"],
            "execution_authorized_by_iter174": False,
            "leaderboard_claimed": False,
            "model_superiority_claimed": False,
            "sota_claimed": False,
            "natural_frequency_claimed": False,
            "broad_robustness_claimed": False,
        },
    }


def result_markdown(
    *,
    audit: dict[str, Any],
    packet: dict[str, Any],
    membership: dict[str, Any],
    secret_audit: dict[str, Any],
    ready: dict[str, Any],
) -> str:
    choice_lines = "\n".join(
        "- `{slot_id}`: `{candidate}` / `{model}` via `{api_family}`".format(
            slot_id=choice["slot_id"],
            candidate=choice["chosen_candidate_id"],
            model=choice["exact_model_id"],
            api_family=choice["api_family"],
        )
        for choice in packet["frozen_default_choices"]
    )
    failures = "\n".join(f"- `{failure}`" for failure in audit["failures"]) or "- none"
    next_gate = ready["recommended_next_gate"]
    return f"""# Iteration 174 Result - Reward-Hack Panel Default Choice Freeze

Status: `{audit["status"]}`.

## What this gate did

This zero-spend gate froze exact non-secret default choices from the iter173 public binding menu before
any provider output was observed. It made no provider calls, credential probes, model evaluations,
SWE-bench executions, or cloud-resource changes.

## Frozen Defaults

{choice_lines}

These are defaults for the next bounded paid-pilot hypothesis only. Iter174 does not authorize paid
execution and does not prove any model or panel score.

## Preserved Controls

- Primary aggregation rule: `{packet["primary_aggregation_rule_id"]}`.
- Frozen choices in public menu: `{membership["frozen_choice_count"]}` of `{membership["slot_count"]}`.
- Planned bounded pilot calls plus retry reserve:
  `{packet["paid_pilot_call_accounting"]["planned_calls_plus_retry_reserve"]}` of `160`.
- Spend ceiling: `${packet["paid_pilot_spend_ceiling_usd"]}`.
- Secret/project/account hits: `{secret_audit["secret_hit_count"]}`.

Readiness decision: `{ready["readiness_decision"]}`.

Recommended next gate: `{next_gate["experiment_id"]}` ({next_gate["gate_type"]}), with provider-call
ceiling `{next_gate["provider_call_ceiling"]}` and spend ceiling `${next_gate["spend_ceiling_usd"]}`.

Failures:

{failures}

## Claim Boundary

Supported if status is pass: Telos has a zero-spend default model/API choice freeze for the reward-hack
independent judge-panel path.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, paid execution authorization, or claim that the frozen providers were actually called.

## Evidence

- `proof/default_choice_packet.json`
- `proof/menu_membership_audit.json`
- `proof/secret_safety_audit.json`
- `proof/readiness_decision.json`
- `proof/audit_report.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_default_choice_freeze.json`
"""


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    menu = read_json(PUBLIC_MENU)
    template = read_json(CHOICE_TEMPLATE)
    iter173_ready = read_json(ITER173_READINESS)
    read_json(SOURCE_ALIGNMENT)
    primary_rule = read_json(PRIMARY_RULE)
    paid_plan = read_json(PAID_PLAN)

    packet, choice_failures = default_choice_packet(
        menu=menu,
        primary_rule=primary_rule,
        paid_plan=paid_plan,
        template=template,
    )
    membership = menu_membership_audit(
        packet=packet,
        menu=menu,
        template=template,
        choice_failures=choice_failures,
    )
    secret_audit = secret_safety_audit(
        {
            rel(DEFAULT_PACKET): packet,
            rel(MEMBERSHIP_AUDIT): membership,
        }
    )
    ready = readiness_decision(
        membership=membership,
        secret_audit=secret_audit,
        packet=packet,
    )
    audit = audit_report(
        packet=packet,
        membership=membership,
        secret_audit=secret_audit,
        ready=ready,
    )
    status = audit["status"]

    endpoint = {
        "schema_version": "telos.iter174.endpoint_results.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "readiness_decision": ready["readiness_decision"],
        "provider_calls": 0,
        "credential_probes": 0,
        "model_evaluations": 0,
        "new_swebench_executions": 0,
        "new_cloud_resources": 0,
        "execution_authorized_by_iter174": False,
        "leaderboard_claimed": False,
        "model_superiority_claimed": False,
        "sota_claimed": False,
        "natural_frequency_claimed": False,
        "broad_reward_model_robustness_claimed": False,
    }
    input_hashes = {
        rel(HYPOTHESIS): sha256_file(HYPOTHESIS),
        rel(ITER173_RESULT): sha256_file(ITER173_RESULT),
        rel(PUBLIC_MENU): sha256_file(PUBLIC_MENU),
        rel(CHOICE_TEMPLATE): sha256_file(CHOICE_TEMPLATE),
        rel(ITER173_READINESS): sha256_file(ITER173_READINESS),
        rel(SOURCE_ALIGNMENT): sha256_file(SOURCE_ALIGNMENT),
        rel(PRIMARY_RULE): sha256_file(PRIMARY_RULE),
        rel(PAID_PLAN): sha256_file(PAID_PLAN),
    }
    run_summary = {
        "schema_version": "telos.iter174.run_summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": now_utc(),
        "status": status,
        "failures": audit["failures"],
        "input_hashes": input_hashes,
        "prior_readiness_decision": iter173_ready["readiness_decision"],
        "readiness_decision": ready["readiness_decision"],
        "frozen_choice_count": membership["frozen_choice_count"],
        "primary_aggregation_rule_id": packet["primary_aggregation_rule_id"],
        "planned_calls_plus_retry_reserve": packet["paid_pilot_call_accounting"][
            "planned_calls_plus_retry_reserve"
        ],
        "secret_hit_count": secret_audit["secret_hit_count"],
        "recommended_next_gate": NEXT_EXPERIMENT_ID,
        "provider_calls": 0,
        "credential_probes": 0,
        "model_evaluations": 0,
        "new_swebench_executions": 0,
        "new_cloud_resources": 0,
    }
    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/default_choice_packet.json",
            f"experiments/{EXPERIMENT_ID}/proof/menu_membership_audit.json",
            f"experiments/{EXPERIMENT_ID}/proof/secret_safety_audit.json",
            f"experiments/{EXPERIMENT_ID}/proof/readiness_decision.json",
            f"experiments/{EXPERIMENT_ID}/proof/audit_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_reward_hack_panel_default_choice_freeze.json",
        ],
        "insight": (
            "The public menu can be converted into an exact default binding packet without spend, "
            "while preserving the rule, budget, and no-substitution controls."
        ),
        "next_action": (
            "Pre-register and run the bounded paid panel pilot only under the frozen defaults, "
            "call/spend ceilings, runtime credential controls, and no-overclaim boundary."
        ),
    }
    receipt = {
        "receipt_id": f"iter174-reward-hack-panel-default-choice-freeze-{status}",
        "task_id": f"telos:{EXPERIMENT_ID}",
        "agent_id": "codex-local-zero-spend-default-choice-freeze",
        "benchmark_id": "reward_hack_benchmark_v1",
        "status": status,
        "stated_goal": (
            "Freeze exact non-secret default model/API choices from the iter173 public menu "
            "without provider calls or credential probes."
        ),
        "acceptance_criteria": [
            "Zero provider calls, credential probes, model evaluations, SWE-bench executions, and cloud resources.",
            "Every frozen choice comes from the iter173 public menu and operator-choice template.",
            "No committed artifact contains secrets, bearer tokens, project IDs, or service accounts.",
            "The iter171 majority_catch primary aggregation rule remains frozen.",
            "Future paid pilot remains capped at 160 provider calls and $50.00.",
            "No leaderboard, model-superiority, SOTA, natural-frequency, or broad robustness claim is made.",
        ],
        "evidence": [
            {"artifact": rel(DEFAULT_PACKET), "kind": "artifact", "status": status},
            {"artifact": rel(MEMBERSHIP_AUDIT), "kind": "artifact", "status": status},
            {"artifact": rel(SECRET_AUDIT), "kind": "artifact", "status": status},
            {"artifact": rel(READINESS), "kind": "artifact", "status": status},
            {"artifact": rel(AUDIT), "kind": "adversarial_review", "status": status},
        ],
        "falsifiers": [
            "The gate fails if any provider call, credential probe, or model evaluation occurs.",
            "The gate fails if any frozen choice is absent from the iter173 public menu.",
            "The gate fails if a committed artifact contains secrets or private project/account identifiers.",
            "The gate fails if the primary aggregation rule changes after iter171.",
            "The gate fails if a paid pilot is authorized above 160 calls or $50.00.",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)

    for path, payload in [
        (DEFAULT_PACKET, packet),
        (MEMBERSHIP_AUDIT, membership),
        (SECRET_AUDIT, secret_audit),
        (READINESS, ready),
        (AUDIT, audit),
        (ENDPOINT, endpoint),
        (RUN_SUMMARY, run_summary),
        (LEARNING, learning),
        (RECEIPT, receipt),
    ]:
        write_json(path, payload)
    RESULT.write_text(
        result_markdown(
            audit=audit,
            packet=packet,
            membership=membership,
            secret_audit=secret_audit,
            ready=ready,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"experiment_id": EXPERIMENT_ID, "status": status}, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
