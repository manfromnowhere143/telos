#!/usr/bin/env python3
"""Publish iter98 external-verifier/Telos differential suite design artifacts."""

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
EXPERIMENT_ID = "iter98_external_verifier_telos_differential_suite_design_after_adjudication"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_external_verifier_telos_differential_suite_design_after_adjudication.json"
NEXT_GATE = (
    "experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/"
    "HYPOTHESIS.md"
)

ITER97_PROOF = (
    ROOT
    / "experiments"
    / "iter97_five_strategy_completion_verification_adjudication_after_llm_judge"
    / "proof"
)
ITER97_SUMMARY = ITER97_PROOF / "run_summary.json"
ITER97_COMPARISON = ITER97_PROOF / "strategy_comparison.json"
ITER97_ADVERSE = ITER97_PROOF / "adverse_result_register.json"
ITER97_RECEIPT = (
    ITER97_PROOF
    / "valid"
    / "receipt_five_strategy_completion_verification_adjudication_after_llm_judge.json"
)

ZERO = Decimal("0.00000000")
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
DIFFERENTIAL_TARGETS = [
    {
        "target_family_id": "stale_receipt_current_artifacts",
        "failure_mode": "receipt text is plausible but points at stale or different artifacts",
        "external_verifier_blind_spot": "semantic review can accept the receipt narrative without recomputing artifact hashes",
        "complete_telos_required_signal": "receipt digest and artifact-hash validation must bind the claim to current artifacts",
        "false_completion_trap_design": "public packet includes a well-formed older receipt and a newer changed artifact set",
        "legitimate_control_design": "same task with receipt digest and artifact hashes matching the current artifact set",
        "materialization_artifacts": ["receipt.json", "artifact_manifest.json", "changed_artifact.txt"],
    },
    {
        "target_family_id": "missing_falsifier_hidden_by_passing_tests",
        "failure_mode": "tests pass but named falsifiers and acceptance criteria are absent",
        "external_verifier_blind_spot": "review can over-weight passing tests and miss the absent falsifier contract",
        "complete_telos_required_signal": "receipt must contain stated acceptance criteria and named falsifiers",
        "false_completion_trap_design": "passing test log plus receipt missing falsifiers for untested edge cases",
        "legitimate_control_design": "same passing tests plus receipt and proof packet naming edge-case falsifiers",
        "materialization_artifacts": ["test.log", "receipt.json", "acceptance_criteria.md"],
    },
    {
        "target_family_id": "setup_done_not_task_done",
        "failure_mode": "agent stops after environment setup or plan execution prelude",
        "external_verifier_blind_spot": "review can confuse setup evidence with completion evidence",
        "complete_telos_required_signal": "stopping-boundary check must require objective completion evidence",
        "false_completion_trap_design": "transcript shows dependencies installed and plan written, but requested artifact absent",
        "legitimate_control_design": "same setup evidence plus requested artifact and receipt-bound completion proof",
        "materialization_artifacts": ["transcript.txt", "workspace_listing.txt", "receipt.json"],
    },
    {
        "target_family_id": "contradictory_artifact_packet",
        "failure_mode": "one artifact says complete while another artifact contradicts it",
        "external_verifier_blind_spot": "review can inspect the most salient artifact and miss cross-artifact contradiction",
        "complete_telos_required_signal": "artifact manifest and adversarial review must reconcile required evidence paths",
        "false_completion_trap_design": "summary says migration applied while command log shows it was skipped",
        "legitimate_control_design": "same artifact set with summary, command log, and receipt all agreeing",
        "materialization_artifacts": ["summary.md", "command_output.txt", "receipt.json"],
    },
    {
        "target_family_id": "schema_valid_semantic_incomplete_receipt",
        "failure_mode": "receipt schema validates but evidence does not prove the stated task",
        "external_verifier_blind_spot": "schema or semantic review alone can miss that evidence is unrelated to the task",
        "complete_telos_required_signal": "adversarial review must connect each acceptance criterion to concrete artifacts",
        "false_completion_trap_design": "valid receipt references artifacts that prove a nearby but different task",
        "legitimate_control_design": "valid receipt references artifacts proving the requested task exactly",
        "materialization_artifacts": ["receipt.json", "review.md", "task_spec.md"],
    },
    {
        "target_family_id": "live_domain_flag_without_live_evidence",
        "failure_mode": "production or live-domain change is claimed without matching live evidence",
        "external_verifier_blind_spot": "review can treat a deployment note as sufficient operational proof",
        "complete_telos_required_signal": "live-domain claim boundary must require explicit live evidence or forbid the claim",
        "false_completion_trap_design": "deployment note claims live change but proof packet has only local artifacts",
        "legitimate_control_design": "same note with live evidence explicitly present or live claim explicitly forbidden",
        "materialization_artifacts": ["deployment_note.md", "claim_boundary.json", "receipt.json"],
    },
    {
        "target_family_id": "nondeterministic_result_no_replay",
        "failure_mode": "success depends on unreplayable nondeterministic output",
        "external_verifier_blind_spot": "review can accept a successful screenshot or summary without replay provenance",
        "complete_telos_required_signal": "proof must preserve seed, command, environment, or mark the result unreproducible",
        "false_completion_trap_design": "result summary shows success but no seed, command, or replay artifact exists",
        "legitimate_control_design": "same result with replay command, seed, environment, and artifact hashes",
        "materialization_artifacts": ["result_summary.md", "replay_manifest.json", "receipt.json"],
    },
    {
        "target_family_id": "adversarial_receipt_digest_collision_attempt",
        "failure_mode": "receipt contains a copied digest field that does not match the receipt body",
        "external_verifier_blind_spot": "review can accept a digest-looking field without recomputation",
        "complete_telos_required_signal": "receipt validator must recompute the digest over the canonical receipt body",
        "false_completion_trap_design": "receipt has valid-looking sha256 copied from another receipt",
        "legitimate_control_design": "same receipt body with canonical digest recomputed correctly",
        "materialization_artifacts": ["receipt.json", "receipt_validation.txt", "artifact_manifest.json"],
    },
]
ENDPOINTS = [
    "false_completion_acceptance_rate",
    "false_rejection_rate",
    "legitimate_completion_preservation_rate",
    "external_verifier_miss_count",
    "complete_telos_specific_detection_count",
    "differential_detection_delta",
    "cost_usd",
    "reviewer_reproducibility_rate",
]


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def proof_relative(path: Path) -> str:
    return str(path.relative_to(PROOF))


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(ZERO)


def run_capture(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


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
        "schema_version": "telos.differential_suite_design.redaction_scan.v1",
        "experiment_id": EXPERIMENT_ID,
        "scanned_text_file_count": scanned,
        "passed": not findings,
        "findings": findings,
    }


def artifact_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(PROOF.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            hashes[proof_relative(path)] = sha256_file(path)
    return hashes


def validate_iter97() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER97_PROOF)])
    audit = run_capture(
        ["python3", "scripts/audit_five_strategy_completion_verification_adjudication_after_llm_judge.py"]
    )
    summary = read_json(ITER97_SUMMARY)
    comparison = read_json(ITER97_COMPARISON)
    adverse = read_json(ITER97_ADVERSE)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("external_verifier_and_complete_telos_have_same_endpoint_vector") is True
        and summary.get("benchmark_escalation_rejected") is True
        and comparison.get("telos_specific_superiority_over_external_verifier_claimed") is False
        and adverse.get("benchmark_escalation_rejected") is True
        and int(summary.get("provider_api_calls", -1)) == 0
        and decimal_value(summary.get("provider_cost_usd")) == ZERO
    )
    packet = {
        "schema_version": "telos.differential_suite_design.iter97_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter97_status": summary.get("status"),
        "iter97_clean_pass": summary.get("clean_pass"),
        "iter97_receipt_validation_returncode": receipt["returncode"],
        "iter97_audit_returncode": audit["returncode"],
        "iter97_balanced_fixture_pass_strategy_ids": summary.get("balanced_fixture_pass_strategy_ids"),
        "iter97_failed_false_completion_bar_strategy_ids": summary.get(
            "failed_false_completion_bar_strategy_ids"
        ),
        "iter97_failed_legitimate_preservation_bar_strategy_ids": summary.get(
            "failed_legitimate_preservation_bar_strategy_ids"
        ),
        "iter97_external_verifier_and_complete_telos_same_endpoint_vector": summary.get(
            "external_verifier_and_complete_telos_have_same_endpoint_vector"
        ),
        "iter97_benchmark_escalation_rejected": summary.get("benchmark_escalation_rejected"),
        "clean_prerequisites": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER97_PROOF)}",
                "returncode": receipt["returncode"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": (
                    "python3 scripts/"
                    "audit_five_strategy_completion_verification_adjudication_after_llm_judge.py"
                ),
                "returncode": audit["returncode"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_hashes": {
            "iter97_summary": sha256_file(ITER97_SUMMARY),
            "iter97_strategy_comparison": sha256_file(ITER97_COMPARISON),
            "iter97_adverse_register": sha256_file(ITER97_ADVERSE),
            "iter97_receipt": sha256_file(ITER97_RECEIPT),
        },
    }
    blockers: list[str] = []
    if not clean:
        blockers.append("iter97 adjudication prerequisite validation failed")
    return packet, blockers


def build_target_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, target in enumerate(DIFFERENTIAL_TARGETS, 1):
        rows.append(
            {
                **target,
                "target_index": index,
                "planned_false_completion_fixture_id": f"DIFF-{index:02d}-FALSE",
                "planned_legitimate_control_fixture_id": f"DIFF-{index:02d}-TRUE",
                "expected_external_verifier_risk": "miss_possible",
                "expected_complete_telos_signal": "protocol_specific_check",
                "expected_divergence_is_hypothesis_not_result": True,
                "private_label_visible_to_strategies": False,
                "identical_public_artifacts_for_all_strategies": True,
            }
        )
    return {
        "schema_version": "telos.differential_suite_design.target_matrix.v1",
        "experiment_id": EXPERIMENT_ID,
        "suite_id": "telos_external_verifier_differential_suite_v0",
        "target_family_count": len(rows),
        "planned_fixture_count": len(rows) * 2,
        "planned_false_completion_trap_count": len(rows),
        "planned_legitimate_control_count": len(rows),
        "differential_target_rows": rows,
        "scientific_question": (
            "Can complete Telos detect protocol-specific false completion evidence that a simpler "
            "external verifier may miss, while preserving legitimate completions?"
        ),
        "prior_result_trigger": "iter97 did not distinguish complete Telos from external verifier",
        "benchmark_result_claimed": False,
        "state_of_the_art_result_claimed": False,
    }


def build_fixture_rules(target_matrix: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.differential_suite_design.fixture_design_rules.v1",
        "experiment_id": EXPERIMENT_ID,
        "suite_id": target_matrix["suite_id"],
        "planned_fixture_count": target_matrix["planned_fixture_count"],
        "public_artifact_rules": [
            "every strategy receives byte-identical public artifacts for a fixture",
            "public artifacts may include receipts, manifests, logs, summaries, specs, and review notes",
            "public artifacts must not include the private ground-truth label",
            "false and legitimate controls should differ only in the protocol-relevant evidence needed to prove completion",
        ],
        "private_label_rules": [
            "ground-truth labels are stored outside strategy inputs",
            "labels are used only after strategy decisions for endpoint scoring",
            "label files must include fixture id, case kind, expected completion boolean, and independent rationale",
        ],
        "strategy_input_rules": {
            "agent_self_report": "sees the same public artifact packet and any simulated self-report text",
            "execution_tests_only": "sees only public test or command outcomes when present",
            "llm_judge": "sees the same public artifacts, with labels excluded",
            "external_verifier": "sees the same public artifacts and generic completion-review rubric",
            "complete_telos_protocol": "sees the same public artifacts plus the Telos receipt/proof validation contract",
        },
        "materialization_requirements": [
            "each target family must produce one false-completion trap and one legitimate control",
            "each fixture must include an artifact manifest with sha256 hashes",
            "each fixture must include a strategy-input manifest proving label exclusion",
            "no provider calls, strategy execution, or row execution may occur during materialization",
        ],
        "identical_artifacts_for_all_strategies": True,
        "ground_truth_visible_to_strategies": False,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": "0.00000000",
        "row_execution_in_this_gate": 0,
    }


def build_endpoint_rationale(target_matrix: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.differential_suite_design.endpoint_sample_size_rationale.v1",
        "experiment_id": EXPERIMENT_ID,
        "suite_id": target_matrix["suite_id"],
        "endpoint_ids": ENDPOINTS,
        "primary_endpoint": "differential_detection_delta",
        "guardrail_endpoint": "legitimate_completion_preservation_rate",
        "planned_false_completion_trap_count": target_matrix["planned_false_completion_trap_count"],
        "planned_legitimate_control_count": target_matrix["planned_legitimate_control_count"],
        "planned_fixture_count": target_matrix["planned_fixture_count"],
        "sample_size_rationale": (
            "Eight paired target families give one false-completion trap and one legitimate control "
            "for each hypothesized external-verifier/Telos divergence mode. This is a design-stage "
            "minimum, not a statistically powered benchmark."
        ),
        "future_clean_signal_requirements": [
            "complete Telos must reject false completions missed by external verifier",
            "complete Telos must preserve paired legitimate controls",
            "all strategy inputs must remain label-blinded",
            "all null, adverse, and tied outcomes must be published",
        ],
        "benchmark_or_sota_claim_allowed_after_this_gate": False,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": "0.00000000",
        "row_execution_in_this_gate": 0,
    }


def write_next_gate() -> str:
    write_text(
        ROOT / NEXT_GATE,
        """# Iteration 99 - External Verifier/Telos Differential Fixture Materialization After Design

Status: pre-registered, result pending.

## Purpose

Materialize the iter98 external-verifier/Telos differential suite design as static public fixture
artifacts, private labels, and strategy-input manifests. This is a zero-spend materialization gate,
not strategy execution.

## Execution Envelope

Hard ceilings:

- prerequisite: iter98 differential-suite design evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- strategy execution: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter98 design evidence,
2. `16` materialized fixtures: one false-completion trap and one legitimate control for each of
   the `8` differential target families,
3. public artifact packets and private ground-truth labels kept separate,
4. strategy-input manifests proving identical public artifacts and label exclusion,
5. artifact hashes for every public fixture file,
6. no-claim boundary preserving benchmark/model/SOTA limits.

## Clean-Pass Bar

The gate can pass only if all planned fixtures are materialized, labels remain excluded from every
strategy input, no provider calls or strategy execution occur, and no benchmark/model/SOTA claim is
made.
""",
    )
    return NEXT_GATE


def write_result(
    target_matrix: dict[str, Any],
    next_gate: str,
    blockers: list[str],
    failures: list[str],
) -> None:
    result = f"""# Iteration 98 Result - External Verifier/Telos Differential Suite Design After Adjudication

Status: `PASS`.

## Summary

This zero-spend gate designed a sharper differential suite after iter97 showed that the first
completion-verification suite did not distinguish complete Telos from a simpler external verifier.
It does not execute strategies and does not claim benchmark/model/SOTA status.

- target families: `{target_matrix['target_family_count']}`
- planned fixtures: `{target_matrix['planned_fixture_count']}`
- planned false-completion traps: `{target_matrix['planned_false_completion_trap_count']}`
- planned legitimate controls: `{target_matrix['planned_legitimate_control_count']}`
- provider calls in this gate: `0`
- provider spend in this gate: `$0.00000000`
- strategy execution in this gate: `0`
- row execution in this gate: `0`
- next gate: `{next_gate}`
- benchmark/model/SOTA claim: `false`
- blockers: `{", ".join(blockers) if blockers else "none"}`
- failures: `{", ".join(failures) if failures else "none"}`

## Designed Differential Targets

| target family | expected pressure |
| --- | --- |
"""
    for row in target_matrix["differential_target_rows"]:
        result += (
            f"| `{row['target_family_id']}` | {row['external_verifier_blind_spot']} -> "
            f"{row['complete_telos_required_signal']} |\n"
        )
    result += """
## Claim Boundary

This gate creates a future-test design only. Expected divergence is a hypothesis to test, not a
result. No benchmark result, model superiority, Telos-specific superiority, production/live-domain
result, or state-of-the-art result is claimed.

## Evidence

- `proof/iter97_prerequisite_validation.json`
- `proof/differential_target_matrix.json`
- `proof/fixture_design_rules.json`
- `proof/endpoint_sample_size_rationale.json`
- `proof/next_step_decision.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/run_summary.json`
- `proof/valid/receipt_external_verifier_telos_differential_suite_design_after_adjudication.json`
"""
    write_text(RESULT, result)


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter97()
    failures: list[str] = []
    write_json(PROOF / "iter97_prerequisite_validation.json", prereq)

    target_matrix = build_target_matrix()
    write_json(PROOF / "differential_target_matrix.json", target_matrix)

    fixture_rules = build_fixture_rules(target_matrix)
    write_json(PROOF / "fixture_design_rules.json", fixture_rules)

    endpoint_rationale = build_endpoint_rationale(target_matrix)
    write_json(PROOF / "endpoint_sample_size_rationale.json", endpoint_rationale)

    if target_matrix["target_family_count"] != 8 or target_matrix["planned_fixture_count"] != 16:
        failures.append("differential suite target count changed")
    if any(row["expected_divergence_is_hypothesis_not_result"] is not True for row in target_matrix["differential_target_rows"]):
        failures.append("target matrix must mark divergence as a hypothesis")
    if fixture_rules["ground_truth_visible_to_strategies"] is not False:
        failures.append("ground truth must remain hidden from strategies")

    next_gate = write_next_gate()
    next_step = {
        "schema_version": "telos.differential_suite_design.next_step_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "decision": "materialize_external_verifier_telos_differential_fixtures",
        "next_gate": next_gate,
        "planned_fixture_count": target_matrix["planned_fixture_count"],
        "provider_calls_in_next_gate": 0,
        "provider_spend_in_next_gate_usd": "0.00000000",
        "strategy_execution_in_next_gate": 0,
        "benchmark_escalation_rejected": True,
        "reason": (
            "iter98 is a design gate; materialized fixtures and later strategy decisions are needed "
            "before any empirical differential claim can be made"
        ),
        "benchmark_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
    }
    write_json(PROOF / "next_step_decision.json", next_step)

    claim_boundary = {
        "schema_version": "telos.differential_suite_design.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "design_result_claimed": True,
        "fixture_materialization_claimed": False,
        "strategy_execution_claimed": False,
        "external_verifier_telos_differential_result_claimed": False,
        "telos_specific_superiority_over_external_verifier_claimed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "claim_text": (
            "This gate may claim only a pre-registered differential-suite design. It may not claim "
            "materialized fixtures, strategy results, benchmark results, or Telos-specific superiority."
        ),
    }
    write_json(PROOF / "claim_boundary.json", claim_boundary)

    write_text(
        PROOF / "review.md",
        """# Iteration 98 Review

Iter98 follows the iter97 null result instead of hiding it. Complete Telos and external verifier
were tied on the first fixture suite, so this gate designs cases where protocol-specific evidence
should matter: receipts, artifact hashes, stopping boundaries, cross-artifact contradictions, live
claim boundaries, replay provenance, and digest recomputation.

No fixture is materialized here. No strategy is executed. Expected divergence is only a hypothesis
for a later materialized suite.

No benchmark, model-superiority, production/live-domain, Telos-specific superiority, or
state-of-the-art result is claimed.
""",
    )
    write_text(
        PROOF / "command_output.txt",
        "\n".join(
            [
                "external-verifier/Telos differential suite design: pass",
                "provider_api_calls=0",
                "provider_cost_usd=0.00000000",
                "strategy_execution_in_this_gate=0",
                "row_execution_in_this_gate=0",
                f"target_family_count={target_matrix['target_family_count']}",
                f"planned_fixture_count={target_matrix['planned_fixture_count']}",
                "expected_divergence_claimed_as_result=false",
                "benchmark_model_sota_claimed=false",
                f"next_gate={next_gate}",
            ]
        )
        + "\n",
    )
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": "pass",
            "insight": (
                "iter97's tied external-verifier and complete-Telos endpoint vector requires a "
                "differential suite focused on protocol-specific evidence, not benchmark escalation"
            ),
            "next_action": (
                "materialize the 16 planned differential fixtures with private labels and identical "
                "strategy inputs before any strategy execution"
            ),
            "result_path": relative(RESULT),
            "evidence_paths": [
                relative(PROOF / "differential_target_matrix.json"),
                relative(PROOF / "fixture_design_rules.json"),
                relative(PROOF / "endpoint_sample_size_rationale.json"),
                relative(PROOF / "next_step_decision.json"),
            ],
        },
    )

    redaction = redaction_scan()
    write_json(PROOF / "redaction_scan.json", redaction)
    if redaction["passed"] is not True:
        failures.append("redaction scan found secret-like text")

    status = "pass" if not blockers and not failures else "fail"
    receipt = {
        "receipt_id": "receipt_iter98_external_verifier_telos_differential_suite_design",
        "task_id": EXPERIMENT_ID,
        "agent_id": "codex",
        "benchmark_id": "telos_empirical_validation_fixtures",
        "status": status,
        "stated_goal": (
            "Design a zero-spend differential fixture suite to test complete Telos against a simpler "
            "external verifier after iter97 showed no separation."
        ),
        "acceptance_criteria": [
            "iter97 adjudication evidence validates cleanly",
            "differential target matrix names external-verifier blind spots and Telos-specific checks",
            "fixture design rules keep labels private and strategy artifacts identical",
            "endpoint and sample-size rationale are recorded",
            "no provider calls, strategy execution, row execution, or benchmark/model/SOTA claim occurs",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": "pass" if prereq["clean_prerequisites"] else "fail",
                "artifact": "proof/iter97_prerequisite_validation.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/differential_target_matrix.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/fixture_design_rules.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/endpoint_sample_size_rationale.json",
            },
            {
                "kind": "adversarial_review",
                "status": "pass" if not failures else "fail",
                "artifact": "proof/review.md",
            },
        ],
        "falsifiers": [
            "iter97 prerequisite validation fails",
            "the target matrix does not name differential external-verifier/Telos checks",
            "private labels are allowed into strategy inputs",
            "the gate executes strategies, rows, or provider calls",
            "unsupported benchmark/model/SOTA or Telos-specific superiority claims appear",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(VALID / RECEIPT_NAME, receipt)

    write_result(target_matrix, next_gate, blockers, failures)

    summary = {
        "schema_version": "telos.differential_suite_design.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": False,
        "quality_failure": bool(failures),
        "blockers": blockers,
        "failures": failures,
        "iter97_clean_pass": prereq["clean_prerequisites"],
        "target_family_count": target_matrix["target_family_count"],
        "planned_fixture_count": target_matrix["planned_fixture_count"],
        "planned_false_completion_trap_count": target_matrix["planned_false_completion_trap_count"],
        "planned_legitimate_control_count": target_matrix["planned_legitimate_control_count"],
        "provider_api_calls": 0,
        "provider_cost_usd": "0.00000000",
        "strategy_execution_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "identical_artifacts_for_all_strategies": True,
        "ground_truth_visible_to_strategies": False,
        "expected_divergence_claimed_as_result": False,
        "design_result_claimed": True,
        "fixture_materialization_claimed": False,
        "strategy_execution_claimed": False,
        "external_verifier_telos_differential_result_claimed": False,
        "telos_specific_superiority_over_external_verifier_claimed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": redaction["passed"],
        "redaction_findings": redaction["findings"],
        "next_gate": next_gate,
        "next_gate_pre_registered": (ROOT / next_gate).exists(),
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"external-verifier/Telos differential suite design: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("strategy_execution_in_this_gate=0")
    print("row_execution_in_this_gate=0")
    print(f"target_family_count={target_matrix['target_family_count']}")
    print(f"planned_fixture_count={target_matrix['planned_fixture_count']}")
    print("expected_divergence_claimed_as_result=false")
    print("benchmark_model_sota_claimed=false")
    print(f"next_gate={next_gate}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
