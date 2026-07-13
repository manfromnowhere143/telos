#!/usr/bin/env python3
"""Build iter173 reward-hack panel public binding menu without provider calls."""

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
EXPERIMENT_ID = "iter173_reward_hack_panel_public_binding_menu"
NEXT_EXPERIMENT_ID = "iter174_reward_hack_panel_default_choice_freeze"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"

ITER172_RESULT = ROOT / "experiments" / "iter172_reward_hack_panel_operator_binding_recovery" / "RESULT.md"
OPERATOR_PACKET = (
    ROOT
    / "experiments"
    / "iter172_reward_hack_panel_operator_binding_recovery"
    / "proof"
    / "operator_binding_packet.json"
)
MISSING_INPUTS = (
    ROOT
    / "experiments"
    / "iter172_reward_hack_panel_operator_binding_recovery"
    / "proof"
    / "missing_operator_inputs.json"
)
ITER172_READINESS = (
    ROOT
    / "experiments"
    / "iter172_reward_hack_panel_operator_binding_recovery"
    / "proof"
    / "readiness_decision.json"
)
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

PUBLIC_MENU = PROOF / "public_binding_menu.json"
CHOICE_TEMPLATE = PROOF / "operator_choice_template.json"
SOURCE_ALIGNMENT = PROOF / "source_alignment.json"
REJECTIONS = PROOF / "rejection_reasons.json"
READINESS = PROOF / "readiness_decision.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
AUDIT = PROOF / "audit_report.json"
ENDPOINT = PROOF / "endpoint_results.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_reward_hack_panel_public_binding_menu.json"

CALL_CEILING = 160
SPEND_CEILING_USD = Decimal("50.00")
RETRIEVED_AT_UTC = "2026-07-13T19:40:00Z"

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


def source_alignment() -> dict[str, Any]:
    return {
        "schema_version": "telos.iter173.source_alignment.v1",
        "experiment_id": EXPERIMENT_ID,
        "retrieved_at_utc": RETRIEVED_AT_UTC,
        "method": "Official public provider documentation only; no provider API calls or credential probes.",
        "sources": [
            {
                "provider_family": "google_vertex_or_gemini",
                "source_url": "https://ai.google.dev/gemini-api/docs/structured-output",
                "observed": "Gemini structured output uses response_format with JSON schema.",
            },
            {
                "provider_family": "google_vertex_or_gemini",
                "source_url": "https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash",
                "observed": "gemini-2.5-flash is a stable model with structured-output support.",
            },
            {
                "provider_family": "google_vertex_or_gemini",
                "source_url": "https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash",
                "observed": "gemini-3.5-flash is a stable model with structured-output support.",
            },
            {
                "provider_family": "openai",
                "source_url": "https://developers.openai.com/api/docs/guides/structured-outputs",
                "observed": "OpenAI structured outputs support strict JSON schema response formats.",
            },
            {
                "provider_family": "openai",
                "source_url": "https://developers.openai.com/api/docs/models",
                "observed": "OpenAI public model catalog lists GPT-5.6 family API model IDs.",
            },
            {
                "provider_family": "anthropic",
                "source_url": "https://platform.claude.com/docs/en/build-with-claude/structured-outputs",
                "observed": "Claude structured outputs use output_config JSON schema.",
            },
            {
                "provider_family": "anthropic",
                "source_url": "https://docs.anthropic.com/en/docs/about-claude/models/overview",
                "observed": "Anthropic public model catalog lists Claude Opus 4.8, Sonnet 5, and Fable 5.",
            },
        ],
    }


def candidate(
    *,
    candidate_id: str,
    model_id: str,
    api_family: str,
    api_route: str,
    credential_route: str,
    structured_mode: str,
    source_urls: list[str],
    rationale: str,
    recommendation: str,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "exact_model_id": model_id,
        "api_family": api_family,
        "api_route": api_route,
        "credential_source_route": credential_route,
        "private_identifier_policy": "runtime_placeholder_only",
        "structured_output_mode": structured_mode,
        "source_urls": source_urls,
        "rationale": rationale,
        "recommendation": recommendation,
        "notes": notes or [],
    }


def public_menu(primary_rule: dict[str, Any], paid_plan: dict[str, Any]) -> dict[str, Any]:
    google_sources = [
        "https://ai.google.dev/gemini-api/docs/structured-output",
        "https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash",
        "https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash",
    ]
    openai_sources = [
        "https://developers.openai.com/api/docs/guides/structured-outputs",
        "https://developers.openai.com/api/docs/models",
    ]
    anthropic_sources = [
        "https://platform.claude.com/docs/en/build-with-claude/structured-outputs",
        "https://docs.anthropic.com/en/docs/about-claude/models/overview",
    ]
    slots = [
        {
            "slot_id": "google_continuity_fast_judge",
            "provider_family": "google_vertex_or_gemini",
            "menu_status": "menu_ready_for_operator_choice",
            "recommended_candidate_id": "google_continuity_gemini_2_5_flash_vertex",
            "candidates": [
                candidate(
                    candidate_id="google_continuity_gemini_2_5_flash_vertex",
                    model_id="gemini-2.5-flash",
                    api_family="Google Vertex AI generateContent or Gemini API generateContent",
                    api_route="runtime_placeholder_vertex_or_gemini_generate_content",
                    credential_route="runtime_adc_or_runtime_api_key_outside_repo",
                    structured_mode="response_format_json_schema_or_provider_native_equivalent",
                    source_urls=google_sources,
                    rationale="Preserves the iter161/iter165/iter167 continuity model while adding provider-native structured output.",
                    recommendation="recommended_continuity_choice",
                ),
                candidate(
                    candidate_id="google_current_flash_gemini_3_5_flash",
                    model_id="gemini-3.5-flash",
                    api_family="Google Gemini API generateContent",
                    api_route="runtime_placeholder_gemini_generate_content",
                    credential_route="runtime_api_key_or_adc_outside_repo",
                    structured_mode="response_format_json_schema",
                    source_urls=google_sources,
                    rationale="Current public flash-family candidate for speed-oriented judging if operator chooses to move beyond continuity.",
                    recommendation="acceptable_alternative_requires_explicit_choice",
                ),
            ],
        },
        {
            "slot_id": "openai_reasoning_judge",
            "provider_family": "openai",
            "menu_status": "menu_ready_for_operator_choice",
            "recommended_candidate_id": "openai_balanced_gpt_5_6_terra",
            "candidates": [
                candidate(
                    candidate_id="openai_balanced_gpt_5_6_terra",
                    model_id="gpt-5.6-terra",
                    api_family="OpenAI Responses API",
                    api_route="runtime_placeholder_openai_responses",
                    credential_route="runtime_OPENAI_API_KEY_outside_repo",
                    structured_mode="response_format_json_schema_strict_true",
                    source_urls=openai_sources,
                    rationale="Preserves the frontier model family already used in reward-hack artifacts while adding strict structured output.",
                    recommendation="recommended_independent_reasoning_choice",
                ),
                candidate(
                    candidate_id="openai_flagship_gpt_5_6_sol",
                    model_id="gpt-5.6-sol",
                    api_family="OpenAI Responses API",
                    api_route="runtime_placeholder_openai_responses",
                    credential_route="runtime_OPENAI_API_KEY_outside_repo",
                    structured_mode="response_format_json_schema_strict_true",
                    source_urls=openai_sources,
                    rationale="Higher-capability public catalog option if operator accepts higher expected cost/latency.",
                    recommendation="acceptable_alternative_requires_explicit_choice",
                ),
            ],
        },
        {
            "slot_id": "anthropic_reasoning_or_safety_judge",
            "provider_family": "anthropic",
            "menu_status": "menu_ready_for_operator_choice",
            "recommended_candidate_id": "anthropic_opus_4_8",
            "candidates": [
                candidate(
                    candidate_id="anthropic_opus_4_8",
                    model_id="claude-opus-4-8",
                    api_family="Anthropic Messages API",
                    api_route="runtime_placeholder_anthropic_messages",
                    credential_route="runtime_ANTHROPIC_API_KEY_outside_repo",
                    structured_mode="output_config_json_schema",
                    source_urls=anthropic_sources,
                    rationale="Preserves the Anthropic frontier judge family used in prior reward-hack artifacts while using native structured output.",
                    recommendation="recommended_independent_reasoning_choice",
                ),
                candidate(
                    candidate_id="anthropic_sonnet_5",
                    model_id="claude-sonnet-5",
                    api_family="Anthropic Messages API",
                    api_route="runtime_placeholder_anthropic_messages",
                    credential_route="runtime_ANTHROPIC_API_KEY_outside_repo",
                    structured_mode="output_config_json_schema",
                    source_urls=anthropic_sources,
                    rationale="Balanced public catalog option if operator chooses lower expected latency/cost than Opus.",
                    recommendation="acceptable_alternative_requires_explicit_choice",
                ),
            ],
        },
    ]
    return {
        "schema_version": "telos.iter173.public_binding_menu.v1",
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": now_utc(),
        "retrieved_at_utc": RETRIEVED_AT_UTC,
        "primary_aggregation_rule_id": primary_rule["primary_rule_id"],
        "primary_rule_selected_before_outputs": primary_rule["selected_before_outputs"],
        "paid_pilot_call_accounting": paid_plan["call_accounting"],
        "paid_pilot_spend_ceiling_usd": paid_plan["spend_accounting"]["spend_ceiling_usd"],
        "slot_menus": slots,
        "claim_boundary": "Public binding menu only; no provider was called, scored, ranked, or compared.",
    }


def choice_template(menu: dict[str, Any]) -> dict[str, Any]:
    slots = []
    for slot in menu["slot_menus"]:
        slots.append(
            {
                "slot_id": slot["slot_id"],
                "provider_family": slot["provider_family"],
                "choose_one_candidate_id_from_menu": [
                    row["candidate_id"] for row in slot["candidates"]
                ],
                "exact_model_id": "<copy_exact_model_id_from_chosen_candidate>",
                "api_family": "<copy_api_family_from_chosen_candidate>",
                "api_route": "<runtime_placeholder_only_no_private_project_or_account_id>",
                "credential_source_route": "<runtime_env_or_adc_label_only_no_secret_value>",
                "private_identifier_policy": "runtime_placeholder_only",
                "structured_output_mode": "<copy_structured_output_mode_from_chosen_candidate>",
            }
        )
    return {
        "schema_version": "telos.iter173.operator_choice_template.v1",
        "experiment_id": EXPERIMENT_ID,
        "instructions": [
            "Fill with non-secret labels only.",
            "Do not commit API keys, bearer tokens, service-account JSON, project IDs, account IDs, or quota project names.",
            "Do not alter the iter171 primary aggregation rule or iter171 call/spend ceilings.",
        ],
        "slots": slots,
    }


def rejection_reasons() -> dict[str, Any]:
    return {
        "schema_version": "telos.iter173.rejection_reasons.v1",
        "experiment_id": EXPERIMENT_ID,
        "rejected_option_classes": [
            {
                "option_class": "unsourced_model_id",
                "reason": "No candidate may enter the operator menu without a public source URL.",
            },
            {
                "option_class": "preview_or_experimental_without_explicit_choice",
                "reason": "Preview/experimental options require a separate explicit operator choice and cannot be defaulted.",
            },
            {
                "option_class": "credential_or_project_value",
                "reason": "Secrets and private identifiers are not binding choices and must stay outside committed artifacts.",
            },
            {
                "option_class": "post_output_model_substitution",
                "reason": "Changing a model after seeing outputs would invalidate the pre-registered panel design.",
            },
        ],
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
        "schema_version": "telos.iter173.secret_safety_audit.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not hits else "fail",
        "scanned_artifact_count": len(artifacts),
        "secret_hit_count": len(hits),
        "patterns": [name for name, _pattern in SECRET_PATTERNS],
        "hits": hits,
    }


def readiness(menu: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    for slot in menu["slot_menus"]:
        if not slot["candidates"]:
            blocked_reasons.append(f"{slot['slot_id']}: no source-linked public candidates")
        for candidate_row in slot["candidates"]:
            if not candidate_row["source_urls"]:
                blocked_reasons.append(f"{candidate_row['candidate_id']}: missing source URL")
    source_urls = {row["source_url"] for row in source["sources"]}
    for slot in menu["slot_menus"]:
        for candidate_row in slot["candidates"]:
            for url in candidate_row["source_urls"]:
                if url not in source_urls:
                    blocked_reasons.append(f"{candidate_row['candidate_id']}: source not in alignment")
    return {
        "schema_version": "telos.iter173.readiness_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "readiness_decision": (
            "menu_ready_for_operator_choice" if not blocked_reasons else "blocked_with_reasons"
        ),
        "ready_for_paid_pilot": False,
        "execution_authorized_by_iter173": False,
        "blocked_reasons": blocked_reasons,
        "recommended_next_gate": {
            "experiment_id": NEXT_EXPERIMENT_ID,
            "gate_type": "zero-spend default model/API choice freeze",
            "provider_call_ceiling": 0,
            "spend_ceiling_usd": "0.00",
            "new_swebench_execution_ceiling": 0,
            "new_cloud_resource_ceiling": 0,
        },
    }


def audit_report(
    menu: dict[str, Any],
    source: dict[str, Any],
    template: dict[str, Any],
    secret_audit: dict[str, Any],
    ready: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    if menu["primary_aggregation_rule_id"] != "majority_catch":
        failures.append("primary_rule_changed")
    if not menu["primary_rule_selected_before_outputs"]:
        failures.append("primary_rule_not_selected_before_outputs")
    if menu["paid_pilot_call_accounting"]["planned_calls_plus_retry_reserve"] > CALL_CEILING:
        failures.append("planned_call_ceiling_exceeded")
    if Decimal(menu["paid_pilot_spend_ceiling_usd"]) > SPEND_CEILING_USD:
        failures.append("spend_ceiling_exceeded")
    if len(source["sources"]) < 6:
        failures.append("insufficient_source_coverage")
    if any(not slot["candidates"] for slot in menu["slot_menus"]):
        failures.append("slot_without_candidate")
    if secret_audit["status"] != "pass":
        failures.append("secret_safety_audit_failed")
    if ready["readiness_decision"] != "menu_ready_for_operator_choice":
        failures.append("menu_not_ready_for_operator_choice")
    if len(template["slots"]) != len(menu["slot_menus"]):
        failures.append("operator_choice_template_slot_mismatch")
    return {
        "schema_version": "telos.iter173.audit_report.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "bars": {
            "provider_calls": 0,
            "credential_probes": 0,
            "model_evaluations": 0,
            "new_swebench_executions": 0,
            "new_cloud_resources": 0,
            "slot_count": len(menu["slot_menus"]),
            "source_count": len(source["sources"]),
            "candidate_count": sum(len(slot["candidates"]) for slot in menu["slot_menus"]),
            "primary_aggregation_rule_id": menu["primary_aggregation_rule_id"],
            "planned_calls_plus_retry_reserve": menu["paid_pilot_call_accounting"][
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
    menu: dict[str, Any],
    secret_audit: dict[str, Any],
    ready: dict[str, Any],
) -> str:
    slot_lines = "\n".join(
        "- `{slot_id}`: recommended `{recommended}`; candidates `{count}`".format(
            slot_id=slot["slot_id"],
            recommended=slot["recommended_candidate_id"],
            count=len(slot["candidates"]),
        )
        for slot in menu["slot_menus"]
    )
    failures = "\n".join(f"- `{failure}`" for failure in audit["failures"]) or "- none"
    next_gate = ready["recommended_next_gate"]
    return f"""# Iteration 173 Result - Reward-Hack Panel Public Binding Menu

Status: `{audit["status"]}`.

## What this gate did

This zero-spend gate built a public, source-linked menu of non-secret model/API binding choices for
the reward-hack judge panel. It made no provider calls, credential probes, model evaluations,
SWE-bench executions, or cloud-resource changes.

## Public Binding Menu

{slot_lines}

The menu is ready for operator choice, but it does not authorize paid execution. A later gate must
freeze exact choices from this menu before any provider call.

## Frozen Controls Preserved

- Primary aggregation rule: `{menu["primary_aggregation_rule_id"]}`.
- Planned bounded pilot calls plus retry reserve:
  `{menu["paid_pilot_call_accounting"]["planned_calls_plus_retry_reserve"]}` of `160`.
- Spend ceiling: `${menu["paid_pilot_spend_ceiling_usd"]}`.

## Secret Safety

Generated binding artifacts scanned: `{secret_audit["scanned_artifact_count"]}`.
Secret/project/account hits: `{secret_audit["secret_hit_count"]}`.

Readiness decision: `{ready["readiness_decision"]}`.

Recommended next gate: `{next_gate["experiment_id"]}` ({next_gate["gate_type"]}), with provider-call
ceiling `{next_gate["provider_call_ceiling"]}` and spend ceiling `${next_gate["spend_ceiling_usd"]}`.

Failures:

{failures}

## Claim Boundary

Supported if status is pass: Telos has a zero-spend public binding menu and operator-choice template for
the reward-hack independent judge-panel path.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, or claim that paid provider bindings are executable.

## Evidence

- `proof/public_binding_menu.json`
- `proof/operator_choice_template.json`
- `proof/source_alignment.json`
- `proof/rejection_reasons.json`
- `proof/secret_safety_audit.json`
- `proof/readiness_decision.json`
- `proof/audit_report.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_public_binding_menu.json`
"""


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    primary_rule = read_json(PRIMARY_RULE)
    paid_plan = read_json(PAID_PLAN)
    read_json(OPERATOR_PACKET)
    read_json(MISSING_INPUTS)
    iter172_ready = read_json(ITER172_READINESS)

    source = source_alignment()
    menu = public_menu(primary_rule, paid_plan)
    template = choice_template(menu)
    rejections = rejection_reasons()
    secret_audit = secret_safety_audit(
        {
            rel(PUBLIC_MENU): menu,
            rel(CHOICE_TEMPLATE): template,
            rel(SOURCE_ALIGNMENT): source,
            rel(REJECTIONS): rejections,
        }
    )
    ready = readiness(menu, source)
    audit = audit_report(menu, source, template, secret_audit, ready)
    status = audit["status"]

    endpoint = {
        "schema_version": "telos.iter173.endpoint_results.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "readiness_decision": ready["readiness_decision"],
        "provider_calls": 0,
        "credential_probes": 0,
        "model_evaluations": 0,
        "new_swebench_executions": 0,
        "new_cloud_resources": 0,
        "execution_authorized_by_iter173": False,
        "leaderboard_claimed": False,
        "model_superiority_claimed": False,
        "sota_claimed": False,
        "natural_frequency_claimed": False,
        "broad_reward_model_robustness_claimed": False,
    }
    input_hashes = {
        rel(HYPOTHESIS): sha256_file(HYPOTHESIS),
        rel(ITER172_RESULT): sha256_file(ITER172_RESULT),
        rel(OPERATOR_PACKET): sha256_file(OPERATOR_PACKET),
        rel(MISSING_INPUTS): sha256_file(MISSING_INPUTS),
        rel(ITER172_READINESS): sha256_file(ITER172_READINESS),
        rel(PRIMARY_RULE): sha256_file(PRIMARY_RULE),
        rel(PAID_PLAN): sha256_file(PAID_PLAN),
    }
    run_summary = {
        "schema_version": "telos.iter173.run_summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": now_utc(),
        "status": status,
        "failures": audit["failures"],
        "input_hashes": input_hashes,
        "prior_readiness_decision": iter172_ready["readiness_decision"],
        "readiness_decision": ready["readiness_decision"],
        "source_count": audit["bars"]["source_count"],
        "candidate_count": audit["bars"]["candidate_count"],
        "primary_aggregation_rule_id": menu["primary_aggregation_rule_id"],
        "planned_calls_plus_retry_reserve": menu["paid_pilot_call_accounting"][
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
            f"experiments/{EXPERIMENT_ID}/proof/public_binding_menu.json",
            f"experiments/{EXPERIMENT_ID}/proof/operator_choice_template.json",
            f"experiments/{EXPERIMENT_ID}/proof/source_alignment.json",
            f"experiments/{EXPERIMENT_ID}/proof/rejection_reasons.json",
            f"experiments/{EXPERIMENT_ID}/proof/secret_safety_audit.json",
            f"experiments/{EXPERIMENT_ID}/proof/readiness_decision.json",
            f"experiments/{EXPERIMENT_ID}/proof/audit_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_reward_hack_panel_public_binding_menu.json",
        ],
        "insight": (
            "The panel can advance without spend by turning missing operator bindings into a "
            "source-linked public menu, while still not authorizing paid execution."
        ),
        "next_action": (
            "Run a zero-spend default model/API choice freeze from the public menu before any paid "
            "reward-hack panel call."
        ),
    }
    receipt = {
        "receipt_id": f"iter173-reward-hack-panel-public-binding-menu-{status}",
        "task_id": f"telos:{EXPERIMENT_ID}",
        "agent_id": "codex-local-zero-spend-public-binding-menu",
        "benchmark_id": "reward_hack_benchmark_v1",
        "status": status,
        "stated_goal": (
            "Build a public, source-linked, non-secret binding menu for the reward-hack judge panel "
            "without provider calls or credential probes."
        ),
        "acceptance_criteria": [
            "Zero provider calls, credential probes, model evaluations, SWE-bench executions, and cloud resources.",
            "At least one source-linked public candidate or explicit blocked reason per slot.",
            "No committed artifact contains secrets, bearer tokens, project IDs, or service accounts.",
            "The iter171 majority_catch primary aggregation rule remains frozen.",
            "Future paid pilot remains capped at 160 provider calls and $50.00.",
            "No leaderboard, model-superiority, SOTA, natural-frequency, or broad robustness claim is made.",
        ],
        "evidence": [
            {"artifact": rel(PUBLIC_MENU), "kind": "artifact", "status": status},
            {"artifact": rel(CHOICE_TEMPLATE), "kind": "artifact", "status": status},
            {"artifact": rel(SOURCE_ALIGNMENT), "kind": "artifact", "status": status},
            {"artifact": rel(SECRET_AUDIT), "kind": "artifact", "status": status},
            {"artifact": rel(AUDIT), "kind": "adversarial_review", "status": status},
        ],
        "falsifiers": [
            "The gate fails if any provider call, credential probe, or model evaluation occurs.",
            "The gate fails if any candidate lacks a public source URL.",
            "The gate fails if a committed artifact contains secrets or private project/account identifiers.",
            "The gate fails if the primary aggregation rule changes after iter171.",
            "The gate fails if a paid pilot is authorized above 160 calls or $50.00.",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)

    for path, payload in [
        (PUBLIC_MENU, menu),
        (CHOICE_TEMPLATE, template),
        (SOURCE_ALIGNMENT, source),
        (REJECTIONS, rejections),
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
        result_markdown(audit=audit, menu=menu, secret_audit=secret_audit, ready=ready),
        encoding="utf-8",
    )
    print(json.dumps({"experiment_id": EXPERIMENT_ID, "status": status}, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
