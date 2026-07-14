#!/usr/bin/env python3
"""Design the iter188 Telos mission evidence/data-process audit without spend."""

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
EXPERIMENT_ID = "iter188_telos_mission_data_process_audit_design"
NEXT_EXPERIMENT_ID = "iter189_telos_mission_evidence_data_process_audit"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"
NEXT_HYPOTHESIS = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"

AUDIT_DESIGN_PACKET = PROOF / "audit_design_packet.json"
REQUIRED_SECTION_LIST = PROOF / "future_audit_required_sections.json"
VERIFIER_PLAN = PROOF / "future_verifier_plan.json"
FRESHNESS_EDIT_POLICY = PROOF / "future_freshness_edit_policy.json"
FORBIDDEN_CLAIMS = PROOF / "future_forbidden_claims.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary_audit.json"
FORBIDDEN_SCAN = PROOF / "forbidden_claim_scan.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
ENDPOINT_RESULTS = PROOF / "endpoint_results.json"
AUDIT_REPORT = PROOF / "audit_report.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_telos_mission_data_process_audit_design.json"

NEXT_GATE = f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md"
PROVIDER_CALLS = 0
CREDENTIAL_PROBES = 0
MODEL_EVALUATIONS = 0
PROPERTY_GENERATOR_CALLS = 0
NEW_SWEBENCH_EXECUTIONS = 0
NEW_CLOUD_RESOURCES = 0

PUBLIC_SURFACES = [
    ROOT / "README.md",
    ROOT / "CONTINUITY.md",
    ROOT / "HANDOFF.md",
    ROOT / "docs" / "REPORT.md",
    ROOT / "docs" / "MISSION_LOOP.md",
    ROOT / "docs" / "LITERATURE_ALIGNMENT_2026.md",
    ROOT / "mission" / "loop.json",
]

FROZEN_INPUTS = [
    "README.md",
    "CONTINUITY.md",
    "HANDOFF.md",
    "docs/REPORT.md",
    "docs/MISSION_LOOP.md",
    "docs/LITERATURE_ALIGNMENT_2026.md",
    "mission/loop.json",
    "benchmarks/reward_hack_benchmark_v1/",
    "experiments/iter153_reward_hack_benchmark_seed_materialization/RESULT.md",
    "experiments/iter156_reward_hack_benchmark_v1_manifest/RESULT.md",
    "experiments/iter161_reward_hack_single_model_judge_execution/RESULT.md",
    "experiments/iter165_reward_hack_control_evaluation_rate_limit_recovery/RESULT.md",
    "experiments/iter167_reward_hack_skeptical_judge_calibration/RESULT.md",
    "experiments/iter175_reward_hack_panel_bounded_paid_pilot/RESULT.md",
    "experiments/iter179_reward_hack_panel_full_cohort_adjudication/RESULT.md",
    "experiments/iter181_reward_hack_panel_openai_nondecision_repair_execution/RESULT.md",
    "experiments/iter182_reward_hack_panel_repair_execution_adjudication/RESULT.md",
    "experiments/iter183_reward_hack_panel_public_claim_surface_sync/RESULT.md",
    "experiments/iter184_reward_hack_panel_frontier_research_alignment_design/RESULT.md",
    "experiments/iter185_reward_hack_panel_miss_property_probe_design/RESULT.md",
    "experiments/iter186_reward_hack_panel_property_probe_packet_materialization/RESULT.md",
    "experiments/iter187_reward_hack_property_generator_schema_preflight/RESULT.md",
    "scripts/validate_learning_ledger.py",
    "scripts/validate_mission_loop.py",
    "scripts/validate_docs.py",
    "scripts/validate_receipts.py",
]

REQUIRED_SECTIONS = [
    {
        "section_id": "source_refresh_and_evidence_inputs",
        "title": "Source Refresh And Evidence Inputs",
        "purpose": "List the exact committed local inputs and their hashes before judging claims.",
    },
    {
        "section_id": "defensible_strengths",
        "title": "Defensible Strengths",
        "purpose": "Name what the committed evidence really supports, without upgrading claims.",
    },
    {
        "section_id": "reviewer_attack_surface",
        "title": "Reviewer Attack Surface",
        "purpose": "State the strongest hostile-reviewer objections and data-process gaps.",
    },
    {
        "section_id": "data_lineage_and_receipt_integrity",
        "title": "Data Lineage And Receipt Integrity",
        "purpose": "Trace benchmark rows, packets, model outputs, metrics, learning records, and receipts.",
    },
    {
        "section_id": "freshness_fixes",
        "title": "Freshness Fixes",
        "purpose": "Record only concrete stale public-surface corrections made during the audit.",
    },
    {
        "section_id": "next_bounded_actions",
        "title": "Next Bounded Actions",
        "purpose": "Constrain the next empirical step and preserve spend/leakage boundaries.",
    },
    {
        "section_id": "claim_boundary",
        "title": "Claim Boundary",
        "purpose": "Separate completed audit evidence from unsupported score, product, and SOTA claims.",
    },
]

VERIFIER_CHECKS = [
    {
        "check_id": "required_sections",
        "mechanism": "Parse the audit note and require every iter188 required section heading.",
    },
    {
        "check_id": "claim_boundary",
        "mechanism": "Require an exact claim-boundary paragraph and false flags for unsupported claims.",
    },
    {
        "check_id": "public_metric_freshness",
        "mechanism": "Require public surfaces to preserve unrepaired iter179 17/40 and 0/40 counts.",
    },
    {
        "check_id": "learning_ledger",
        "mechanism": "Run scripts/validate_learning_ledger.py and require the active next action.",
    },
    {
        "check_id": "receipt_presence",
        "mechanism": "Require proof/valid receipts for completed recent gates or explicit legacy exceptions.",
    },
    {
        "check_id": "benchmark_artifact_lineage",
        "mechanism": "Verify benchmark manifest, rows, packets, controls, metrics, probe packets, and schema.",
    },
    {
        "check_id": "forbidden_claims",
        "mechanism": "Scan durable docs and audit outputs for positive forbidden claim patterns.",
    },
    {
        "check_id": "secret_safety",
        "mechanism": "Scan audit outputs and public surfaces for secret and private identifier patterns.",
    },
]

FORBIDDEN_CLAIM_ITEMS = [
    {
        "claim_id": "leaderboard",
        "boundary": "No ranking or leaderboard may be presented from the current evidence.",
    },
    {
        "claim_id": "model_comparison",
        "boundary": "No general model comparison may be presented from bounded panel evidence.",
    },
    {
        "claim_id": "model_superiority",
        "boundary": "No model-superiority claim may be presented from the current evidence.",
    },
    {
        "claim_id": "sota",
        "boundary": "No state-of-the-art or SOTA claim may be presented from the current evidence.",
    },
    {
        "claim_id": "public_benchmark_score",
        "boundary": "No public benchmark score may be presented until the benchmark protocol supports one.",
    },
    {
        "claim_id": "natural_frequency",
        "boundary": "No natural-frequency estimate may be inferred from the constructed benchmark rows.",
    },
    {
        "claim_id": "broad_robustness",
        "boundary": "No broad reward-model robustness claim may be presented from this bounded panel path.",
    },
    {
        "claim_id": "repaired_score",
        "boundary": "No repaired-score claim may replace unrepaired iter179 as the public metric.",
    },
    {
        "claim_id": "production",
        "boundary": "No production deployment or operational product claim may be presented.",
    },
    {
        "claim_id": "product_value",
        "boundary": "No product-value or company-value claim may be presented from research artifacts.",
    },
]

SENTINEL_AUDIT_STANDARD = [
    "pre-register before the audit note or freshness edits",
    "read committed docs/results and named source anchors only",
    "separate defensible strengths, reviewer attack surface, freshness fixes, next actions, and claim boundary",
    "update stale durable docs only when a concrete freshness mismatch is found",
    "add a verifier for required sections, anchors, freshness terms, and forbidden claim boundaries",
    "publish JSON and markdown proof artifacts, tests, result, and handoff",
    "preserve hard forbidden claims even when the audit passes",
]

REQUIRED_VERIFIER_IDS = {
    "required_sections",
    "claim_boundary",
    "public_metric_freshness",
    "learning_ledger",
    "receipt_presence",
    "benchmark_artifact_lineage",
    "forbidden_claims",
}

REQUIRED_FORBIDDEN_IDS = {
    "leaderboard",
    "model_comparison",
    "sota",
    "public_benchmark_score",
    "natural_frequency",
    "broad_robustness",
    "repaired_score",
    "production",
    "product_value",
}

FORBIDDEN_POSITIVE_PATTERNS = [
    (
        "leaderboard_positive_claim",
        re.compile(
            r"\b(?:leaderboard|ranking)\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "public_benchmark_score_positive_claim",
        re.compile(
            r"\bpublic benchmark score\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "model_comparison_positive_claim",
        re.compile(
            r"\bmodel[- ]comparison\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "model_superiority_positive_claim",
        re.compile(
            r"\bmodel[- ]superiority\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "sota_positive_claim",
        re.compile(
            r"\b(?:SOTA|state-of-the-art)\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "natural_frequency_positive_claim",
        re.compile(
            r"\bnatural[- ]frequency\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "broad_robustness_positive_claim",
        re.compile(
            r"\bbroad robustness\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "repaired_score_positive_claim",
        re.compile(
            r"\brepaired[- ]score\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established|made)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "production_positive_claim",
        re.compile(
            r"\bproduction\b.{0,80}\b(?:ready|supported|proven|deployed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "product_value_positive_claim",
        re.compile(
            r"\bproduct[- ]value\b.{0,80}\b"
            r"(?:supported|proven|achieved|claimed|established)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
]

SECRET_PATTERNS = [
    ("google_oauth_token", re.compile(r"ya29\.[A-Za-z0-9._-]+")),
    ("bearer_token", re.compile(r"Bearer\s+(?!\[REDACTED_BEARER_TOKEN\])[A-Za-z0-9._~+/=-]+")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{18,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9._-]{18,}\b")),
    ("gcp_project_path", re.compile(r"projects/[A-Za-z][A-Za-z0-9-]{3,}")),
    ("gcp_project_url", re.compile(r"/projects/[A-Za-z][A-Za-z0-9-]{3,}/")),
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("service_account_email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com")),
]


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def directory_digest(path: Path) -> tuple[int, str]:
    chunks: list[str] = []
    file_count = 0
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        if ".git" in file_path.parts:
            continue
        file_count += 1
        chunks.append(f"{file_path.relative_to(path).as_posix()}:{sha256_file(file_path)}")
    return file_count, sha256_text("\n".join(chunks))


def pretty_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(payload), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit(f"expected object JSON: {rel(path)}")
    return loaded


def frozen_input_inventory() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for item in FROZEN_INPUTS:
        path = ROOT / item
        row: dict[str, Any] = {"path": item}
        if not path.exists():
            row["exists"] = False
            missing.append(item)
        elif path.is_dir():
            file_count, digest = directory_digest(path)
            row.update(
                {
                    "directory_sha256": digest,
                    "exists": True,
                    "file_count": file_count,
                    "type": "directory",
                }
            )
        else:
            row.update({"exists": True, "sha256": sha256_file(path), "type": "file"})
        rows.append(row)
    return {
        "experiment_id": EXPERIMENT_ID,
        "frozen_input_count": len(rows),
        "missing": missing,
        "rows": rows,
        "schema_version": "telos.iter188.frozen_input_inventory.v1",
        "status": "pass" if not missing else "fail",
    }


def audit_design_packet(frozen_inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "audit_kind": "Sentinel-style hostile mission evidence/data-process audit design",
        "claim_boundary": (
            "This gate designs the future audit only. It does not execute the audit, change scores, "
            "authorize provider spend, or upgrade public claims."
        ),
        "experiment_id": EXPERIMENT_ID,
        "frozen_inputs": frozen_inputs["rows"],
        "next_gate": NEXT_GATE,
        "required_sections": REQUIRED_SECTIONS,
        "schema_version": "telos.iter188.audit_design_packet.v1",
        "sentinel_audit_standard": SENTINEL_AUDIT_STANDARD,
        "status": "pass" if frozen_inputs["status"] == "pass" else "fail",
        "verifier_checks": VERIFIER_CHECKS,
    }


def required_section_list() -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "required_section_count": len(REQUIRED_SECTIONS),
        "required_sections": REQUIRED_SECTIONS,
        "schema_version": "telos.iter188.future_audit_required_sections.v1",
        "status": "pass" if len(REQUIRED_SECTIONS) >= 6 else "fail",
    }


def verifier_plan() -> dict[str, Any]:
    check_ids = {check["check_id"] for check in VERIFIER_CHECKS}
    missing = sorted(REQUIRED_VERIFIER_IDS - check_ids)
    return {
        "check_count": len(VERIFIER_CHECKS),
        "checks": VERIFIER_CHECKS,
        "experiment_id": EXPERIMENT_ID,
        "missing_required_check_ids": missing,
        "required_check_ids": sorted(REQUIRED_VERIFIER_IDS),
        "schema_version": "telos.iter188.future_verifier_plan.v1",
        "status": "pass" if not missing else "fail",
    }


def freshness_edit_policy() -> dict[str, Any]:
    return {
        "allowed_surfaces": [
            "README.md",
            "CONTINUITY.md",
            "HANDOFF.md",
            "docs/REPORT.md",
            "docs/MISSION_LOOP.md",
            "docs/LITERATURE_ALIGNMENT_2026.md",
            "mission/loop.json",
        ],
        "disallowed_edits": [
            "Do not alter historical RESULT.md or proof packets to improve a narrative.",
            "Do not change metric values unless a recomputation proof artifact supports the change.",
            "Do not replace unrepaired iter179 as the public metric from documentation review alone.",
            "Do not broaden claims from audit prose, literature notes, or product language.",
        ],
        "experiment_id": EXPERIMENT_ID,
        "required_policy": (
            "A future audit may make only surgical freshness edits when a concrete stale active gate, "
            "current metric, result path, or next-action mismatch is found."
        ),
        "schema_version": "telos.iter188.future_freshness_edit_policy.v1",
        "status": "pass",
    }


def future_forbidden_claims() -> dict[str, Any]:
    claim_ids = {item["claim_id"] for item in FORBIDDEN_CLAIM_ITEMS}
    missing = sorted(REQUIRED_FORBIDDEN_IDS - claim_ids)
    return {
        "claim_count": len(FORBIDDEN_CLAIM_ITEMS),
        "claims": FORBIDDEN_CLAIM_ITEMS,
        "experiment_id": EXPERIMENT_ID,
        "missing_required_claim_ids": missing,
        "required_claim_ids": sorted(REQUIRED_FORBIDDEN_IDS),
        "schema_version": "telos.iter188.future_forbidden_claims.v1",
        "status": "pass" if not missing else "fail",
    }


def endpoint_results() -> dict[str, Any]:
    return {
        "credential_probes": CREDENTIAL_PROBES,
        "estimated_provider_spend_usd": 0.0,
        "experiment_id": EXPERIMENT_ID,
        "model_evaluations": MODEL_EVALUATIONS,
        "new_cloud_resources": NEW_CLOUD_RESOURCES,
        "new_swebench_executions": NEW_SWEBENCH_EXECUTIONS,
        "property_generator_calls": PROPERTY_GENERATOR_CALLS,
        "provider_calls": PROVIDER_CALLS,
        "schema_version": "telos.iter188.endpoint_results.v1",
        "status": "pass",
    }


def claim_boundary_audit() -> dict[str, Any]:
    metrics = read_json(
        ROOT
        / "experiments"
        / "iter179_reward_hack_panel_full_cohort_adjudication"
        / "proof"
        / "full_cohort_panel_metrics.json"
    )
    primary = metrics["rules"]["majority_catch"]
    return {
        "benchmark_score_claim_supported": False,
        "broad_robustness_claim_supported": False,
        "claim_supported": (
            "Telos has a zero-spend design packet for a future mission evidence/data-process audit "
            "over committed local surfaces."
        ),
        "completed_mission_audit_supported": False,
        "experiment_id": EXPERIMENT_ID,
        "leaderboard_claim_supported": False,
        "model_comparison_claim_supported": False,
        "model_superiority_claim_supported": False,
        "natural_frequency_claim_supported": False,
        "primary_public_metric": {
            "control_catches": primary["control_counts"]["catch_count"],
            "control_rows": primary["control_counts"]["attempted"],
            "hack_catches": primary["hack_counts"]["catch_count"],
            "hack_rows": primary["hack_counts"]["attempted"],
            "rule_id": "majority_catch",
        },
        "product_value_claim_supported": False,
        "production_claim_supported": False,
        "public_benchmark_score_claim_supported": False,
        "repaired_score_claim_supported": False,
        "schema_version": "telos.iter188.claim_boundary_audit.v1",
        "sota_claim_supported": False,
        "status": "pass",
    }


def local_negation_before_match(text: str, start: int) -> bool:
    prefix = text[max(0, start - 500) : start].lower()
    sentence_prefix = re.split(r"[.!?]", prefix)[-1]
    return bool(
        re.search(
            r"\b(no|not|none|without|cannot|never|does not|do not|did not|may not)\b",
            sentence_prefix,
        )
    )


def forbidden_claim_scan(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for path in sorted({path for path in paths if path.exists() and path.is_file()}):
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in FORBIDDEN_POSITIVE_PATTERNS:
            for match in pattern.finditer(text):
                if local_negation_before_match(text, match.start()):
                    continue
                hits.append(
                    {
                        "context": " ".join(match.group(0).split())[:180],
                        "path": rel(path),
                        "pattern": name,
                    }
                )
    return {
        "experiment_id": EXPERIMENT_ID,
        "hit_count": len(hits),
        "hits": hits,
        "patterns": [name for name, _pattern in FORBIDDEN_POSITIVE_PATTERNS],
        "schema_version": "telos.iter188.forbidden_claim_scan.v1",
        "status": "pass" if not hits else "fail",
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
    return {
        "experiment_id": EXPERIMENT_ID,
        "hits": hits,
        "patterns": [name for name, _pattern in SECRET_PATTERNS],
        "schema_version": "telos.iter188.secret_safety_audit.v1",
        "scanned_artifact_count": scanned,
        "secret_hit_count": len(hits),
        "status": "pass" if not hits else "fail",
    }


def active_gate_ok() -> bool:
    loop = read_json(ROOT / "mission" / "loop.json")
    text_paths = [
        ROOT / "README.md",
        ROOT / "CONTINUITY.md",
        ROOT / "HANDOFF.md",
        ROOT / "docs" / "MISSION_LOOP.md",
    ]
    text_ok = all(NEXT_GATE in path.read_text(encoding="utf-8", errors="replace") for path in text_paths)
    return loop.get("active_gate") == NEXT_GATE and text_ok and NEXT_HYPOTHESIS.exists()


def build_failures(
    *,
    claim: dict[str, Any],
    design: dict[str, Any],
    endpoint: dict[str, Any],
    forbidden: dict[str, Any],
    forbidden_claims: dict[str, Any],
    frozen_inputs: dict[str, Any],
    required_sections: dict[str, Any],
    secret: dict[str, Any] | None,
    verifier: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if endpoint["provider_calls"] != 0:
        failures.append("provider_calls_not_zero")
    if endpoint["credential_probes"] != 0:
        failures.append("credential_probes_not_zero")
    if endpoint["property_generator_calls"] != 0:
        failures.append("property_generator_calls_not_zero")
    if endpoint["new_swebench_executions"] != 0:
        failures.append("new_swebench_executions_not_zero")
    if endpoint["new_cloud_resources"] != 0:
        failures.append("new_cloud_resources_not_zero")
    if frozen_inputs["frozen_input_count"] < 10:
        failures.append("frozen_input_count_below_10")
    if frozen_inputs["missing"]:
        failures.append("frozen_inputs_missing")
    if required_sections["required_section_count"] < 6:
        failures.append("required_sections_below_6")
    if verifier["missing_required_check_ids"]:
        failures.append("verifier_missing_required_check_ids")
    if forbidden_claims["missing_required_claim_ids"]:
        failures.append("forbidden_claim_list_missing_required_claim_ids")
    if design["status"] != "pass":
        failures.append("audit_design_packet_not_pass")
    if not active_gate_ok():
        failures.append("active_gate_references_not_next_gate")
    primary = claim["primary_public_metric"]
    if primary != {
        "control_catches": 0,
        "control_rows": 40,
        "hack_catches": 17,
        "hack_rows": 40,
        "rule_id": "majority_catch",
    }:
        failures.append("primary_public_metric_not_iter179_unrepaired")
    for flag in [
        "benchmark_score_claim_supported",
        "broad_robustness_claim_supported",
        "completed_mission_audit_supported",
        "leaderboard_claim_supported",
        "model_comparison_claim_supported",
        "model_superiority_claim_supported",
        "natural_frequency_claim_supported",
        "product_value_claim_supported",
        "production_claim_supported",
        "public_benchmark_score_claim_supported",
        "repaired_score_claim_supported",
        "sota_claim_supported",
    ]:
        if claim.get(flag) is not False:
            failures.append(f"claim_boundary_not_false:{flag}")
    if forbidden["status"] != "pass":
        failures.append("forbidden_positive_claim_scan_hits")
    if secret is not None and secret["status"] != "pass":
        failures.append("secret_safety_audit_failed")
    return failures


def audit_report(
    *,
    endpoint: dict[str, Any],
    failures: list[str],
    forbidden: dict[str, Any],
    forbidden_claims: dict[str, Any],
    frozen_inputs: dict[str, Any],
    required_sections: dict[str, Any],
    secret: dict[str, Any],
    status: str,
    verifier: dict[str, Any],
) -> dict[str, Any]:
    return {
        "bars": {
            "active_gate_references_point_to_next_pre_registered_gate": active_gate_ok(),
            "credential_probes": endpoint["credential_probes"],
            "forbidden_positive_claim_hits": forbidden["hit_count"],
            "frozen_input_count": frozen_inputs["frozen_input_count"],
            "missing_forbidden_claim_ids": forbidden_claims["missing_required_claim_ids"],
            "missing_required_verifier_ids": verifier["missing_required_check_ids"],
            "new_cloud_resources": endpoint["new_cloud_resources"],
            "new_swebench_executions": endpoint["new_swebench_executions"],
            "property_generator_calls": endpoint["property_generator_calls"],
            "provider_calls": endpoint["provider_calls"],
            "required_section_count": required_sections["required_section_count"],
            "secret_hit_count": secret["secret_hit_count"],
        },
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "schema_version": "telos.iter188.audit_report.v1",
        "status": status,
    }


def result_markdown(
    *,
    failures: list[str],
    frozen_inputs: dict[str, Any],
    required_sections: dict[str, Any],
    status: str,
    verifier: dict[str, Any],
) -> str:
    failure_text = "\n".join(f"- `{failure}`" for failure in failures) or "- none"
    return f"""# Iteration 188 Result - Telos Mission Data/Process Audit Design

Status: `{status}`.

## What this gate did

This zero-spend gate designed the future Sentinel-style Telos mission evidence/data-process audit. It
made no provider calls, credential probes, model evaluations, property-generator calls, SWE-bench
executions, cloud resource changes, benchmark-score changes, or claim upgrades.

## Design Packet

- Frozen local inputs named: `{frozen_inputs['frozen_input_count']}`.
- Required future audit-note sections: `{required_sections['required_section_count']}`.
- Future verifier checks: `{verifier['check_count']}`.
- Missing required verifier checks: `{verifier['missing_required_check_ids']}`.

Failures / blockers:

{failure_text}

## Future Audit Shape

The next gate must execute the hostile audit over committed local surfaces only. It must check required
sections, public metric freshness, learning-ledger validity, receipt presence, benchmark artifact
lineage, forbidden claims, and secret safety. Freshness edits are allowed only for concrete stale durable
docs; historical result/proof packets must not be edited to improve the narrative.

The active next gate is `{NEXT_GATE}`.

## Claim Boundary

At most, this gate supports a pre-registered zero-spend design for a future mission evidence/data-process
audit over committed Telos surfaces. The public panel metric remains unrepaired iter179 `majority_catch`:
`17/40` hack rows and `0/40` controls.

No completed mission audit, leaderboard ranking, model-comparison result, model-superiority claim,
state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model robustness claim,
production deployment claim, product-value claim, public benchmark score, repaired-score claim, or claim
outside committed iter175-iter188 proof packets is supported.

## Evidence

- `proof/audit_design_packet.json`
- `proof/future_audit_required_sections.json`
- `proof/future_verifier_plan.json`
- `proof/future_freshness_edit_policy.json`
- `proof/future_forbidden_claims.json`
- `proof/claim_boundary_audit.json`
- `proof/forbidden_claim_scan.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_telos_mission_data_process_audit_design.json`
"""


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    frozen = frozen_input_inventory()
    design = audit_design_packet(frozen)
    sections = required_section_list()
    verifier = verifier_plan()
    freshness = freshness_edit_policy()
    forbidden_claims = future_forbidden_claims()
    endpoint = endpoint_results()
    claim = claim_boundary_audit()

    generated_paths = [
        AUDIT_DESIGN_PACKET,
        REQUIRED_SECTION_LIST,
        VERIFIER_PLAN,
        FRESHNESS_EDIT_POLICY,
        FORBIDDEN_CLAIMS,
        CLAIM_BOUNDARY,
        FORBIDDEN_SCAN,
        SECRET_AUDIT,
        ENDPOINT_RESULTS,
        AUDIT_REPORT,
        RUN_SUMMARY,
        LEARNING,
        RECEIPT,
        RESULT,
    ]

    write_json(AUDIT_DESIGN_PACKET, design)
    write_json(REQUIRED_SECTION_LIST, sections)
    write_json(VERIFIER_PLAN, verifier)
    write_json(FRESHNESS_EDIT_POLICY, freshness)
    write_json(FORBIDDEN_CLAIMS, forbidden_claims)
    write_json(CLAIM_BOUNDARY, claim)
    write_json(ENDPOINT_RESULTS, endpoint)

    preliminary_forbidden = forbidden_claim_scan(
        [HYPOTHESIS, NEXT_HYPOTHESIS, *PUBLIC_SURFACES, *generated_paths]
    )
    preliminary_failures = build_failures(
        claim=claim,
        design=design,
        endpoint=endpoint,
        forbidden=preliminary_forbidden,
        forbidden_claims=forbidden_claims,
        frozen_inputs=frozen,
        required_sections=sections,
        secret=None,
        verifier=verifier,
    )
    preliminary_status = "pass" if not preliminary_failures else "fail"
    RESULT.write_text(
        result_markdown(
            failures=preliminary_failures,
            frozen_inputs=frozen,
            required_sections=sections,
            status=preliminary_status,
            verifier=verifier,
        ),
        encoding="utf-8",
    )

    forbidden = forbidden_claim_scan([HYPOTHESIS, NEXT_HYPOTHESIS, *PUBLIC_SURFACES, *generated_paths])
    secret = secret_safety_audit([HYPOTHESIS, NEXT_HYPOTHESIS, *PUBLIC_SURFACES, *generated_paths])
    failures = build_failures(
        claim=claim,
        design=design,
        endpoint=endpoint,
        forbidden=forbidden,
        forbidden_claims=forbidden_claims,
        frozen_inputs=frozen,
        required_sections=sections,
        secret=secret,
        verifier=verifier,
    )
    status = "pass" if not failures else "fail"

    write_json(FORBIDDEN_SCAN, forbidden)
    write_json(SECRET_AUDIT, secret)
    write_json(
        AUDIT_REPORT,
        audit_report(
            endpoint=endpoint,
            failures=failures,
            forbidden=forbidden,
            forbidden_claims=forbidden_claims,
            frozen_inputs=frozen,
            required_sections=sections,
            secret=secret,
            status=status,
            verifier=verifier,
        ),
    )
    run_summary = {
        "credential_probes": CREDENTIAL_PROBES,
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "forbidden_positive_claim_hits": forbidden["hit_count"],
        "frozen_input_count": frozen["frozen_input_count"],
        "generated_at_utc": now_utc(),
        "new_cloud_resources": NEW_CLOUD_RESOURCES,
        "new_swebench_executions": NEW_SWEBENCH_EXECUTIONS,
        "next_gate": NEXT_GATE,
        "property_generator_calls": PROPERTY_GENERATOR_CALLS,
        "provider_calls": PROVIDER_CALLS,
        "required_section_count": sections["required_section_count"],
        "schema_version": "telos.iter188.run_summary.v1",
        "secret_hit_count": secret["secret_hit_count"],
        "status": status,
        "verifier_check_count": verifier["check_count"],
    }
    learning = {
        "evidence_paths": [
            rel(AUDIT_DESIGN_PACKET),
            rel(REQUIRED_SECTION_LIST),
            rel(VERIFIER_PLAN),
            rel(FRESHNESS_EDIT_POLICY),
            rel(FORBIDDEN_CLAIMS),
            rel(CLAIM_BOUNDARY),
            rel(FORBIDDEN_SCAN),
            rel(SECRET_AUDIT),
            rel(RECEIPT),
        ],
        "experiment_id": EXPERIMENT_ID,
        "insight": (
            "Telos now has a zero-spend, verifier-backed design for a hostile mission "
            "evidence/data-process audit before any new property-generator spend."
        )
        if status == "pass"
        else "the mission audit design did not satisfy frozen-input, verifier, or boundary bars",
        "next_action": f"run {NEXT_EXPERIMENT_ID} before any new property-generator spend",
        "result_path": rel(RESULT),
        "schema_version": "telos.learning_record.v1",
        "status": status if status == "pass" else "null",
    }
    write_json(RUN_SUMMARY, run_summary)
    write_json(LEARNING, learning)
    RESULT.write_text(
        result_markdown(
            failures=failures,
            frozen_inputs=frozen,
            required_sections=sections,
            status=status,
            verifier=verifier,
        ),
        encoding="utf-8",
    )

    receipt = {
        "acceptance_criteria": [
            "No provider calls, credential probes, model evaluations, property-generator calls, SWE-bench executions, or cloud resources are used.",
            "The audit design names at least six required future audit-note sections.",
            "The audit design names at least ten frozen committed local inputs.",
            "The future verifier plan includes required-section, claim-boundary, public-metric freshness, learning-ledger, receipt, benchmark-lineage, and forbidden-claim checks.",
            "The future forbidden-claim list includes leaderboard, model-comparison, SOTA, public benchmark score, natural-frequency, broad robustness, repaired-score, production, and product-value boundaries.",
            "The primary public metric remains unrepaired iter179 majority_catch, 17/40 hack rows and 0/40 controls.",
            "No forbidden positive claim is made and no audited artifact contains secrets or private identifiers.",
        ],
        "agent_id": "codex-local-telos-mission-data-process-audit-design",
        "benchmark_id": "telos_mission_evidence_data_process_audit",
        "evidence": [
            {
                "artifact": rel(AUDIT_DESIGN_PACKET),
                "kind": "artifact",
                "notes": f"Frozen local inputs named: {frozen['frozen_input_count']}.",
                "status": status,
            },
            {
                "artifact": rel(VERIFIER_PLAN),
                "kind": "test",
                "notes": f"Verifier checks named: {verifier['check_count']}.",
                "status": status,
            },
            {
                "artifact": rel(FRESHNESS_EDIT_POLICY),
                "kind": "diff_scope",
                "notes": "Future freshness edits constrained to concrete stale durable docs.",
                "status": status,
            },
            {
                "artifact": rel(CLAIM_BOUNDARY),
                "kind": "adversarial_review",
                "notes": "Unsupported score, product, production, and SOTA claims remain false.",
                "status": status,
            },
            {
                "artifact": rel(SECRET_AUDIT),
                "kind": "adversarial_review",
                "notes": f"Secret scan hits: {secret['secret_hit_count']}.",
                "status": status,
            },
        ],
        "falsifiers": [
            "Any provider call, credential probe, model evaluation, property-generator call, SWE-bench execution, or cloud resource change occurs.",
            "The future audit design omits the mechanical verifier plan.",
            "The future verifier plan omits learning-ledger, receipt, benchmark-lineage, public-metric, or forbidden-claim checks.",
            "The design allows audit prose to upgrade leaderboard, model-comparison, SOTA, public benchmark, repaired-score, product, or production claims.",
            "A committed artifact contains secret or private project/account material.",
            "The result presents a completed mission audit or a score upgrade.",
        ],
        "receipt_id": "receipt_telos_mission_data_process_audit_design",
        "status": status,
        "stated_goal": (
            "Design the zero-spend Sentinel-style Telos mission evidence/data-process audit and "
            "pre-register the executable next gate before any new property-generator spend."
        ),
        "task_id": EXPERIMENT_ID,
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(RECEIPT, receipt)

    print(
        pretty_json(
            {
                "credential_probes": CREDENTIAL_PROBES,
                "experiment_id": EXPERIMENT_ID,
                "forbidden_positive_claim_hits": forbidden["hit_count"],
                "frozen_input_count": frozen["frozen_input_count"],
                "property_generator_calls": PROPERTY_GENERATOR_CALLS,
                "provider_calls": PROVIDER_CALLS,
                "required_section_count": sections["required_section_count"],
                "secret_hit_count": secret["secret_hit_count"],
                "status": status,
                "verifier_check_count": verifier["check_count"],
            }
        ).strip()
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
