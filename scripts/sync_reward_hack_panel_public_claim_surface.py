#!/usr/bin/env python3
"""Audit iter183 public claim surfaces against the adjudicated repair boundary."""

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
EXPERIMENT_ID = "iter183_reward_hack_panel_public_claim_surface_sync"
NEXT_EXPERIMENT_ID = "iter184_reward_hack_panel_frontier_research_alignment_design"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
HYPOTHESIS = EXPERIMENT / "HYPOTHESIS.md"
NEXT_HYPOTHESIS = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"

ITER182 = ROOT / "experiments" / "iter182_reward_hack_panel_repair_execution_adjudication"
ITER182_RESULT = ITER182 / "RESULT.md"
ITER182_CLAIM = ITER182 / "proof" / "claim_boundary_decision.json"

PUBLIC_SURFACES = [
    ROOT / "README.md",
    ROOT / "docs" / "REPORT.md",
    ROOT / "docs" / "MISSION_LOOP.md",
    ROOT / "CONTINUITY.md",
    ROOT / "HANDOFF.md",
    ROOT / "mission" / "loop.json",
]
PAPER_BOUNDARY_SURFACES = [
    ROOT / "docs" / "PAPER.md",
    ROOT / "paper" / "README.md",
    ROOT / "paper" / "telos.tex",
]

PUBLIC_CLAIM_AUDIT = PROOF / "public_claim_surface_audit.json"
ACTIVE_GATE_AUDIT = PROOF / "active_gate_synchronization_audit.json"
FORBIDDEN_SCAN = PROOF / "forbidden_claim_scan.json"
SECRET_AUDIT = PROOF / "secret_safety_audit.json"
ENDPOINT_RESULTS = PROOF / "endpoint_results.json"
NEXT_RECOMMENDATION = PROOF / "next_gate_recommendation.json"
AUDIT_REPORT = PROOF / "audit_report.json"
RUN_SUMMARY = PROOF / "run_summary.json"
LEARNING = PROOF / "learning_record.json"
RECEIPT = VALID / "receipt_reward_hack_panel_public_claim_surface_sync.json"

NEXT_GATE = f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md"
PRIMARY_RULE = "majority_catch"
PROVIDER_CALLS = 0
CREDENTIAL_PROBES = 0
MODEL_EVALUATIONS = 0
NEW_SWEBENCH_EXECUTIONS = 0
NEW_CLOUD_RESOURCES = 0

README_NO_CLAIM_SUBSTRING = (
    "No leaderboard, public benchmark score, model-comparison result, precision result"
)

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
]

SECRET_PATTERNS = [
    ("google_oauth_token", re.compile(r"ya29\.[A-Za-z0-9._-]+")),
    ("bearer_token", re.compile(r"Bearer\s+(?!\[REDACTED_BEARER_TOKEN\])[A-Za-z0-9._~+/=-]+")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{18,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9._-]{18,}\b")),
    ("gcp_project_path", re.compile(r"projects/[A-Za-z][A-Za-z0-9-]{3,}")),
    ("gcp_project_url", re.compile(r"/projects/[A-Za-z][A-Za-z0-9-]{3,}/")),
    ("numeric_account_id", re.compile(r"\b[0-9]{12}\b")),
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(payload), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit(f"expected JSON object: {rel(path)}")
    return loaded


def surface_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def primary_metric_ok(text: str) -> bool:
    lowered = text.lower()
    return (
        "iter179" in lowered
        and "17/40" in text
        and "0/40" in text
        and ("majority_catch" in text or "majority-catch" in lowered)
        and ("primary" in lowered or "unrepaired" in lowered)
    )


def diagnostic_boundary_ok(text: str) -> bool:
    lowered = text.lower()
    iter181_ok = "iter181" not in lowered or "diagnostic" in lowered
    iter182_ok = "iter182" not in lowered or "adjudicat" in lowered
    repaired_ok = "repaired public score" not in lowered
    return iter181_ok and iter182_ok and repaired_ok


def public_claim_surface_audit(claim: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    expected_primary = claim["primary_public_metric"]
    for path in PUBLIC_SURFACES:
        text = surface_text(path)
        checks = {
            "contains_iter179_primary_metric": primary_metric_ok(text),
            "iter181_iter182_repair_boundary_is_diagnostic": diagnostic_boundary_ok(text),
            "contains_majority_catch": "majority_catch" in text
            or "majority-catch" in text.lower(),
            "contains_hack_primary_count": f"{expected_primary['hack_catches']}/"
            f"{expected_primary['hack_rows']}" in text,
            "contains_control_primary_count": f"{expected_primary['control_catches']}/"
            f"{expected_primary['control_rows']}" in text,
        }
        if path.name == "README.md":
            checks["readme_preserves_exact_no_claim_substring"] = (
                README_NO_CLAIM_SUBSTRING in text
            )
        failed = [name for name, ok in checks.items() if not ok]
        failures.extend(f"{rel(path)}:{name}" for name in failed)
        rows.append(
            {
                "checks": checks,
                "path": rel(path),
                "sha256": sha256_text(text),
                "status": "pass" if not failed else "fail",
            }
        )
    return {
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "primary_public_metric": expected_primary,
        "rows": rows,
        "schema_version": "telos.iter183.public_claim_surface_audit.v1",
        "status": "pass" if not failures else "fail",
    }


def active_gate_synchronization_audit() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []

    text_expectations = {
        ROOT / "README.md": NEXT_GATE,
        ROOT / "CONTINUITY.md": f"- `{NEXT_GATE}`",
        ROOT / "HANDOFF.md": f"Active gate: `{NEXT_GATE}`",
        ROOT / "docs" / "MISSION_LOOP.md": f"../{NEXT_GATE}",
    }
    for path, expected in text_expectations.items():
        text = surface_text(path)
        ok = expected in text
        if not ok:
            failures.append(f"{rel(path)}:missing_next_gate_reference")
        rows.append(
            {
                "expected": expected,
                "path": rel(path),
                "status": "pass" if ok else "fail",
            }
        )

    loop = read_json(ROOT / "mission" / "loop.json")
    loop_gate = loop.get("active_gate")
    loop_ok = loop_gate == NEXT_GATE
    if not loop_ok:
        failures.append("mission/loop.json:active_gate_not_next_gate")
    rows.append(
        {
            "actual": loop_gate,
            "expected": NEXT_GATE,
            "path": "mission/loop.json",
            "status": "pass" if loop_ok else "fail",
        }
    )

    next_exists = NEXT_HYPOTHESIS.exists()
    if not next_exists:
        failures.append(f"{rel(NEXT_HYPOTHESIS)}:missing_next_hypothesis")
    return {
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "next_gate": NEXT_GATE,
        "next_hypothesis_exists": next_exists,
        "rows": rows,
        "schema_version": "telos.iter183.active_gate_synchronization_audit.v1",
        "status": "pass" if not failures else "fail",
    }


def forbidden_claim_scan() -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    paths = [*PUBLIC_SURFACES, *PAPER_BOUNDARY_SURFACES, RESULT, HYPOTHESIS, NEXT_HYPOTHESIS]
    for path in sorted({path for path in paths if path.exists() and path.is_file()}):
        text = surface_text(path)
        for name, pattern in FORBIDDEN_POSITIVE_PATTERNS:
            for match in pattern.finditer(text):
                if local_negation_before_match(text, match.start()):
                    continue
                context = " ".join(match.group(0).split())
                hits.append(
                    {
                        "context": context[:180],
                        "path": rel(path),
                        "pattern": name,
                    }
                )
    return {
        "experiment_id": EXPERIMENT_ID,
        "hit_count": len(hits),
        "hits": hits,
        "patterns": [name for name, _pattern in FORBIDDEN_POSITIVE_PATTERNS],
        "schema_version": "telos.iter183.forbidden_claim_scan.v1",
        "status": "pass" if not hits else "fail",
    }


def local_negation_before_match(text: str, start: int) -> bool:
    prefix = text[max(0, start - 500) : start].lower()
    sentence_prefix = re.split(r"[.!?]", prefix)[-1]
    return bool(
        re.search(
            r"\b(no|not|none|without|cannot|never|does not|do not|did not)\b",
            sentence_prefix,
        )
    )


def secret_safety_audit(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    scanned = 0
    for path in sorted({path for path in paths if path.exists() and path.is_file()}):
        if path == SECRET_AUDIT:
            continue
        scanned += 1
        text = surface_text(path)
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
        "schema_version": "telos.iter183.secret_safety_audit.v1",
        "scanned_artifact_count": scanned,
        "secret_hit_count": len(hits),
        "status": "pass" if not hits else "fail",
    }


def endpoint_results() -> dict[str, Any]:
    return {
        "credential_probes": CREDENTIAL_PROBES,
        "endpoint_calls": [],
        "estimated_provider_spend_usd": "0.00",
        "experiment_id": EXPERIMENT_ID,
        "model_evaluations": MODEL_EVALUATIONS,
        "new_cloud_resources": NEW_CLOUD_RESOURCES,
        "new_swebench_executions": NEW_SWEBENCH_EXECUTIONS,
        "provider_calls": PROVIDER_CALLS,
        "schema_version": "telos.iter183.endpoint_results.v1",
        "status": "pass",
    }


def next_gate_recommendation(status: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "next_gate": NEXT_GATE,
        "recommendation": (
            "Run iter184 as a public-source frontier-research alignment design before any "
            "new paid evaluator expansion."
            if status == "pass"
            else "Fix public claim surfaces before adding literature or evaluator scope."
        ),
        "schema_version": "telos.iter183.next_gate_recommendation.v1",
        "status": status,
    }


def audit_report(
    *,
    active_gate_audit: dict[str, Any],
    endpoint: dict[str, Any],
    forbidden_scan: dict[str, Any],
    public_audit: dict[str, Any],
    secret_audit: dict[str, Any],
    status: str,
    failures: list[str],
) -> dict[str, Any]:
    return {
        "bars": {
            "active_gate_references_point_to_next_pre_registered_gate": (
                active_gate_audit["status"] == "pass"
            ),
            "broad_robustness_claimed": False,
            "credential_probes": endpoint["credential_probes"],
            "forbidden_positive_claim_hits": forbidden_scan["hit_count"],
            "leaderboard_claimed": False,
            "model_evaluations": endpoint["model_evaluations"],
            "model_superiority_claimed": False,
            "natural_frequency_claimed": False,
            "new_cloud_resources": endpoint["new_cloud_resources"],
            "new_swebench_executions": endpoint["new_swebench_executions"],
            "primary_public_metric_identified_on_public_surfaces": public_audit[
                "status"
            ]
            == "pass",
            "provider_calls": endpoint["provider_calls"],
            "public_benchmark_score_claimed": False,
            "repaired_score_claimed": False,
            "secret_hit_count": secret_audit["secret_hit_count"],
            "sota_claimed": False,
        },
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "schema_version": "telos.iter183.audit_report.v1",
        "status": status,
    }


def result_markdown(
    *,
    active_gate_audit: dict[str, Any],
    failures: list[str],
    forbidden_scan: dict[str, Any],
    public_audit: dict[str, Any],
    secret_audit: dict[str, Any],
    status: str,
) -> str:
    failure_text = "\n".join(f"- `{failure}`" for failure in failures) or "- none"
    primary = public_audit["primary_public_metric"]
    return f"""# Iteration 183 Result - Reward-Hack Panel Public Claim Surface Sync

Status: `{status}`.

## What this gate did

This zero-spend gate audited the public claim surfaces after iter182. It made no provider calls, no
credential probes, no model evaluations, no SWE-bench executions, and no cloud-resource changes.

## Synchronized Boundary

- Primary public metric: unrepaired iter179 `{primary['rule_id']}`.
- Hack rows caught: `{primary['hack_catches']}` of `{primary['hack_rows']}`.
- Control rows caught: `{primary['control_catches']}` of `{primary['control_rows']}`.
- Iter181/iter182 status: bounded repair diagnostic and zero-spend adjudication only.
- Active next gate: `{NEXT_GATE}`.

## Audit Counts

- Public surfaces audited: `{len(public_audit['rows'])}`.
- Active-gate references audited: `{len(active_gate_audit['rows'])}`.
- Forbidden positive-claim hits: `{forbidden_scan['hit_count']}`.
- Secret/project/account hits: `{secret_audit['secret_hit_count']}`.

Failures / blockers:

{failure_text}

Recommended next gate: `{NEXT_GATE}`.

## Not Supported

No leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate, broad
reward-model robustness claim, production deployment claim, model-superiority claim, public benchmark
score, repaired-score claim, or claim outside committed iter175-iter183 proof packets is supported.

## Evidence

- `proof/public_claim_surface_audit.json`
- `proof/active_gate_synchronization_audit.json`
- `proof/forbidden_claim_scan.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_public_claim_surface_sync.json`
"""


def build_failures(
    *,
    active_gate_audit: dict[str, Any],
    claim: dict[str, Any],
    endpoint: dict[str, Any],
    forbidden_scan: dict[str, Any],
    public_audit: dict[str, Any],
    secret_audit: dict[str, Any] | None,
) -> list[str]:
    failures: list[str] = []
    if endpoint["provider_calls"] != 0:
        failures.append("provider_calls_not_zero")
    if endpoint["credential_probes"] != 0:
        failures.append("credential_probes_not_zero")
    forbidden_claim_flags = [
        "benchmark_score_claim_supported",
        "broad_robustness_claim_supported",
        "leaderboard_claim_supported",
        "model_comparison_claim_supported",
        "model_superiority_claim_supported",
        "natural_frequency_claim_supported",
        "repaired_score_claim_supported",
        "sota_claim_supported",
    ]
    for flag in forbidden_claim_flags:
        if claim.get(flag) is not False:
            failures.append(f"iter182_claim_boundary_not_false:{flag}")
    if public_audit["status"] != "pass":
        failures.extend(public_audit["failures"])
    if active_gate_audit["status"] != "pass":
        failures.extend(active_gate_audit["failures"])
    if forbidden_scan["status"] != "pass":
        failures.append("forbidden_positive_claim_scan_hits")
    if secret_audit is not None and secret_audit["status"] != "pass":
        failures.append("secret_safety_audit_failed")
    return failures


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    claim = read_json(ITER182_CLAIM)
    endpoint = endpoint_results()
    public_audit = public_claim_surface_audit(claim)
    active_audit = active_gate_synchronization_audit()
    forbidden = forbidden_claim_scan()
    preliminary_failures = build_failures(
        active_gate_audit=active_audit,
        claim=claim,
        endpoint=endpoint,
        forbidden_scan=forbidden,
        public_audit=public_audit,
        secret_audit=None,
    )
    preliminary_status = "pass" if not preliminary_failures else "fail"
    placeholder_secret = {
        "secret_hit_count": 0,
        "status": "pass",
    }

    write_json(PUBLIC_CLAIM_AUDIT, public_audit)
    write_json(ACTIVE_GATE_AUDIT, active_audit)
    write_json(FORBIDDEN_SCAN, forbidden)
    write_json(ENDPOINT_RESULTS, endpoint)
    write_json(NEXT_RECOMMENDATION, next_gate_recommendation(preliminary_status))
    RESULT.write_text(
        result_markdown(
            active_gate_audit=active_audit,
            failures=preliminary_failures,
            forbidden_scan=forbidden,
            public_audit=public_audit,
            secret_audit=placeholder_secret,
            status=preliminary_status,
        ),
        encoding="utf-8",
    )

    generated_paths = [
        PUBLIC_CLAIM_AUDIT,
        ACTIVE_GATE_AUDIT,
        FORBIDDEN_SCAN,
        ENDPOINT_RESULTS,
        NEXT_RECOMMENDATION,
        AUDIT_REPORT,
        RUN_SUMMARY,
        LEARNING,
        RECEIPT,
        RESULT,
    ]
    secret = secret_safety_audit(
        [
            HYPOTHESIS,
            ITER182_RESULT,
            ITER182_CLAIM,
            NEXT_HYPOTHESIS,
            *PUBLIC_SURFACES,
            *PAPER_BOUNDARY_SURFACES,
            *generated_paths,
        ]
    )
    failures = build_failures(
        active_gate_audit=active_audit,
        claim=claim,
        endpoint=endpoint,
        forbidden_scan=forbidden,
        public_audit=public_audit,
        secret_audit=secret,
    )
    status = "pass" if not failures else "fail"

    write_json(SECRET_AUDIT, secret)
    write_json(NEXT_RECOMMENDATION, next_gate_recommendation(status))
    write_json(
        AUDIT_REPORT,
        audit_report(
            active_gate_audit=active_audit,
            endpoint=endpoint,
            failures=failures,
            forbidden_scan=forbidden,
            public_audit=public_audit,
            secret_audit=secret,
            status=status,
        ),
    )
    run_summary = {
        "credential_probes": CREDENTIAL_PROBES,
        "experiment_id": EXPERIMENT_ID,
        "failures": failures,
        "generated_at_utc": now_utc(),
        "new_cloud_resources": NEW_CLOUD_RESOURCES,
        "new_swebench_executions": NEW_SWEBENCH_EXECUTIONS,
        "provider_calls": PROVIDER_CALLS,
        "public_surface_count": len(public_audit["rows"]),
        "recommended_next_gate": NEXT_GATE,
        "schema_version": "telos.iter183.run_summary.v1",
        "secret_hit_count": secret["secret_hit_count"],
        "status": status,
    }
    learning = {
        "evidence_paths": [
            rel(PUBLIC_CLAIM_AUDIT),
            rel(ACTIVE_GATE_AUDIT),
            rel(FORBIDDEN_SCAN),
            rel(SECRET_AUDIT),
            rel(ENDPOINT_RESULTS),
            rel(AUDIT_REPORT),
            rel(RECEIPT),
        ],
        "experiment_id": EXPERIMENT_ID,
        "insight": (
            "public claim surfaces can carry the iter181/iter182 repair evidence as diagnostic "
            "only while preserving iter179 unrepaired majority-catch as the primary public metric"
        )
        if status == "pass"
        else "the public claim-surface sync did not satisfy its evidence bars",
        "next_action": f"run {NEXT_EXPERIMENT_ID} before any paid evaluator expansion",
        "result_path": rel(RESULT),
        "schema_version": "telos.learning_record.v1",
        "status": status if status == "pass" else "null",
    }
    write_json(RUN_SUMMARY, run_summary)
    write_json(LEARNING, learning)
    RESULT.write_text(
        result_markdown(
            active_gate_audit=active_audit,
            failures=failures,
            forbidden_scan=forbidden,
            public_audit=public_audit,
            secret_audit=secret,
            status=status,
        ),
        encoding="utf-8",
    )

    receipt = {
        "acceptance_criteria": [
            "No provider calls, credential probes, model evaluations, SWE-bench executions, or cloud resources are used.",
            "Every current public claim surface identifies unrepaired iter179 majority-catch as the primary panel metric.",
            "Iter181 and iter182 repair evidence remains diagnostic/adjudication evidence only.",
            "Active gate references point to the next pre-registered gate.",
            "No forbidden positive leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, public benchmark-score, or repaired-score claim is made.",
            "No audited artifact contains secrets or private project/account identifiers.",
        ],
        "agent_id": "codex-zero-spend-public-claim-surface-sync",
        "benchmark_id": "reward_hack_benchmark_v1",
        "evidence": [
            {"artifact": rel(PUBLIC_CLAIM_AUDIT), "kind": "artifact", "status": status},
            {"artifact": rel(ACTIVE_GATE_AUDIT), "kind": "artifact", "status": status},
            {"artifact": rel(FORBIDDEN_SCAN), "kind": "adversarial_review", "status": status},
            {"artifact": rel(SECRET_AUDIT), "kind": "adversarial_review", "status": status},
            {"artifact": rel(AUDIT_REPORT), "kind": "artifact", "status": status},
        ],
        "falsifiers": [
            "The gate fails if any provider call, credential probe, model evaluation, SWE-bench execution, or cloud resource change occurs.",
            "The gate fails if a current public surface upgrades iter181/iter182 repair evidence into a public repaired score.",
            "The gate fails if an active-gate reference points to iter183 instead of the next pre-registered gate.",
            "The gate fails if a forbidden positive public benchmark, leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or repaired-score claim is found.",
            "The gate fails if an audited artifact contains secrets or private project/account identifiers.",
        ],
        "receipt_id": f"iter183-reward-hack-panel-public-claim-surface-sync-{status}",
        "stated_goal": (
            "Synchronize public claim surfaces to the iter182 adjudicated repair-diagnostic "
            "boundary while advancing the active gate."
        ),
        "status": status,
        "task_id": f"telos:{EXPERIMENT_ID}",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(RECEIPT, receipt)

    print(
        json.dumps(
            {
                "credential_probes": CREDENTIAL_PROBES,
                "experiment_id": EXPERIMENT_ID,
                "forbidden_positive_claim_hits": forbidden["hit_count"],
                "provider_calls": PROVIDER_CALLS,
                "secret_hit_count": secret["secret_hit_count"],
                "status": status,
            },
            sort_keys=True,
        )
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
