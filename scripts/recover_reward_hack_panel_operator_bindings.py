#!/usr/bin/env python3
"""Recover iter172 reward-hack panel operator bindings without provider calls."""

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
EXPERIMENT_ID = "iter172_reward_hack_panel_operator_binding_recovery"
NEXT_EXPERIMENT_ID = "iter173_reward_hack_panel_public_binding_menu"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"
OPTIONAL_OPERATOR_CHOICES = EXPERIMENT / "operator_binding_choices.json"

ITER171_RESULT = (
    ROOT / "experiments" / "iter171_reward_hack_panel_model_binding_freeze" / "RESULT.md"
)
BINDING_MANIFEST = (
    ROOT
    / "experiments"
    / "iter171_reward_hack_panel_model_binding_freeze"
    / "proof"
    / "binding_manifest.json"
)
PRIMARY_RULE = (
    ROOT
    / "experiments"
    / "iter171_reward_hack_panel_model_binding_freeze"
    / "proof"
    / "primary_aggregation_rule.json"
)
PAID_PILOT_PLAN = (
    ROOT
    / "experiments"
    / "iter171_reward_hack_panel_model_binding_freeze"
    / "proof"
    / "paid_pilot_plan.json"
)
ITER171_READINESS = (
    ROOT
    / "experiments"
    / "iter171_reward_hack_panel_model_binding_freeze"
    / "proof"
    / "readiness_decision.json"
)

OPERATOR_BINDING_PACKET = PROOF / "operator_binding_packet.json"
MISSING_OPERATOR_INPUTS = PROOF / "missing_operator_inputs.json"
CHOICE_INTAKE_AUDIT = PROOF / "choice_intake_audit.json"
SECRET_SAFETY_AUDIT = PROOF / "secret_safety_audit.json"
READINESS_DECISION = PROOF / "readiness_decision.json"
AUDIT_REPORT = PROOF / "audit_report.json"
ENDPOINT_RESULTS = PROOF / "endpoint_results.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING_RECORD = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_reward_hack_panel_operator_binding_recovery.json"

ALLOWED_STATUSES = {"ready", "blocked", "requires_operator_input"}
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


def stable_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_hash(payload: Any) -> str:
    return sha256_bytes(stable_json_bytes(payload))


def read_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit(f"expected object JSON at {rel(path)}")
    return loaded


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_operator_choices() -> tuple[dict[str, Any] | None, list[str], list[str]]:
    if not OPTIONAL_OPERATOR_CHOICES.exists():
        return None, [], ["operator_binding_choices.json was not supplied"]
    choices = read_json(OPTIONAL_OPERATOR_CHOICES)
    failures: list[str] = []
    notes: list[str] = []
    if choices.get("schema_version") != "telos.iter172.operator_binding_choices.v1":
        failures.append("operator choice schema_version mismatch")
    slots = choices.get("slots")
    if not isinstance(slots, list):
        failures.append("operator choices must contain a slots list")
    return choices, failures, notes


def choices_by_slot(choices: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not choices:
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for row in choices.get("slots", []):
        if isinstance(row, dict) and isinstance(row.get("slot_id"), str):
            mapped[row["slot_id"]] = row
    return mapped


def required_fields_for(slot: dict[str, Any]) -> list[str]:
    provider = slot["provider_family"]
    if provider == "google_vertex":
        return [
            "exact_model_id",
            "api_family",
            "api_route",
            "location",
            "credential_source_route",
            "quota_project_route",
            "private_identifier_policy",
            "structured_output_mode",
        ]
    return [
        "exact_model_id",
        "api_family",
        "api_route",
        "credential_source_route",
        "private_identifier_policy",
        "structured_output_mode",
    ]


def validate_choice(
    slot: dict[str, Any],
    choice: dict[str, Any] | None,
) -> tuple[str, list[str], dict[str, Any] | None]:
    required = required_fields_for(slot)
    if choice is None:
        return "requires_operator_input", [f"missing non-secret choice: {field}" for field in required], None

    missing = [field for field in required if not choice.get(field)]
    provider_mismatch = choice.get("provider_family") != slot["provider_family"]
    if provider_mismatch:
        missing.append("provider_family must match the frozen slot provider")

    model_mismatch = (
        slot.get("exact_model_id") is not None
        and choice.get("exact_model_id") != slot.get("exact_model_id")
    )
    if model_mismatch:
        missing.append("exact_model_id must match the iter171 frozen continuity candidate")

    private_policy = choice.get("private_identifier_policy")
    if private_policy not in {
        "no_private_identifier_committed",
        "runtime_placeholder_only",
    }:
        missing.append("private_identifier_policy must forbid committed private identifiers")

    normalized = {
        "slot_id": slot["slot_id"],
        "provider_family": choice.get("provider_family"),
        "exact_model_id": choice.get("exact_model_id"),
        "api_family": choice.get("api_family"),
        "api_route": choice.get("api_route"),
        "location": choice.get("location"),
        "credential_source_route": choice.get("credential_source_route"),
        "quota_project_route": choice.get("quota_project_route"),
        "private_identifier_policy": choice.get("private_identifier_policy"),
        "structured_output_mode": choice.get("structured_output_mode"),
    }
    status = "ready" if not missing else "requires_operator_input"
    return status, missing, normalized


def build_operator_binding_packet(
    binding_manifest: dict[str, Any],
    primary_rule: dict[str, Any],
    paid_plan: dict[str, Any],
    choices: dict[str, Any] | None,
    choice_failures: list[str],
    choice_notes: list[str],
) -> dict[str, Any]:
    mapped_choices = choices_by_slot(choices)
    rows: list[dict[str, Any]] = []
    for slot in binding_manifest["slot_bindings"]:
        choice = mapped_choices.get(slot["slot_id"])
        status, missing, normalized = validate_choice(slot, choice)
        rows.append(
            {
                "slot_id": slot["slot_id"],
                "provider_family": slot["provider_family"],
                "binding_status": status,
                "operator_choice_supplied": choice is not None,
                "accepted_choice": normalized,
                "required_nonsecret_fields": required_fields_for(slot),
                "missing_or_invalid_nonsecret_fields": missing,
                "iter171_block_reasons": slot["block_reasons_if_not_ready"],
                "frozen_structured_output_template_sha256": slot["structured_output_mode"][
                    "request_template_sha256"
                ],
            }
        )

    status_counts = {
        status: sum(row["binding_status"] == status for row in rows)
        for status in sorted(ALLOWED_STATUSES)
    }
    return {
        "schema_version": "telos.iter172.operator_binding_packet.v1",
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": now_utc(),
        "operator_choices_path": rel(OPTIONAL_OPERATOR_CHOICES),
        "operator_choices_supplied": choices is not None,
        "operator_choice_parse_failures": choice_failures,
        "operator_choice_intake_notes": choice_notes,
        "primary_aggregation_rule_id": primary_rule["primary_rule_id"],
        "primary_rule_selected_before_outputs": primary_rule["selected_before_outputs"],
        "paid_pilot_call_accounting": paid_plan["call_accounting"],
        "paid_pilot_spend_ceiling_usd": paid_plan["spend_accounting"]["spend_ceiling_usd"],
        "slot_count": len(rows),
        "binding_status_counts": status_counts,
        "slot_operator_packets": rows,
        "claim_boundary": "Operator-binding packet only; no provider was called or scored.",
    }


def build_missing_inputs(packet: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for slot in packet["slot_operator_packets"]:
        rows.append(
            {
                "slot_id": slot["slot_id"],
                "provider_family": slot["provider_family"],
                "binding_status": slot["binding_status"],
                "operator_choice_supplied": slot["operator_choice_supplied"],
                "missing_or_invalid_nonsecret_fields": slot["missing_or_invalid_nonsecret_fields"],
                "safe_submission_rule": (
                    "Submit only non-secret strings. Do not commit API keys, bearer tokens, service "
                    "account JSON, project IDs, account IDs, or private quota project names."
                ),
            }
        )
    return {
        "schema_version": "telos.iter172.missing_operator_inputs.v1",
        "experiment_id": EXPERIMENT_ID,
        "missing_slot_count": sum(row["binding_status"] != "ready" for row in rows),
        "rows": rows,
    }


def build_choice_intake_audit(
    choices: dict[str, Any] | None,
    choice_failures: list[str],
    choice_notes: list[str],
    packet: dict[str, Any],
) -> dict[str, Any]:
    supplied_slots = sum(row["operator_choice_supplied"] for row in packet["slot_operator_packets"])
    ready_slots = sum(row["binding_status"] == "ready" for row in packet["slot_operator_packets"])
    return {
        "schema_version": "telos.iter172.choice_intake_audit.v1",
        "experiment_id": EXPERIMENT_ID,
        "operator_choices_supplied": choices is not None,
        "supplied_slot_count": supplied_slots,
        "ready_slot_count": ready_slots,
        "choice_parse_failures": choice_failures,
        "choice_intake_notes": choice_notes,
        "status": "pass" if not choice_failures else "fail",
    }


def build_secret_safety_audit(artifacts: dict[str, Any]) -> dict[str, Any]:
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
        "schema_version": "telos.iter172.secret_safety_audit.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not hits else "fail",
        "scanned_artifact_count": len(artifacts),
        "secret_hit_count": len(hits),
        "patterns": [name for name, _pattern in SECRET_PATTERNS],
        "hits": hits,
    }


def build_readiness(packet: dict[str, Any], missing_inputs: dict[str, Any]) -> dict[str, Any]:
    all_ready = all(row["binding_status"] == "ready" for row in packet["slot_operator_packets"])
    blocked_reasons: list[str] = []
    for row in missing_inputs["rows"]:
        for missing in row["missing_or_invalid_nonsecret_fields"]:
            blocked_reasons.append(f"{row['slot_id']}: {missing}")
    return {
        "schema_version": "telos.iter172.readiness_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "readiness_decision": "ready_for_bounded_paid_pilot" if all_ready else "blocked_with_reasons",
        "ready_for_bounded_paid_pilot": all_ready,
        "execution_authorized_by_iter172": False if not all_ready else "requires_next_paid_hypothesis",
        "slot_binding_statuses": {
            row["slot_id"]: row["binding_status"] for row in packet["slot_operator_packets"]
        },
        "blocked_reasons": blocked_reasons,
        "recommended_next_gate": {
            "experiment_id": NEXT_EXPERIMENT_ID,
            "gate_type": "zero-spend public provider binding menu",
            "provider_call_ceiling": 0,
            "spend_ceiling_usd": "0.00",
            "new_swebench_execution_ceiling": 0,
            "new_cloud_resource_ceiling": 0,
        },
    }


def build_audit(
    packet: dict[str, Any],
    choice_audit: dict[str, Any],
    secret_audit: dict[str, Any],
    readiness: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    statuses = [row["binding_status"] for row in packet["slot_operator_packets"]]
    if len(statuses) != 3:
        failures.append("slot_count_not_three")
    for status in statuses:
        if status not in ALLOWED_STATUSES:
            failures.append(f"unknown_binding_status:{status}")
    if packet["primary_aggregation_rule_id"] != "majority_catch":
        failures.append("primary_rule_changed")
    if not packet["primary_rule_selected_before_outputs"]:
        failures.append("primary_rule_not_selected_before_outputs")
    call_accounting = packet["paid_pilot_call_accounting"]
    if call_accounting["planned_calls_plus_retry_reserve"] > CALL_CEILING:
        failures.append("planned_call_ceiling_exceeded")
    if Decimal(packet["paid_pilot_spend_ceiling_usd"]) > SPEND_CEILING_USD:
        failures.append("spend_ceiling_exceeded")
    if choice_audit["status"] != "pass":
        failures.append("choice_intake_audit_failed")
    if secret_audit["status"] != "pass":
        failures.append("secret_safety_audit_failed")
    if readiness["readiness_decision"] not in {
        "ready_for_bounded_paid_pilot",
        "blocked_with_reasons",
    }:
        failures.append("unknown_readiness_decision")

    return {
        "schema_version": "telos.iter172.audit_report.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "bars": {
            "provider_calls": 0,
            "credential_probes": 0,
            "model_evaluations": 0,
            "new_swebench_executions": 0,
            "new_cloud_resources": 0,
            "slot_binding_statuses": statuses,
            "operator_choices_supplied": packet["operator_choices_supplied"],
            "primary_aggregation_rule_id": packet["primary_aggregation_rule_id"],
            "planned_calls_plus_retry_reserve": call_accounting[
                "planned_calls_plus_retry_reserve"
            ],
            "future_paid_provider_call_ceiling": CALL_CEILING,
            "future_paid_spend_ceiling_usd": f"{SPEND_CEILING_USD:.2f}",
            "secret_hit_count": secret_audit["secret_hit_count"],
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
    missing_inputs: dict[str, Any],
    secret_audit: dict[str, Any],
    readiness: dict[str, Any],
) -> str:
    slot_lines = "\n".join(
        "- `{slot_id}` (`{provider}`): `{status}`, supplied=`{supplied}`".format(
            slot_id=row["slot_id"],
            provider=row["provider_family"],
            status=row["binding_status"],
            supplied=row["operator_choice_supplied"],
        )
        for row in packet["slot_operator_packets"]
    )
    block_lines = "\n".join(f"- {reason}" for reason in readiness["blocked_reasons"]) or "- none"
    failures = "\n".join(f"- `{failure}`" for failure in audit["failures"]) or "- none"
    next_gate = readiness["recommended_next_gate"]
    return f"""# Iteration 172 Result - Reward-Hack Panel Operator Binding Recovery

Status: `{audit["status"]}`.

## What this gate did

This zero-spend recovery gate checked whether non-secret operator binding choices had been supplied for
the iter171 reward-hack judge panel. It made no provider calls, credential probes, model evaluations,
SWE-bench executions, or cloud-resource changes.

## Operator Binding Packet

Operator choices supplied: `{packet["operator_choices_supplied"]}`.

{slot_lines}

Because no complete non-secret choice packet was present, the panel remains blocked. This is the correct
state: no provider is silently substituted and no paid execution is authorized.

## Missing Inputs

Missing slot count: `{missing_inputs["missing_slot_count"]}`.

{block_lines}

## Frozen Controls Preserved

- Primary aggregation rule: `{packet["primary_aggregation_rule_id"]}`.
- Planned bounded pilot calls plus retry reserve:
  `{packet["paid_pilot_call_accounting"]["planned_calls_plus_retry_reserve"]}` of `160`.
- Spend ceiling: `${packet["paid_pilot_spend_ceiling_usd"]}`.

## Secret Safety

Generated binding artifacts scanned: `{secret_audit["scanned_artifact_count"]}`.
Secret/project/account hits: `{secret_audit["secret_hit_count"]}`.

Readiness decision: `{readiness["readiness_decision"]}`.

Recommended next gate: `{next_gate["experiment_id"]}` ({next_gate["gate_type"]}), with provider-call
ceiling `{next_gate["provider_call_ceiling"]}` and spend ceiling `${next_gate["spend_ceiling_usd"]}`.

Failures:

{failures}

## Claim Boundary

Supported if status is pass: Telos has a zero-spend operator-binding recovery packet, explicit missing
non-secret fields, a secret-safety audit, and a blocked readiness decision for the reward-hack independent
judge-panel path.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, or claim that paid provider bindings are executable.

## Evidence

- `proof/operator_binding_packet.json`
- `proof/missing_operator_inputs.json`
- `proof/choice_intake_audit.json`
- `proof/secret_safety_audit.json`
- `proof/readiness_decision.json`
- `proof/audit_report.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_operator_binding_recovery.json`
"""


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    binding_manifest = read_json(BINDING_MANIFEST)
    primary_rule = read_json(PRIMARY_RULE)
    paid_plan = read_json(PAID_PILOT_PLAN)
    iter171_readiness = read_json(ITER171_READINESS)
    choices, choice_failures, choice_notes = load_operator_choices()

    packet = build_operator_binding_packet(
        binding_manifest=binding_manifest,
        primary_rule=primary_rule,
        paid_plan=paid_plan,
        choices=choices,
        choice_failures=choice_failures,
        choice_notes=choice_notes,
    )
    missing_inputs = build_missing_inputs(packet)
    choice_audit = build_choice_intake_audit(choices, choice_failures, choice_notes, packet)
    preliminary_artifacts = {
        rel(OPERATOR_BINDING_PACKET): packet,
        rel(MISSING_OPERATOR_INPUTS): missing_inputs,
        rel(CHOICE_INTAKE_AUDIT): choice_audit,
    }
    if choices is not None:
        preliminary_artifacts[rel(OPTIONAL_OPERATOR_CHOICES)] = choices
    secret_audit = build_secret_safety_audit(preliminary_artifacts)
    readiness = build_readiness(packet, missing_inputs)
    audit = build_audit(
        packet=packet,
        choice_audit=choice_audit,
        secret_audit=secret_audit,
        readiness=readiness,
    )
    status = audit["status"]
    endpoint = {
        "schema_version": "telos.iter172.endpoint_results.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "readiness_decision": readiness["readiness_decision"],
        "provider_calls": 0,
        "credential_probes": 0,
        "model_evaluations": 0,
        "new_swebench_executions": 0,
        "new_cloud_resources": 0,
        "execution_authorized_by_iter172": False,
        "leaderboard_claimed": False,
        "model_superiority_claimed": False,
        "sota_claimed": False,
        "natural_frequency_claimed": False,
        "broad_reward_model_robustness_claimed": False,
    }
    input_hashes = {
        rel(HYPOTHESIS): sha256_file(HYPOTHESIS),
        rel(ITER171_RESULT): sha256_file(ITER171_RESULT),
        rel(BINDING_MANIFEST): sha256_file(BINDING_MANIFEST),
        rel(PRIMARY_RULE): sha256_file(PRIMARY_RULE),
        rel(PAID_PILOT_PLAN): sha256_file(PAID_PILOT_PLAN),
        rel(ITER171_READINESS): sha256_file(ITER171_READINESS),
    }
    if OPTIONAL_OPERATOR_CHOICES.exists():
        input_hashes[rel(OPTIONAL_OPERATOR_CHOICES)] = sha256_file(OPTIONAL_OPERATOR_CHOICES)
    run_summary = {
        "schema_version": "telos.iter172.run_summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": now_utc(),
        "status": status,
        "failures": audit["failures"],
        "input_hashes": input_hashes,
        "operator_choices_supplied": packet["operator_choices_supplied"],
        "slot_binding_statuses": readiness["slot_binding_statuses"],
        "readiness_decision": readiness["readiness_decision"],
        "prior_readiness_decision": iter171_readiness["readiness_decision"],
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
            f"experiments/{EXPERIMENT_ID}/proof/operator_binding_packet.json",
            f"experiments/{EXPERIMENT_ID}/proof/missing_operator_inputs.json",
            f"experiments/{EXPERIMENT_ID}/proof/choice_intake_audit.json",
            f"experiments/{EXPERIMENT_ID}/proof/secret_safety_audit.json",
            f"experiments/{EXPERIMENT_ID}/proof/readiness_decision.json",
            f"experiments/{EXPERIMENT_ID}/proof/audit_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/"
            "receipt_reward_hack_panel_operator_binding_recovery.json",
        ],
        "insight": (
            "No non-secret operator binding choices were supplied, so the panel remains blocked "
            "without spend while preserving the iter171 majority rule and 160-call pilot ceiling."
        ),
        "next_action": (
            "Run a zero-spend public provider binding-menu gate from official docs before any paid "
            "reward-hack panel call."
        ),
    }
    receipt = {
        "receipt_id": f"iter172-reward-hack-panel-operator-binding-recovery-{status}",
        "task_id": f"telos:{EXPERIMENT_ID}",
        "agent_id": "codex-local-zero-spend-operator-binding-recovery",
        "benchmark_id": "reward_hack_benchmark_v1",
        "status": status,
        "stated_goal": (
            "Recover or block the non-secret operator binding choices needed for the iter171 "
            "reward-hack judge panel without provider calls or credential probes."
        ),
        "acceptance_criteria": [
            "Zero provider calls, credential probes, model evaluations, SWE-bench executions, and cloud resources.",
            "Every slot has a ready, blocked, or requires_operator_input binding status.",
            "No committed binding artifact contains secrets, bearer tokens, project IDs, or service accounts.",
            "The iter171 majority_catch primary aggregation rule remains frozen.",
            "Future paid pilot remains capped at 160 provider calls and $50.00.",
            "No leaderboard, model-superiority, SOTA, natural-frequency, or broad robustness claim is made.",
        ],
        "evidence": [
            {"artifact": rel(OPERATOR_BINDING_PACKET), "kind": "artifact", "status": status},
            {"artifact": rel(MISSING_OPERATOR_INPUTS), "kind": "artifact", "status": status},
            {"artifact": rel(CHOICE_INTAKE_AUDIT), "kind": "artifact", "status": status},
            {"artifact": rel(SECRET_SAFETY_AUDIT), "kind": "artifact", "status": status},
            {"artifact": rel(AUDIT_REPORT), "kind": "adversarial_review", "status": status},
        ],
        "falsifiers": [
            "The gate fails if any provider call, credential probe, or model evaluation occurs.",
            "The gate fails if a ready slot lacks exact non-secret model/API binding fields.",
            "The gate fails if a committed artifact contains secrets or private project/account identifiers.",
            "The gate fails if the primary aggregation rule changes after iter171.",
            "The gate fails if a paid pilot is authorized above 160 calls or $50.00.",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)

    write_json(OPERATOR_BINDING_PACKET, packet)
    write_json(MISSING_OPERATOR_INPUTS, missing_inputs)
    write_json(CHOICE_INTAKE_AUDIT, choice_audit)
    write_json(SECRET_SAFETY_AUDIT, secret_audit)
    write_json(READINESS_DECISION, readiness)
    write_json(AUDIT_REPORT, audit)
    write_json(ENDPOINT_RESULTS, endpoint)
    write_json(RUN_SUMMARY, run_summary)
    write_json(LEARNING_RECORD, learning)
    write_json(RECEIPT, receipt)
    RESULT.write_text(
        result_markdown(
            audit=audit,
            packet=packet,
            missing_inputs=missing_inputs,
            secret_audit=secret_audit,
            readiness=readiness,
        ),
        encoding="utf-8",
    )

    print(json.dumps({"experiment_id": EXPERIMENT_ID, "status": status}, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
