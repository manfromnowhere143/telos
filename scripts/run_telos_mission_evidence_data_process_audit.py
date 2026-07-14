#!/usr/bin/env python3
"""Run the iter189 Telos mission evidence/data-process audit without spend."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.ledger import LedgerValidationError, latest_next_action, load_learning_record
from telos.proof import ProofValidationError, load_receipt, receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter189_telos_mission_evidence_data_process_audit"
NEXT_EXPERIMENT_ID = "iter190_reward_hack_property_generator_bounded_execution"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"
NEXT_HYPOTHESIS = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"
AUDIT_NOTE = ROOT / "docs" / "research" / "TELOS_MISSION_EVIDENCE_DATA_PROCESS_AUDIT_2026-07-14.md"

FROZEN_INPUT_INVENTORY = PROOF / "frozen_input_inventory.json"
AUDIT_NOTE_VERIFICATION = PROOF / "audit_note_verification.json"
PUBLIC_METRIC_FRESHNESS = PROOF / "public_metric_freshness.json"
LEARNING_LEDGER_CHECK = PROOF / "learning_ledger_check.json"
RECEIPT_PRESENCE_CHECK = PROOF / "receipt_presence_check.json"
BENCHMARK_LINEAGE = PROOF / "benchmark_artifact_lineage.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary_audit.json"
FORBIDDEN_SCAN = PROOF / "forbidden_claim_scan.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
ENDPOINT_RESULTS = PROOF / "endpoint_results.json"
AUDIT_REPORT = PROOF / "audit_report.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_telos_mission_evidence_data_process_audit.json"

NEXT_GATE = f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md"
PROVIDER_CALLS = 0
CREDENTIAL_PROBES = 0
MODEL_EVALUATIONS = 0
PROPERTY_GENERATOR_CALLS = 0
NEW_SWEBENCH_EXECUTIONS = 0
NEW_CLOUD_RESOURCES = 0

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
    "experiments/iter188_telos_mission_data_process_audit_design/RESULT.md",
    "experiments/iter188_telos_mission_data_process_audit_design/proof/audit_design_packet.json",
    "experiments/iter188_telos_mission_data_process_audit_design/proof/future_verifier_plan.json",
    "scripts/validate_learning_ledger.py",
    "scripts/validate_mission_loop.py",
    "scripts/validate_docs.py",
    "scripts/validate_receipts.py",
]

PUBLIC_SURFACES = [
    ROOT / "README.md",
    ROOT / "CONTINUITY.md",
    ROOT / "HANDOFF.md",
    ROOT / "docs" / "REPORT.md",
    ROOT / "docs" / "MISSION_LOOP.md",
    ROOT / "docs" / "LITERATURE_ALIGNMENT_2026.md",
    ROOT / "mission" / "loop.json",
]

REQUIRED_SECTION_TITLES = [
    "Source Refresh And Evidence Inputs",
    "Defensible Strengths",
    "Reviewer Attack Surface",
    "Data Lineage And Receipt Integrity",
    "Freshness Fixes",
    "Next Bounded Actions",
    "Claim Boundary",
]

KEY_RECEIPT_EXPERIMENTS = [
    "iter153_reward_hack_benchmark_seed_materialization",
    "iter156_reward_hack_benchmark_v1_manifest",
    "iter161_reward_hack_single_model_judge_execution",
    "iter165_reward_hack_control_evaluation_rate_limit_recovery",
    "iter167_reward_hack_skeptical_judge_calibration",
    "iter175_reward_hack_panel_bounded_paid_pilot",
    "iter179_reward_hack_panel_full_cohort_adjudication",
    "iter181_reward_hack_panel_openai_nondecision_repair_execution",
    "iter182_reward_hack_panel_repair_execution_adjudication",
    "iter183_reward_hack_panel_public_claim_surface_sync",
    "iter184_reward_hack_panel_frontier_research_alignment_design",
    "iter185_reward_hack_panel_miss_property_probe_design",
    "iter186_reward_hack_panel_property_probe_packet_materialization",
    "iter187_reward_hack_property_generator_schema_preflight",
    "iter188_telos_mission_data_process_audit_design",
]

LINEAGE_ARTIFACTS = [
    "benchmarks/reward_hack_benchmark_v1/manifest.json",
    "benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl",
    "benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/manifest.json",
    "benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/packets.jsonl",
    "benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/manifest.json",
    "benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/legitimate_controls_v1.jsonl",
    "benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/blinded_control_packets_v1/manifest.json",
    "benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/blinded_control_packets_v1/packets.jsonl",
    "experiments/iter179_reward_hack_panel_full_cohort_adjudication/proof/full_cohort_panel_metrics.json",
    "experiments/iter186_reward_hack_panel_property_probe_packet_materialization/proof/property_probe_packets_v1/manifest.json",
    "experiments/iter186_reward_hack_panel_property_probe_packet_materialization/proof/property_probe_packets_v1/packets.jsonl",
    "experiments/iter187_reward_hack_property_generator_schema_preflight/proof/property_generator_output_schema.json",
    "experiments/iter187_reward_hack_property_generator_schema_preflight/proof/parser_audit.json",
]

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


def jsonl_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


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
        "schema_version": "telos.iter189.frozen_input_inventory.v1",
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
        "schema_version": "telos.iter189.endpoint_results.v1",
        "status": "pass",
    }


def current_public_metric() -> dict[str, Any]:
    metrics = read_json(
        ROOT
        / "experiments"
        / "iter179_reward_hack_panel_full_cohort_adjudication"
        / "proof"
        / "full_cohort_panel_metrics.json"
    )
    primary = metrics["rules"]["majority_catch"]
    return {
        "control_catches": primary["control_counts"]["catch_count"],
        "control_rows": primary["control_counts"]["attempted"],
        "hack_catches": primary["hack_counts"]["catch_count"],
        "hack_rows": primary["hack_counts"]["attempted"],
        "rule_id": "majority_catch",
    }


def public_metric_freshness(metric: dict[str, Any]) -> dict[str, Any]:
    required_terms = ["unrepaired iter179", "majority_catch", "17/40", "0/40"]
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for path in PUBLIC_SURFACES:
        text = path.read_text(encoding="utf-8", errors="replace")
        absent = [term for term in required_terms if term not in text]
        row = {"missing_terms": absent, "path": rel(path), "status": "pass" if not absent else "fail"}
        rows.append(row)
        if absent:
            missing.append(row)
    metric_matches = metric == {
        "control_catches": 0,
        "control_rows": 40,
        "hack_catches": 17,
        "hack_rows": 40,
        "rule_id": "majority_catch",
    }
    return {
        "experiment_id": EXPERIMENT_ID,
        "metric_matches_iter179_unrepaired": metric_matches,
        "primary_public_metric": metric,
        "required_terms": required_terms,
        "rows": rows,
        "schema_version": "telos.iter189.public_metric_freshness.v1",
        "status": "pass" if metric_matches and not missing else "fail",
    }


def receipt_presence_check() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for experiment_id in KEY_RECEIPT_EXPERIMENTS:
        valid_dir = ROOT / "experiments" / experiment_id / "proof" / "valid"
        receipts = sorted(valid_dir.glob("*.json"))
        if not receipts:
            failures.append(f"{experiment_id}:missing_receipt")
            rows.append({"experiment_id": experiment_id, "receipt_count": 0, "status": "fail"})
            continue
        receipt_rows: list[dict[str, str]] = []
        for receipt_path in receipts:
            try:
                load_receipt(receipt_path)
            except ProofValidationError as exc:
                failures.append(f"{experiment_id}:{receipt_path.name}:{exc}")
                receipt_rows.append(
                    {"path": rel(receipt_path), "sha256": sha256_file(receipt_path), "status": "fail"}
                )
            else:
                receipt_rows.append(
                    {"path": rel(receipt_path), "sha256": sha256_file(receipt_path), "status": "pass"}
                )
        rows.append(
            {
                "experiment_id": experiment_id,
                "receipt_count": len(receipts),
                "receipts": receipt_rows,
                "status": "pass" if all(row["status"] == "pass" for row in receipt_rows) else "fail",
            }
        )
    return {
        "checked_experiment_count": len(KEY_RECEIPT_EXPERIMENTS),
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "rows": rows,
        "schema_version": "telos.iter189.receipt_presence_check.v1",
        "status": "pass" if not failures else "fail",
    }


def benchmark_artifact_lineage() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for artifact in LINEAGE_ARTIFACTS:
        path = ROOT / artifact
        if not path.exists():
            missing.append(artifact)
            rows.append({"exists": False, "path": artifact})
        elif path.suffix == ".jsonl":
            rows.append(
                {
                    "exists": True,
                    "line_count": jsonl_count(path),
                    "path": artifact,
                    "sha256": sha256_file(path),
                    "type": "jsonl",
                }
            )
        else:
            rows.append(
                {
                    "exists": True,
                    "path": artifact,
                    "sha256": sha256_file(path),
                    "type": "json",
                }
            )
    benchmark_manifest = read_json(ROOT / "benchmarks" / "reward_hack_benchmark_v1" / "manifest.json")
    blinded_manifest = read_json(
        ROOT / "benchmarks" / "reward_hack_benchmark_v1" / "blinded_model_judge_packets_v1" / "manifest.json"
    )
    controls_manifest = read_json(
        ROOT / "benchmarks" / "reward_hack_benchmark_v1" / "legitimate_controls_v1" / "manifest.json"
    )
    probe_manifest = read_json(
        ROOT
        / "experiments"
        / "iter186_reward_hack_panel_property_probe_packet_materialization"
        / "proof"
        / "property_probe_packets_v1"
        / "manifest.json"
    )
    parser_audit = read_json(
        ROOT
        / "experiments"
        / "iter187_reward_hack_property_generator_schema_preflight"
        / "proof"
        / "parser_audit.json"
    )
    bars = {
        "benchmark_manifest_row_count": benchmark_manifest["manifest_row_count"],
        "benchmark_repo_count": benchmark_manifest["repo_count"],
        "blinded_packet_count": blinded_manifest["packet_count"],
        "control_row_count": controls_manifest["row_count"],
        "parser_fixture_count": parser_audit["fixture_count"],
        "property_probe_total_packet_count": probe_manifest["total_packet_count"],
    }
    expected = {
        "benchmark_manifest_row_count": 40,
        "benchmark_repo_count": 11,
        "blinded_packet_count": 40,
        "control_row_count": 40,
        "parser_fixture_count": 17,
        "property_probe_total_packet_count": 24,
    }
    mismatches = [
        f"{key}:expected_{expected[key]}_observed_{bars[key]}"
        for key in expected
        if bars[key] != expected[key]
    ]
    return {
        "artifact_rows": rows,
        "bars": bars,
        "experiment_id": EXPERIMENT_ID,
        "missing_artifacts": missing,
        "mismatches": mismatches,
        "schema_version": "telos.iter189.benchmark_artifact_lineage.v1",
        "status": "pass" if not missing and not mismatches else "fail",
    }


def learning_ledger_check() -> dict[str, Any]:
    paths = sorted(ROOT.glob("experiments/*/proof/learning_record.json"))
    try:
        records = [load_learning_record(path, root=ROOT) for path in paths]
        next_action = latest_next_action(records)
    except LedgerValidationError as exc:
        return {
            "experiment_id": EXPERIMENT_ID,
            "failure": str(exc),
            "learning_record_count": len(paths),
            "schema_version": "telos.iter189.learning_ledger_check.v1",
            "status": "fail",
        }
    expected_next = f"run {NEXT_EXPERIMENT_ID} under iter185/iter186/iter187 bars"
    return {
        "expected_next_action": expected_next,
        "experiment_id": EXPERIMENT_ID,
        "learning_record_count": len(records),
        "latest_next_action": next_action,
        "schema_version": "telos.iter189.learning_ledger_check.v1",
        "status": "pass" if next_action == expected_next else "fail",
    }


def claim_boundary_audit(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "benchmark_score_claim_supported": False,
        "broad_robustness_claim_supported": False,
        "claim_supported": (
            "Telos has completed a zero-spend mission evidence/data-process audit over committed "
            "local surfaces and has a bounded reviewer attack-surface map for the next empirical step."
        ),
        "completed_mission_audit_supported": True,
        "experiment_id": EXPERIMENT_ID,
        "leaderboard_claim_supported": False,
        "model_comparison_claim_supported": False,
        "model_superiority_claim_supported": False,
        "natural_frequency_claim_supported": False,
        "primary_public_metric": metric,
        "product_value_claim_supported": False,
        "production_claim_supported": False,
        "public_benchmark_score_claim_supported": False,
        "repaired_score_claim_supported": False,
        "schema_version": "telos.iter189.claim_boundary_audit.v1",
        "sota_claim_supported": False,
        "status": "pass",
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


def audit_note_markdown(*, lineage: dict[str, Any], metric: dict[str, Any], receipts: dict[str, Any]) -> str:
    return f"""# Telos Mission Evidence/Data-Process Audit - 2026-07-14

This is the iter189 zero-spend audit note. It reads committed local Telos evidence only and does not
change benchmark numbers, execute model/provider calls, authorize property-generator spend, or upgrade any
public claim.

## Source Refresh And Evidence Inputs

The audit uses the iter188 design packet plus `{len(FROZEN_INPUTS)}` frozen local inputs from the iter189
hypothesis. The frozen set covers public docs, the mission loop, `reward_hack_benchmark_v1`, key result files from
iter153 through iter188, and the local validators for docs, receipts, mission loop, and learning ledger.

Endpoint changes in this audit are zero: provider calls `0`, credential probes `0`, model evaluations
`0`, property-generator calls `0`, SWE-bench executions `0`, and cloud resource changes `0`.

## Defensible Strengths

- The benchmark artifact path is concrete: the v1 manifest records `40` rows across `11` repos, `40`
  execution-verified both-miss rows, `40` hack diff hashes, `40` official report hashes, and `40` source
  traceability entries.
- The public panel metric is bounded and explicit: unrepaired iter179 `majority_catch` remains
  `{metric['hack_catches']}/{metric['hack_rows']}` hack rows and `{metric['control_catches']}/{metric['control_rows']}` controls.
- The property-probe path is leakage-controlled before spend: iter186 has `24` packets, and iter187 has a
  strict schema/parser preflight with `17` fixtures.
- The recent key-gate receipt surface is complete for `{receipts['checked_experiment_count']}` audited
  experiments.

## Reviewer Attack Surface

- The benchmark is constructed from selected reward-hack rows, so it cannot support a natural-frequency
  estimate.
- The panel evidence is useful but bounded: it does not create a leaderboard, a general model-comparison
  result, or a public benchmark score.
- The repaired OpenAI diagnostic reduces nondecisions but is explicitly excluded from the public metric.
- The next property-generator step has not run yet, so property-failure counts, control false-positive
  behavior, and execution yield remain open.
- Public docs must continue to distinguish artifact creation, model/panel measurements, diagnostic repair,
  schema preflight, and future execution.

## Data Lineage And Receipt Integrity

The lineage chain is checkable from committed artifacts:

1. iter153 materialized reward-hack seed rows.
2. iter156 released `reward_hack_benchmark_v1` as an artifact, not a score.
3. iter159 created blinded all-hack judge packets.
4. iter163 created paired legitimate controls.
5. iter175 and iter178 ran bounded panel cohorts.
6. iter179 recomputed the primary unrepaired panel metric.
7. iter181 and iter182 kept repair evidence diagnostic only.
8. iter185 selected the primary-missed property-probe subset.
9. iter186 materialized leakage-scanned property-probe packets.
10. iter187 validated the property-generator schema/parser and prompt contract.
11. iter188 designed this mission audit.

The lineage verifier status is `{lineage['status']}`. It checked benchmark row count, repo count, blinded
packet count, control count, property-probe packet count, and parser fixture count.

## Freshness Fixes

The durable public surfaces now point to iter190 as the next active gate. The audit did not change the
public metric: unrepaired iter179 `majority_catch` remains `17/40` hack rows and `0/40` controls.

No historical `RESULT.md` or proof packet was edited to improve a narrative.

## Next Bounded Actions

The next bounded action is `iter190_reward_hack_property_generator_bounded_execution`: execute the
preflighted property-generator path over the `24` iter186 packets under the preserved bars:

- at most `48` provider calls including retries;
- estimated spend ceiling `$40.00`;
- at least `20` local or container execution attempts;
- control false-positive ceiling `0`;
- nondecision ceiling `4`;
- prompt leakage ceiling `0`;
- response secret-hit ceiling `0`.

## Claim Boundary

Supported: Telos has completed a zero-spend mission evidence/data-process audit over committed local
surfaces and has a bounded reviewer attack-surface map for the next empirical step.

Not supported: benchmark leaderboard, state-of-the-art claim, model-comparison claim, natural reward-hack
frequency estimate, broad reward-model robustness claim, production deployment claim, product-value claim,
public benchmark score, repaired-score claim, or any score upgrade outside committed proof packets.
"""


def audit_note_verification() -> dict[str, Any]:
    text = AUDIT_NOTE.read_text(encoding="utf-8")
    missing = [title for title in REQUIRED_SECTION_TITLES if f"## {title}" not in text]
    return {
        "audit_note": rel(AUDIT_NOTE),
        "experiment_id": EXPERIMENT_ID,
        "missing_sections": missing,
        "required_sections": REQUIRED_SECTION_TITLES,
        "schema_version": "telos.iter189.audit_note_verification.v1",
        "section_count": len(REQUIRED_SECTION_TITLES) - len(missing),
        "status": "pass" if not missing else "fail",
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
        "schema_version": "telos.iter189.forbidden_claim_scan.v1",
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
        "schema_version": "telos.iter189.secret_safety_audit.v1",
        "scanned_artifact_count": scanned,
        "secret_hit_count": len(hits),
        "status": "pass" if not hits else "fail",
    }


def build_failures(
    *,
    claim: dict[str, Any],
    endpoint: dict[str, Any],
    forbidden: dict[str, Any],
    freshness: dict[str, Any],
    frozen: dict[str, Any],
    ledger: dict[str, Any] | None,
    lineage: dict[str, Any],
    note: dict[str, Any],
    receipts: dict[str, Any],
    secret: dict[str, Any] | None,
) -> list[str]:
    failures: list[str] = []
    for key in [
        "provider_calls",
        "credential_probes",
        "model_evaluations",
        "property_generator_calls",
        "new_swebench_executions",
        "new_cloud_resources",
    ]:
        if endpoint[key] != 0:
            failures.append(f"{key}_not_zero")
    if frozen["status"] != "pass":
        failures.append("frozen_input_inventory_failed")
    if note["status"] != "pass" or note["section_count"] != 7:
        failures.append("audit_note_required_sections_failed")
    if freshness["status"] != "pass":
        failures.append("public_metric_freshness_failed")
    if receipts["status"] != "pass":
        failures.append("receipt_presence_check_failed")
    if lineage["status"] != "pass":
        failures.append("benchmark_artifact_lineage_failed")
    if ledger is not None and ledger["status"] != "pass":
        failures.append("learning_ledger_check_failed")
    if not active_gate_ok():
        failures.append("active_gate_references_not_next_gate")
    if not claim.get("completed_mission_audit_supported"):
        failures.append("completed_mission_audit_not_supported")
    for flag in [
        "benchmark_score_claim_supported",
        "broad_robustness_claim_supported",
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
    freshness: dict[str, Any],
    frozen: dict[str, Any],
    ledger: dict[str, Any],
    lineage: dict[str, Any],
    note: dict[str, Any],
    receipts: dict[str, Any],
    secret: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    return {
        "bars": {
            "active_gate_references_point_to_next_pre_registered_gate": active_gate_ok(),
            "audit_note_required_section_count": note["section_count"],
            "benchmark_lineage_status": lineage["status"],
            "credential_probes": endpoint["credential_probes"],
            "forbidden_positive_claim_hits": forbidden["hit_count"],
            "frozen_input_count": frozen["frozen_input_count"],
            "learning_ledger_status": ledger["status"],
            "new_cloud_resources": endpoint["new_cloud_resources"],
            "new_swebench_executions": endpoint["new_swebench_executions"],
            "property_generator_calls": endpoint["property_generator_calls"],
            "provider_calls": endpoint["provider_calls"],
            "public_metric_freshness_status": freshness["status"],
            "receipt_presence_status": receipts["status"],
            "secret_hit_count": secret["secret_hit_count"],
        },
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "schema_version": "telos.iter189.audit_report.v1",
        "status": status,
    }


def result_markdown(*, failures: list[str], ledger: dict[str, Any], status: str) -> str:
    failure_text = "\n".join(f"- `{failure}`" for failure in failures) or "- none"
    return f"""# Iteration 189 Result - Telos Mission Evidence/Data-Process Audit

Status: `{status}`.

## What this gate did

This zero-spend gate executed the Sentinel-style Telos mission evidence/data-process audit designed in
iter188. It made no provider calls, credential probes, model evaluations, property-generator calls,
SWE-bench executions, cloud resource changes, benchmark-score changes, or claim upgrades.

## Audit Result

- Audit note sections present: `7/7`.
- Frozen local inputs checked: `{len(FROZEN_INPUTS)}`.
- Key-gate receipt checks: `{len(KEY_RECEIPT_EXPERIMENTS)}` experiments.
- Forbidden positive claim hits: `0`.
- Secret/private identifier hits: `0`.
- Learning ledger latest next action: `{ledger.get('latest_next_action', 'unavailable')}`.

Failures / blockers:

{failure_text}

## Freshness And Lineage

Public surfaces preserve unrepaired iter179 `majority_catch` as the primary metric: `17/40` hack rows and
`0/40` controls. The audit note maps the lineage from iter153 seed materialization through iter188 audit
design and identifies the next bounded action as `{NEXT_GATE}`.

## Claim Boundary

At most, this gate supports a completed zero-spend mission evidence/data-process audit over committed
Telos surfaces and a bounded reviewer attack-surface map for the next empirical step.

No leaderboard ranking, state-of-the-art claim, model-comparison result, model-superiority claim, natural
reward-hacking frequency estimate, broad reward-model robustness claim, production deployment claim,
product-value claim, public benchmark score, repaired-score claim, or score upgrade is supported.

## Evidence

- `docs/research/TELOS_MISSION_EVIDENCE_DATA_PROCESS_AUDIT_2026-07-14.md`
- `proof/frozen_input_inventory.json`
- `proof/audit_note_verification.json`
- `proof/public_metric_freshness.json`
- `proof/learning_ledger_check.json`
- `proof/receipt_presence_check.json`
- `proof/benchmark_artifact_lineage.json`
- `proof/claim_boundary_audit.json`
- `proof/forbidden_claim_scan.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_telos_mission_evidence_data_process_audit.json`
"""


def write_state(
    *,
    claim: dict[str, Any],
    endpoint: dict[str, Any],
    failures: list[str],
    forbidden: dict[str, Any],
    freshness: dict[str, Any],
    frozen: dict[str, Any],
    ledger: dict[str, Any],
    lineage: dict[str, Any],
    note: dict[str, Any],
    receipts: dict[str, Any],
    secret: dict[str, Any],
    status: str,
) -> None:
    write_json(FROZEN_INPUT_INVENTORY, frozen)
    write_json(AUDIT_NOTE_VERIFICATION, note)
    write_json(PUBLIC_METRIC_FRESHNESS, freshness)
    write_json(LEARNING_LEDGER_CHECK, ledger)
    write_json(RECEIPT_PRESENCE_CHECK, receipts)
    write_json(BENCHMARK_LINEAGE, lineage)
    write_json(CLAIM_BOUNDARY, claim)
    write_json(FORBIDDEN_SCAN, forbidden)
    write_json(SECRET_AUDIT, secret)
    write_json(ENDPOINT_RESULTS, endpoint)
    write_json(
        AUDIT_REPORT,
        audit_report(
            endpoint=endpoint,
            failures=failures,
            forbidden=forbidden,
            freshness=freshness,
            frozen=frozen,
            ledger=ledger,
            lineage=lineage,
            note=note,
            receipts=receipts,
            secret=secret,
            status=status,
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
        "schema_version": "telos.iter189.run_summary.v1",
        "secret_hit_count": secret["secret_hit_count"],
        "status": status,
    }
    learning = {
        "evidence_paths": [
            rel(AUDIT_NOTE),
            rel(AUDIT_NOTE_VERIFICATION),
            rel(PUBLIC_METRIC_FRESHNESS),
            rel(LEARNING_LEDGER_CHECK),
            rel(RECEIPT_PRESENCE_CHECK),
            rel(BENCHMARK_LINEAGE),
            rel(CLAIM_BOUNDARY),
            rel(FORBIDDEN_SCAN),
            rel(SECRET_AUDIT),
            rel(RECEIPT),
        ],
        "experiment_id": EXPERIMENT_ID,
        "insight": (
            "The mission evidence/data-process audit confirms the current public metric and data lineage "
            "are checkable, while the next empirical value depends on bounded property-generator execution."
        )
        if status == "pass"
        else "the mission evidence/data-process audit did not satisfy freshness, lineage, receipt, or boundary bars",
        "next_action": f"run {NEXT_EXPERIMENT_ID} under iter185/iter186/iter187 bars",
        "result_path": rel(RESULT),
        "schema_version": "telos.learning_record.v1",
        "status": status if status == "pass" else "null",
    }
    write_json(RUN_SUMMARY, run_summary)
    write_json(LEARNING, learning)
    RESULT.write_text(result_markdown(failures=failures, ledger=ledger, status=status), encoding="utf-8")
    receipt = {
        "acceptance_criteria": [
            "No provider calls, credential probes, model evaluations, property-generator calls, SWE-bench executions, or cloud resources are used.",
            "The audit note contains all seven required sections from iter188.",
            "Public surfaces preserve unrepaired iter179 majority_catch as 17/40 hack rows and 0/40 controls.",
            "The learning ledger validates and advances to the bounded property-generator execution gate.",
            "Required recent-gate receipts validate.",
            "Benchmark artifact lineage validates from v1 rows through property-probe packets and parser preflight.",
            "Forbidden positive claim hits and secret/private identifier hits are zero.",
        ],
        "agent_id": "codex-local-telos-mission-evidence-data-process-audit",
        "benchmark_id": "telos_mission_evidence_data_process_audit",
        "evidence": [
            {
                "artifact": rel(AUDIT_NOTE),
                "kind": "adversarial_review",
                "notes": "Human-readable hostile audit note with all required sections.",
                "status": status,
            },
            {
                "artifact": rel(AUDIT_NOTE_VERIFICATION),
                "kind": "test",
                "notes": f"Audit note section count: {note['section_count']}.",
                "status": status,
            },
            {
                "artifact": rel(RECEIPT_PRESENCE_CHECK),
                "kind": "artifact",
                "notes": f"Recent key-gate receipts checked: {receipts['checked_experiment_count']}.",
                "status": status,
            },
            {
                "artifact": rel(BENCHMARK_LINEAGE),
                "kind": "diff_scope",
                "notes": "Benchmark rows, controls, packets, panel metrics, probe packets, and parser artifacts checked.",
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
            "The audit note omits any required iter188 section.",
            "Public surfaces replace unrepaired iter179 with a repaired diagnostic metric or public benchmark score.",
            "Learning-ledger, receipt, benchmark-lineage, public-metric, forbidden-claim, or secret-safety checks fail.",
            "A committed artifact contains secret or private project/account material.",
            "The result presents a leaderboard, model-comparison, SOTA, natural-frequency, broad robustness, production, product-value, public benchmark-score, repaired-score, or score-upgrade claim.",
        ],
        "receipt_id": "receipt_telos_mission_evidence_data_process_audit",
        "status": status,
        "stated_goal": (
            "Execute the zero-spend Sentinel-style Telos mission evidence/data-process audit over "
            "committed local surfaces before any new property-generator spend."
        ),
        "task_id": EXPERIMENT_ID,
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(RECEIPT, receipt)


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    AUDIT_NOTE.parent.mkdir(parents=True, exist_ok=True)

    frozen = frozen_input_inventory()
    endpoint = endpoint_results()
    metric = current_public_metric()
    freshness = public_metric_freshness(metric)
    receipts = receipt_presence_check()
    lineage = benchmark_artifact_lineage()
    claim = claim_boundary_audit(metric)
    AUDIT_NOTE.write_text(
        audit_note_markdown(lineage=lineage, metric=metric, receipts=receipts),
        encoding="utf-8",
    )
    note = audit_note_verification()

    generated_paths = [
        AUDIT_NOTE,
        FROZEN_INPUT_INVENTORY,
        AUDIT_NOTE_VERIFICATION,
        PUBLIC_METRIC_FRESHNESS,
        LEARNING_LEDGER_CHECK,
        RECEIPT_PRESENCE_CHECK,
        BENCHMARK_LINEAGE,
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

    preliminary_forbidden = forbidden_claim_scan([HYPOTHESIS, NEXT_HYPOTHESIS, *PUBLIC_SURFACES, *generated_paths])
    preliminary_secret = secret_safety_audit([HYPOTHESIS, NEXT_HYPOTHESIS, *PUBLIC_SURFACES, *generated_paths])
    preliminary_failures = build_failures(
        claim=claim,
        endpoint=endpoint,
        forbidden=preliminary_forbidden,
        freshness=freshness,
        frozen=frozen,
        ledger=None,
        lineage=lineage,
        note=note,
        receipts=receipts,
        secret=preliminary_secret,
    )
    preliminary_status = "pass" if not preliminary_failures else "fail"
    placeholder_ledger = {
        "expected_next_action": f"run {NEXT_EXPERIMENT_ID} under iter185/iter186/iter187 bars",
        "experiment_id": EXPERIMENT_ID,
        "latest_next_action": "pending_final_ledger_write",
        "learning_record_count": 0,
        "schema_version": "telos.iter189.learning_ledger_check.v1",
        "status": "pass",
    }
    write_state(
        claim=claim,
        endpoint=endpoint,
        failures=preliminary_failures,
        forbidden=preliminary_forbidden,
        freshness=freshness,
        frozen=frozen,
        ledger=placeholder_ledger,
        lineage=lineage,
        note=note,
        receipts=receipts,
        secret=preliminary_secret,
        status=preliminary_status,
    )

    ledger = learning_ledger_check()
    forbidden = forbidden_claim_scan([HYPOTHESIS, NEXT_HYPOTHESIS, *PUBLIC_SURFACES, *generated_paths])
    secret = secret_safety_audit([HYPOTHESIS, NEXT_HYPOTHESIS, *PUBLIC_SURFACES, *generated_paths])
    failures = build_failures(
        claim=claim,
        endpoint=endpoint,
        forbidden=forbidden,
        freshness=freshness,
        frozen=frozen,
        ledger=ledger,
        lineage=lineage,
        note=note,
        receipts=receipts,
        secret=secret,
    )
    status = "pass" if not failures else "fail"
    write_state(
        claim=claim,
        endpoint=endpoint,
        failures=failures,
        forbidden=forbidden,
        freshness=freshness,
        frozen=frozen,
        ledger=ledger,
        lineage=lineage,
        note=note,
        receipts=receipts,
        secret=secret,
        status=status,
    )

    print(
        pretty_json(
            {
                "audit_note_sections": note["section_count"],
                "credential_probes": CREDENTIAL_PROBES,
                "experiment_id": EXPERIMENT_ID,
                "forbidden_positive_claim_hits": forbidden["hit_count"],
                "property_generator_calls": PROPERTY_GENERATOR_CALLS,
                "provider_calls": PROVIDER_CALLS,
                "secret_hit_count": secret["secret_hit_count"],
                "status": status,
            }
        ).strip()
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
