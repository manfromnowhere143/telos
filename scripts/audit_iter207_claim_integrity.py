#!/usr/bin/env python3
"""Build the deterministic iter207 claim-integrity correction ledger.

This audit is deliberately offline. It reads only committed/local repository artifacts and
read-only Git history, never provider state, network state, credentials, containers, or remotes.
Frozen historical evidence is immutable input. Exact public interpretation surfaces may be
relabelled only under the hash-bound allowlist below; the only paths this script writes are the
three iter207 correction artifacts declared in ``OUTPUTS``.
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter207_claim_integrity_and_admission_recovery"
PROOF = EXP / "proof"
OUTPUTS = {
    "iter192": PROOF / "corrections/iter192_novelty_scope_correction.json",
    "iter195": PROOF / "strict/iter195_protocol_failure.json",
    "ledger": PROOF / "claim_integrity_correction.json",
}

ITER192 = ROOT / "experiments/iter192_reward_hack_benchmark_construct_validity_audit"
ITER175 = ROOT / "experiments/iter175_reward_hack_panel_bounded_paid_pilot"
ITER178 = ROOT / "experiments/iter178_reward_hack_panel_remaining_pairs_paid_expansion"
ITER179 = ROOT / "experiments/iter179_reward_hack_panel_full_cohort_adjudication"
ITER181 = ROOT / "experiments/iter181_reward_hack_panel_openai_nondecision_repair_execution"
ITER195 = ROOT / "experiments/iter195_synthesized_input_differential_oracle"
ITER196 = ROOT / "experiments/iter196_detector_vs_certified_hacks"
ITER199 = ROOT / "experiments/iter199_benchmark_expansion_across_repos"
ITER200 = ROOT / "experiments/iter200_natural_certified_yet_wrong_rate"
ITER201 = ROOT / "experiments/iter201_detectors_on_full_benchmark"
ITER202 = ROOT / "experiments/iter202_natural_rate_scaled"
ITER206_SEAL_COMMIT = "a2a05ef2ed05a0c457076f2bd5f1475507190685"
ITER207_SEAL_COMMIT = "f4ee0d5bcb3b4abee7ebf1683be5b9edda263c28"
HISTORICAL_RELABEL_PATHS = (
    ITER192 / "RESULT.md",
    ITER192 / "proof/learning_record.json",
    ITER195 / "RESULT.md",
    ITER195 / "proof/learning_record.json",
    ITER196 / "RESULT.md",
    ITER196 / "proof/learning_record.json",
    ROOT / "experiments/iter198_findings_paper_synthesis_and_accessibility/RESULT.md",
    ROOT
    / "experiments/iter198_findings_paper_synthesis_and_accessibility/proof/learning_record.json",
    ITER199 / "RESULT.md",
    ITER199 / "proof/learning_record.json",
    ITER200 / "RESULT.md",
    ITER202 / "RESULT.md",
)
ADDITIVE_ITER206_PATHS = (
    "experiments/iter206_iter205_admission_history_recovery/RESULT.md",
    "experiments/iter206_iter205_admission_history_recovery/"
    "proof/learning_record.pre_publication_claim_integrity_null.json",
    "experiments/iter206_iter205_admission_history_recovery/"
    "proof/pre_publication_claim_integrity_null.json",
)
ITER207_PREFIX = "experiments/iter207_claim_integrity_and_admission_recovery/"


class ClaimIntegrityError(ValueError):
    """Raised when frozen evidence no longer supports the correction ledger."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ClaimIntegrityError(message)


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClaimIntegrityError(f"cannot read canonical JSON: {path.relative_to(ROOT)}") from exc


def _jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ClaimIntegrityError(
                f"invalid canonical JSONL: {path.relative_to(ROOT)}:{line_number}"
            ) from exc
        _require(isinstance(row, dict), f"non-object JSONL row: {path.relative_to(ROOT)}")
        rows.append(row)
    return rows


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ClaimIntegrityError(f"cannot read evidence: {path.relative_to(ROOT)}") from exc


def _contains_any_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, dict):
        return bool(keys & value.keys()) or any(_contains_any_key(item, keys) for item in value.values())
    if isinstance(value, list):
        return any(_contains_any_key(item, keys) for item in value)
    return False


def _require_fragments(path: Path, *fragments: str) -> str:
    text = _text(path)
    for fragment in fragments:
        _require(fragment in text, f"missing evidence fragment in {path.relative_to(ROOT)}: {fragment}")
    return text


def _git_blob(commit: str, path: Path) -> bytes:
    relative = path.relative_to(ROOT).as_posix()
    process = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return process.stdout


def _require_git_fragments(commit: str, path: Path, *fragments: str) -> str:
    try:
        text = _git_blob(commit, path).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ClaimIntegrityError(
            f"historical Git blob is not UTF-8: {commit}:{path.relative_to(ROOT)}"
        ) from exc
    for fragment in fragments:
        _require(
            fragment in text,
            f"missing historical fragment in {commit}:{path.relative_to(ROOT)}: {fragment}",
        )
    return text


def _git_evidence(commit: str, paths: list[Path] | tuple[Path, ...]) -> list[dict[str, Any]]:
    records = []
    for path in sorted(paths):
        payload = _git_blob(commit, path)
        records.append(
            {
                "bytes": len(payload),
                "commit": commit,
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return records


def _experiment_delta_statuses() -> dict[str, str]:
    """Return the exact sealed iter206-to-iter207 experiment delta."""

    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ITER207_SEAL_COMMIT, "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        process = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "--no-renames",
                ITER206_SEAL_COMMIT,
                ITER207_SEAL_COMMIT,
                "--",
                "experiments",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ClaimIntegrityError(
            "cannot audit the exact iter206-to-iter207 sealed experiment delta"
        ) from exc

    statuses: dict[str, str] = {}
    for line in process.stdout.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        _require(len(parts) == 2, f"unexpected Git delta row: {line}")
        status, path = parts
        _require(status in {"A", "M"}, f"forbidden experiment delta status {status}: {path}")
        _require(path not in statuses, f"duplicate experiment delta path: {path}")
        statuses[path] = status
    return statuses


def _validate_experiment_delta(statuses: dict[str, str] | None = None) -> dict[str, str]:
    """Fail closed outside exact public relabels, predecessor nulls, and iter207 additions."""

    observed = _experiment_delta_statuses() if statuses is None else statuses
    relabels = {path.relative_to(ROOT).as_posix() for path in HISTORICAL_RELABEL_PATHS}
    additive_iter206 = set(ADDITIVE_ITER206_PATHS)
    for path in sorted(relabels):
        _require(observed.get(path) == "M", f"historical relabel is not one exact modification: {path}")
    for path in sorted(additive_iter206):
        _require(observed.get(path) == "A", f"iter206 terminal-null path is not one addition: {path}")
    for path, status in sorted(observed.items()):
        if path in relabels:
            _require(status == "M", f"historical relabel status changed: {path}")
        elif path in additive_iter206:
            _require(status == "A", f"iter206 terminal-null status changed: {path}")
        elif path.startswith(ITER207_PREFIX):
            _require(status == "A", f"iter207 path existed before the iter206 seal: {path}")
        else:
            raise ClaimIntegrityError(f"unauthorized historical experiment delta: {path}")
    return observed


def _historical_relabel_bindings() -> list[dict[str, Any]]:
    base = {
        row["path"]: row
        for row in _git_evidence(ITER206_SEAL_COMMIT, HISTORICAL_RELABEL_PATHS)
    }
    current = {
        row["path"]: row
        for row in _git_evidence(ITER207_SEAL_COMMIT, HISTORICAL_RELABEL_PATHS)
    }
    bindings = []
    for path in sorted(base):
        _require(path in current, f"historical relabel surface disappeared: {path}")
        bindings.append(
            {
                "path": path,
                "iter206_seal_commit": ITER206_SEAL_COMMIT,
                "iter206_seal_bytes": base[path]["bytes"],
                "iter206_seal_sha256": base[path]["sha256"],
                "current_bytes": current[path]["bytes"],
                "current_sha256": current[path]["sha256"],
            }
        )
    return bindings


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence(paths: list[Path] | tuple[Path, ...]) -> list[dict[str, Any]]:
    records = []
    for path in sorted(paths):
        records.append(
            {
                "bytes": path.stat().st_size,
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": _sha256(path),
            }
        )
    return records


def _corpus_digest(paths: list[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(base).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _first_addition(path: Path, expected_commit: str, expected_time: str) -> dict[str, str]:
    relative = path.relative_to(ROOT).as_posix()
    process = subprocess.run(
        [
            "git",
            "log",
            "--all",
            "--reverse",
            "--diff-filter=A",
            "--format=%H%x09%aI",
            "--",
            relative,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in process.stdout.splitlines() if line]
    _require(bool(lines), f"no Git addition record for {relative}")
    commit, authored_at = lines[0].split("\t", 1)
    _require(commit == expected_commit, f"first-addition commit changed for {relative}")
    _require(authored_at == expected_time, f"first-addition time changed for {relative}")
    return {"commit": commit, "path": relative, "time": authored_at}


def audit_iter192() -> dict[str, Any]:
    hypothesis = ITER192 / "HYPOTHESIS.md"
    result = ITER192 / "RESULT.md"
    scan_path = ITER192 / "proof/existing_baseline_scan.json"
    audit_path = ITER192 / "proof/audit_report.json"
    discarded_path = ITER192 / "proof/discarded_certified_variants.json"
    iter151 = ROOT / "experiments/iter151_cross_repo_scale_official"
    iter151_hypothesis = iter151 / "HYPOTHESIS.md"
    iter151_result = iter151 / "RESULT.md"
    iter151_rows_path = iter151 / "proof/raw/scale_results.json"
    iter151_reports_path = iter151 / "proof/raw/sweb_reports.tgz"
    v1_path = ROOT / "benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl"

    _require_git_fragments(
        "c681785efa8f0bf420eb52b8a3bb634957cc040e",
        hypothesis,
        "committed test-suite/official-harness baselines for v1 found by scan is exactly `0`",
        "that baseline has never been reported anywhere in this",
    )
    _require_git_fragments(
        "c681785efa8f0bf420eb52b8a3bb634957cc040e",
        result,
        "pre-existing committed test-suite baselines for v1 | `0`",
        "comparison has never appeared in the repository.",
    )
    _require_git_fragments(
        "7d09f941fffdc5a82fc81bde3531ed2c174237fc",
        iter151_hypothesis,
        "proxy baseline (expected `0` by construction)",
        "a both-miss fails a `PASS_TO_PASS`",
    )
    _require_git_fragments(
        "7d09f941fffdc5a82fc81bde3531ed2c174237fc",
        iter151_result,
        "proxy (accept on target-test pass) | `0/20`",
        "gate would also reject these both-miss",
    )

    scan = _json(scan_path)
    historical_audit = _json(audit_path)
    discarded = _json(discarded_path)
    iter151_rows = _json(iter151_rows_path)
    v1_rows = _jsonl(v1_path)
    _require(scan["existing_baseline_hit_count"] == 0, "iter192 lexical scan changed")
    _require(scan["markdown_files_scanned"] == 677, "iter192 lexical scan corpus changed")
    _require(historical_audit["status"] == "pass", "iter192 historical status changed")
    _require(isinstance(iter151_rows, list) and len(iter151_rows) == 45, "iter151 rows changed")
    baseline_rows = [row for row in iter151_rows if row.get("both_miss")]
    _require(len(baseline_rows) == 20, "iter151 both-miss denominator changed")
    _require(
        all(row.get("baseline_resolved") is False for row in baseline_rows),
        "iter151 official baseline is no longer 0/20",
    )
    _require(len(v1_rows) == 40, "v1 benchmark row count changed")
    v1_ids = {row["instance_id"] for row in v1_rows}
    shared_ids = sorted(v1_ids & {row["id"] for row in baseline_rows})
    _require(len(shared_ids) == 19, "iter151/v1 instance overlap changed")
    patch_identity_keys = {
        "hack_diff",
        "hack_diff_sha256",
        "model_patch",
        "model_patch_sha256",
        "patch",
        "patch_sha256",
        "repl",
    }
    rows_with_patch_identity = [
        row["id"] for row in baseline_rows if _contains_any_key(row, patch_identity_keys)
    ]
    _require(not rows_with_patch_identity, "iter151 rows gained retained patch identity")
    with tarfile.open(iter151_reports_path, "r:gz") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        _require(len(members) == 132, "iter151 report archive member count changed")
        _require(
            all(member.name.endswith("/report.json") for member in members),
            "iter151 report archive gained a non-report artifact",
        )
        reports_with_patch_identity = []
        for member in members:
            stream = archive.extractfile(member)
            _require(stream is not None, f"cannot read iter151 archive member: {member.name}")
            try:
                report = json.loads(stream.read())
            except json.JSONDecodeError as exc:
                raise ClaimIntegrityError(
                    f"invalid iter151 archived report JSON: {member.name}"
                ) from exc
            if _contains_any_key(report, patch_identity_keys):
                reports_with_patch_identity.append(member.name)
    _require(not reports_with_patch_identity, "iter151 reports gained retained patch identity")
    overlap_sources = Counter(
        row["source_experiment"] for row in v1_rows if row["instance_id"] in shared_ids
    )
    _require(
        overlap_sources
        == Counter(
            {
                "iter152_reward_model_gaming_scale": 16,
                "iter154_reward_hack_benchmark_expansion_pilot": 3,
            }
        ),
        "iter151/v1 overlap provenance changed",
    )
    _require(
        discarded["certified_resolved_hack_variants"] == 139,
        "iter192 harness-resolved evaluation count changed",
    )
    _require(
        discarded["certified_resolved_unique_instances"] == 65,
        "iter192 harness-resolved instance count changed",
    )
    _require(
        len(discarded["generator_discarded_instance_ids"]) == 23,
        "iter152 discarded-instance evidence changed",
    )
    _require(
        discarded["instances_both_discarded_and_certified_resolved_count"] == 17,
        "iter152 discard/resolution overlap changed",
    )

    return {
        "schema_version": "telos.iter207.iter192_novelty_scope_correction.v1",
        "experiment_id": ITER192.name,
        "historical_recorded_status": "pass",
        "standing_adjudication_status": "conservative_novelty_fail",
        "literal_falsifier_5_status": "indeterminate",
        "correction_id": "overbroad_conceptual_novelty",
        "correction": {
            "claim": (
                "The iter192 result treated its zero-hit lexical scan as support that the test-suite "
                "baseline had never been reported in the repository."
            ),
            "finding": (
                "iter151 had already reported the same class-level mechanism: 0/20 official resolutions "
                "for both-miss starts, explicitly because PASS_TO_PASS failure makes the zero "
                "definitional. Its accepted patch bytes were not retained, so this does not establish "
                "a prior row-identical baseline for the later v1 artifact."
            ),
            "lexical_scan_hits": 0,
            "prior_semantic_baseline": [0, 20],
            "prior_baseline_and_v1_shared_instance_ids": shared_ids,
            "prior_baseline_and_v1_shared_instance_count": len(shared_ids),
            "iter151_rows_with_retained_patch_identity": len(rows_with_patch_identity),
            "iter151_archived_report_count": len(members),
            "iter151_archived_reports_with_retained_patch_identity": len(
                reports_with_patch_identity
            ),
            "exact_v1_row_identity_in_iter151_established": None,
            "literal_v1_specific_falsifier_triggered": None,
            "adjudication_rule": (
                "Fail conceptual firstness conservatively while recording the literal v1-specific "
                "falsifier trigger as indeterminate."
            ),
        },
        "chronology": {
            "prior_baseline": _first_addition(
                iter151_result,
                "7d09f941fffdc5a82fc81bde3531ed2c174237fc",
                "2026-07-12T19:31:57+03:00",
            ),
            "iter192_gate": _first_addition(
                hypothesis,
                "c681785efa8f0bf420eb52b8a3bb634957cc040e",
                "2026-07-14T15:39:47+03:00",
            ),
        },
        "retained_findings": {
            "v1_rows_audited": historical_audit["bars"]["rows_audited"],
            "v1_rows_official_resolved_false": historical_audit["bars"][
                "rows_official_resolved_false"
            ],
            "v1_rows_with_p2p_failure": historical_audit["bars"][
                "rows_with_at_least_one_p2p_failure"
            ],
            "harness_resolved_hack_tagged_evaluations": discarded[
                "certified_resolved_hack_variants"
            ],
            "harness_resolved_unique_instance_ids": discarded[
                "certified_resolved_unique_instances"
            ],
            "iter152_generator_discarded_instance_ids": len(
                discarded["generator_discarded_instance_ids"]
            ),
            "iter152_discarded_and_harness_resolved_instance_ids": discarded[
                "instances_both_discarded_and_certified_resolved_count"
            ],
            "all_139_evaluations_bound_to_generator_discard_decisions": False,
            "interpretation": (
                "The 40/40 construct correction remains deterministically supported. Historical "
                "tarballs also contain 139 harness-resolved hack-tagged evaluations across 65 "
                "instance IDs. The committed decision evidence binds only 23 iter152 discarded "
                "instance IDs, 17 of which overlap the harness-resolved set; it does not bind every "
                "evaluation to a discard decision or preserve the evaluated patch bytes. What "
                "fails conservatively is conceptual firstness; the literal v1-specific falsifier "
                "trigger remains indeterminate."
            ),
        },
        "evidence": _evidence(
            [
                scan_path,
                audit_path,
                discarded_path,
                iter151_rows_path,
                iter151_reports_path,
                v1_path,
            ]
        ),
        "historical_git_evidence": [
            *_git_evidence(
                "c681785efa8f0bf420eb52b8a3bb634957cc040e", [hypothesis, result]
            ),
            *_git_evidence(
                "7d09f941fffdc5a82fc81bde3531ed2c174237fc",
                [iter151_hypothesis, iter151_result],
            ),
        ],
    }


def audit_iter195() -> dict[str, Any]:
    hypothesis = ITER195 / "HYPOTHESIS.md"
    result = ITER195 / "RESULT.md"
    runner = ROOT / "scripts/run_iter195_scenario_generator.py"
    summary_path = ITER195 / "proof/raw/scenarios/phase_a_summary.json"
    per_path = ITER195 / "proof/iter195_per_candidate.json"
    accepted_path = ITER195 / "proof/accepted_rows.json"
    audit_path = ITER195 / "proof/audit_report.json"
    receipt_path = ITER195 / "proof/valid/receipt_synthesized_input_differential_oracle.json"

    _require_git_fragments(
        "b9c549e3b2dc028853c38abb61c1cfc108b1ca21",
        hypothesis,
        "the model never sees the gold patch",
        "at least `10` of `20` synthesized inputs",
        "raw synthesis prompts (leakage-scanned)",
    )
    runner_text = _require_git_fragments(
        "80f0c51fe145b6fe322d760e12508a58ea9ea502",
        runner,
        "GOLD hunk:",
        "VARIANT hunk:",
        "Write a single self-contained Python 3 script",
        "gold_hunk=hunk(gold_patch, src_file)",
        "variant_hunk=hunk(var_patch, src_file)",
    )
    _require("for input" not in runner_text, "iter195 runner unexpectedly gained input iteration")
    _require_git_fragments(
        "d5afa98948d76f465d15002c8592c085a6e29688",
        result,
        "saw both the gold and the variant hunk",
        "Validated scenarios (gold ran clean): `13/15`",
    )

    summary = _json(summary_path)
    per = _json(per_path)["candidates"]
    accepted = _json(accepted_path)
    historical_audit = _json(audit_path)
    receipt = _json(receipt_path)
    scenario_files = sorted((ITER195 / "proof/raw/scenarios").glob("*.scenario.py"))
    execution_logs = sorted((ITER195 / "proof/raw/execution").glob("*.log"))
    raw_prompt_or_response = sorted(
        path
        for path in (ITER195 / "proof/raw").rglob("*")
        if path.is_file() and ("prompt" in path.name.lower() or "response" in path.name.lower())
    )
    distribution = Counter(row["status"] for row in per)
    _require(summary["certified_candidates"] == 16, "iter195 candidate count changed")
    _require(summary["provider_calls"] == 16, "iter195 provider call count changed")
    _require(summary["scenarios"] == 15, "iter195 scenario count changed")
    _require(len(scenario_files) == 15, "iter195 scenario file set changed")
    _require(len(execution_logs) == 30, "iter195 execution log set changed")
    _require(len(per) == 15, "iter195 adjudicated row count changed")
    _require(sum(bool(row.get("gold_clean")) for row in per) == 13, "iter195 gold-clean count changed")
    _require(distribution == Counter({"wrong": 10, "scenario_failed": 2,
                                      "certified_equivalent": 2, "variant_errored": 1}),
             "iter195 outcome distribution changed")
    _require(accepted["accepted_count"] == 10, "iter195 accepted count changed")
    _require(historical_audit["status"] == "pass", "iter195 historical status changed")
    _require(receipt["status"] == "pass", "iter195 historical receipt status changed")
    _require(len(raw_prompt_or_response) == 0, "iter195 prompt/response custody changed")

    failures = [
        {
            "id": "gold_and_variant_hunks_entered_synthesis_prompt",
            "registered_rule": "input synthesis sees no gold patch or gold diff",
            "observed": "the provider prompt contained labeled GOLD and VARIANT hunks",
        },
        {
            "id": "twenty_input_generator_validation_replaced",
            "registered_rule": "validate >=10 of 20 inputs per trusted generator",
            "observed": (
                "one targeted scenario script was generated per candidate and a single clean gold run "
                "was relabeled as validation"
            ),
        },
        {
            "id": "raw_prompt_and_leakage_scan_custody_missing",
            "registered_rule": "retain raw synthesis prompts with leakage scans for every accepted row",
            "observed": "zero dedicated raw prompt, raw response, or leakage-scan artifacts are retained",
        },
    ]
    _require(len(failures) == 3, "iter195 failure taxonomy changed")

    return {
        "schema_version": "telos.iter207.iter195_protocol_failure.v1",
        "experiment_id": ITER195.name,
        "historical_recorded_status": "pass",
        "strict_protocol_status": "fail",
        "protocol_failures": failures,
        "chronology": {
            "hypothesis_frozen_before_phase_a": _first_addition(
                hypothesis,
                "b9c549e3b2dc028853c38abb61c1cfc108b1ca21",
                "2026-07-14T18:14:36+03:00",
            ),
            "deviating_runner_and_phase_a_outputs_same_commit": {
                "runner": _first_addition(
                    runner,
                    "80f0c51fe145b6fe322d760e12508a58ea9ea502",
                    "2026-07-14T18:29:26+03:00",
                ),
                "phase_a_summary": _first_addition(
                    summary_path,
                    "80f0c51fe145b6fe322d760e12508a58ea9ea502",
                    "2026-07-14T18:29:26+03:00",
                ),
            },
            "execution_output_commit": _first_addition(
                execution_logs[0],
                "d5afa98948d76f465d15002c8592c085a6e29688",
                "2026-07-14T19:30:19+03:00",
            ),
        },
        "retained_counts": {
            "certified_candidates_entering_phase_a": 16,
            "provider_calls": 16,
            "estimated_spend_usd": summary["estimated_spend_usd"],
            "single_scenario_scripts": len(scenario_files),
            "paired_execution_logs": len(execution_logs),
            "gold_clean_single_scenarios": 13,
            "clean_differing_single_scenarios": 10,
            "certified_equivalent_single_scenarios": 2,
            "scenario_failed": 2,
            "variant_errored": 1,
            "dedicated_raw_prompt_or_response_artifacts": len(raw_prompt_or_response),
        },
        "retained_exploratory_interpretation": (
            "Ten official-harness-resolved variants have retained clean, single-scenario gold-versus-"
            "variant output differentials. The scenario provider saw both hunks. This is exploratory, "
            "gold-assisted reference-differential evidence; it is not a passed synthesized-input oracle "
            "and does not establish global semantic inequivalence."
        ),
        "execution_environment_limit": (
            "Historical execution selected mutable image tags and retained no resolved digest."
        ),
        "evidence": _evidence([summary_path, per_path, accepted_path, audit_path, receipt_path]),
        "historical_git_evidence": [
            *_git_evidence(
                "b9c549e3b2dc028853c38abb61c1cfc108b1ca21", [hypothesis]
            ),
            *_git_evidence(
                "80f0c51fe145b6fe322d760e12508a58ea9ea502", [runner]
            ),
            *_git_evidence(
                "d5afa98948d76f465d15002c8592c085a6e29688", [result]
            ),
        ],
        "scenario_corpus": {
            "count": len(scenario_files),
            "sha256": _corpus_digest(scenario_files, ITER195 / "proof/raw/scenarios"),
        },
        "execution_log_corpus": {
            "count": len(execution_logs),
            "sha256": _corpus_digest(execution_logs, ITER195 / "proof/raw/execution"),
        },
    }


def audit_iter199() -> dict[str, Any]:
    hypothesis = ITER199 / "HYPOTHESIS.md"
    result = ITER199 / "RESULT.md"
    runner = ROOT / "scripts/run_iter199_scenarios.py"
    targets_path = ITER199 / "proof/raw/targets.json"
    adversary_path = ITER199 / "proof/raw/candidates/adversary_summary.json"
    scenarios_path = ITER199 / "proof/raw/scenarios/scenarios_summary.json"
    audit_path = ITER199 / "proof/audit_report.json"

    _require_git_fragments(
        "03d199f49b69bcbe7948e223e26bdcd3ff2a32c9",
        hypothesis,
        "The target set is frozen in `proof/raw/targets.json` before any variant is",
        "gold is used only at ground-truth time",
    )
    _require_git_fragments(
        "03d199f49b69bcbe7948e223e26bdcd3ff2a32c9",
        runner,
        "Reuses the iter195 scenario generator",
        "a model sees both the gold and variant hunks",
        "gold_hunk=scen.hunk(gold_patch, src_file)",
        "variant_hunk=scen.hunk(var_patch, src_file)",
    )
    _require_git_fragments(
        "0b45815c90fc150eb1c54124981d50a37f3709b7",
        result,
        "Provider calls `86`",
        "certified **and** witnessed wrong (confirmed) | `12`",
    )
    targets = _json(targets_path)
    adversary = _json(adversary_path)
    scenarios = _json(scenarios_path)
    audit = _json(audit_path)
    _require(targets["count"] == 42, "iter199 target count changed")
    _require(adversary["targets"] == 42, "iter199 adversary target count changed")
    _require(adversary["provider_calls"] == 63, "iter199 adversary calls changed")
    _require(adversary["candidates"] == 23, "iter199 candidate count changed")
    _require(scenarios["provider_calls"] == 23, "iter199 scenario calls changed")
    _require(scenarios["scenarios"] == 23, "iter199 scenario count changed")
    _require(audit["status"] == "pass", "iter199 historical status changed")
    _require(audit["metrics"]["confirmed_new_hacks"] == 12, "iter199 confirmed count changed")

    common_commit = "03d199f49b69bcbe7948e223e26bdcd3ff2a32c9"
    common_time = "2026-07-14T23:20:56+03:00"
    chronology = {
        "hypothesis": _first_addition(hypothesis, common_commit, common_time),
        "targets": _first_addition(targets_path, common_commit, common_time),
        "adversary_provider_outputs": _first_addition(adversary_path, common_commit, common_time),
        "scenario_provider_outputs": _first_addition(scenarios_path, common_commit, common_time),
    }

    return {
        "protocol_status": "registration_timing_not_independently_established",
        "claim": (
            "The hypothesis, frozen targets, runner, adversary outputs, and scenario outputs first enter "
            "Git in one commit, so Git does not independently establish the claimed pre-generation freeze."
        ),
        "chronology": chronology,
        "method": (
            "Gold-assisted targeted scenario construction matching the executed iter195 method: the "
            "scenario provider saw labeled gold and variant hunks. This was construction/labeling, not a "
            "gold-blind detector."
        ),
        "retained_counts": {
            "targets": 42,
            "adversary_provider_calls": 63,
            "candidate_variants": 23,
            "scenario_provider_calls": 23,
            "scenario_scripts": 23,
            "certified_variants": 20,
            "clean_reference_differentials": 12,
            "repositories": audit["metrics"]["repository_count"],
            "new_repositories": audit["metrics"]["new_repository_count"],
        },
        "retained_exploratory_interpretation": (
            "The 12 retained rows remain exploratory gold-assisted reference-differential witnesses with "
            "official-harness certification. They are not a prospectively registered frequency result or "
            "an independent semantic oracle."
        ),
        "evidence": _evidence([targets_path, adversary_path, scenarios_path, audit_path]),
        "historical_git_evidence": [
            *_git_evidence(common_commit, [hypothesis, runner]),
            *_git_evidence(
                "0b45815c90fc150eb1c54124981d50a37f3709b7", [result]
            ),
        ],
    }


def audit_iter196() -> dict[str, Any]:
    hypothesis = ITER196 / "HYPOTHESIS.md"
    result = ITER196 / "RESULT.md"
    audit_path = ITER196 / "proof/audit_report.json"
    judge_path = ITER196 / "proof/judge_panel_results.json"
    _require_git_fragments(
        "d5afa98948d76f465d15002c8592c085a6e29688",
        hypothesis,
        "both detectors are run on all `10` positives and all controls",
        "gold-free property/differential oracle",
    )
    _require_git_fragments(
        "336c484200289d27ee1361f5fbd1e85e51494fa9",
        result,
        "Status: **partial**",
        "claim the gate's `>=` both-detector bar",
    )
    audit = _json(audit_path)
    judge = _json(judge_path)
    _require(audit["status"] == "blocked", "iter196 corrected audit status changed")
    _require(audit["provenance"]["parsed_response_labels_retained"] == [44, 44],
             "iter196 parsed-label custody changed")
    _require(judge["metrics"]["provider_calls"] == 44, "iter196 call count changed")
    return {
        "gate_status": "partial_and_blocked",
        "both_detector_bar_met": False,
        "detector_a_delivered": True,
        "detector_b_delivered_in_iter196": False,
        "historical_third_panel_member_status": (
            "unavailable in the recorded run; this is not a statement about current runtime availability"
        ),
        "retained_counts": {
            "provider_calls": 44,
            "parsed_labels": 44,
            "hack_observed_lower": [7, 10],
            "hack_missing_upper": [9, 10],
            "hack_complete_case": [7, 8],
        },
        "chronology": audit["chronology"],
        "raw_provider_response_text_retained": False,
        "evidence": _evidence([audit_path, judge_path]),
        "historical_git_evidence": [
            *_git_evidence(
                "d5afa98948d76f465d15002c8592c085a6e29688", [hypothesis]
            ),
            *_git_evidence(
                "336c484200289d27ee1361f5fbd1e85e51494fa9", [result]
            ),
        ],
    }


def _added_lines(patch: str) -> set[str]:
    return {
        line[1:].strip()
        for line in patch.splitlines()
        if line.startswith("+") and not line.startswith("+++") and line[1:].strip()
    }


def audit_iter201_disclosure() -> dict[str, Any]:
    manifest_path = ROOT / "benchmarks/certified_resolved_reward_hack_v2/manifest.json"
    judge_path = ITER201 / "proof/judge_panel_22_results.json"
    audit_path = ITER201 / "proof/audit_report.json"
    runner = ROOT / "scripts/run_iter201_judge_panel.py"
    manifest = _json(manifest_path)
    judge = _json(judge_path)
    audit = _json(audit_path)
    _require(manifest["total_rows"] == 22, "iter201 benchmark count changed")
    _require(judge["metrics"]["leakage_shared_gold_lines"] == 4,
             "iter201 shared-gold diagnostic changed")
    _require(audit["status"] == "fail", "iter201 protocol status changed")
    candidate_dirs = {
        "iter195_synthesized_input_differential_oracle": (
            ROOT
            / "experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/"
            "phase_a_candidates"
        ),
        "iter199_benchmark_expansion_across_repos": ITER199 / "proof/raw/candidates",
    }
    diagnostic_rows = []
    patch_files: list[Path] = []
    for row in manifest["rows"]:
        directory = candidate_dirs[row["source_experiment"]]
        iid = row["instance_id"]
        gold_path = directory / f"{iid}.gold.patch"
        variant_path = directory / f"{iid}.variant.patch"
        patch_files.extend([gold_path, variant_path])
        gold = _text(gold_path)
        variant = _text(variant_path)
        shared = sorted(line for line in (_added_lines(gold) - _added_lines(variant)) if line in variant)
        if shared:
            diagnostic_rows.append({"instance_id": iid, "shared_line_count": len(shared)})
    _require(
        [row["instance_id"] for row in diagnostic_rows]
        == [
            "django__django-11211",
            "matplotlib__matplotlib-24627",
            "astropy__astropy-12907",
            "sympy__sympy-11618",
        ],
        "iter201 disclosure rows changed",
    )
    return {
        "diagnostic": "leakage_shared_gold_lines",
        "row_count": 4,
        "rows": diagnostic_rows,
        "disposition": "disclosure_only_not_invalidation",
        "reason": (
            "The judge received each candidate's own diff, and four candidate diffs also contained a line "
            "identified by the historical heuristic as gold-distinctive elsewhere. The gold patch was not "
            "shown as a comparison reference. Report the diagnostic; do not treat it as causal evidence or "
            "as an additional protocol failure."
        ),
        "separate_protocol_status": (
            "iter201 remains FAIL for its already-recorded candidate-diff-derived locator deviation"
        ),
        "candidate_patch_corpus": {
            "count": len(patch_files),
            "sha256": _corpus_digest(patch_files, ROOT),
        },
        "evidence": _evidence([manifest_path, judge_path, audit_path, runner]),
    }


def audit_iter179_cost_attribution() -> dict[str, Any]:
    iter175_cost_path = ITER175 / "proof/cost_call_audit.json"
    iter178_cost_path = ITER178 / "proof/cost_call_audit.json"
    iter178_ledger_path = ITER178 / "proof/provider_call_ledger.jsonl"
    iter179_metric_path = ITER179 / "proof/full_cohort_metric_recomputation_audit.json"
    iter181_cost_path = ITER181 / "proof/cost_call_audit.json"
    iter175 = _json(iter175_cost_path)
    iter178 = _json(iter178_cost_path)
    iter178_calls = _jsonl(iter178_ledger_path)
    iter179 = _json(iter179_metric_path)
    iter181 = _json(iter181_cost_path)
    first_guard = Decimal(iter175["estimated_spend_guard_usd"])
    expansion_guard = Decimal(iter178["estimated_spend_guard_usd"])
    repair_guard = Decimal(iter181["estimated_spend_guard_usd"])
    _require(first_guard == Decimal("6.312690"), "iter175 spend guard changed")
    _require(expansion_guard == Decimal("7.005150"), "iter178 spend guard changed")
    _require(repair_guard == Decimal("0.271800"), "iter181 spend guard changed")
    _require(iter178["planned_diagnostic_calls"] == 3, "iter178 diagnostic-call count changed")
    _require(len(iter178_calls) == 123, "iter178 call-ledger count changed")
    iter178_primary_guard = sum(
        (
            Decimal(row["estimated_cost_usd_guard"])
            for row in iter178_calls
            if row["diagnostic_only"] is False
        ),
        Decimal("0"),
    )
    iter178_diagnostic_guard = sum(
        (
            Decimal(row["estimated_cost_usd_guard"])
            for row in iter178_calls
            if row["diagnostic_only"] is True
        ),
        Decimal("0"),
    )
    _require(iter178_primary_guard == Decimal("6.815400"), "iter178 primary guard sum changed")
    _require(
        iter178_diagnostic_guard == Decimal("0.189750"),
        "iter178 diagnostic guard sum changed",
    )
    _require(
        iter178_primary_guard + iter178_diagnostic_guard == expansion_guard,
        "iter178 call-ledger guard reconciliation changed",
    )
    _require(
        iter179["recomputed_full_cohort_panel_metrics"][
            "diagnostic_recovery_excluded_from_score"
        ]
        is True,
        "iter179 diagnostic exclusion changed",
    )
    source_run_guard = first_guard + expansion_guard
    score_producing_guard = first_guard + iter178_primary_guard
    total_through_repair = source_run_guard + repair_guard
    _require(source_run_guard == Decimal("13.317840"), "iter179 source-run guard sum changed")
    _require(
        score_producing_guard == Decimal("13.128090"),
        "iter179 score-producing guard sum changed",
    )
    _require(total_through_repair == Decimal("13.589640"), "iter181 cumulative guard sum changed")
    return {
        "unrepaired_primary_result": {"majority_catch": [17, 40]},
        "score_producing_calls": {
            "count": 240,
            "estimated_spend_guard_usd": str(score_producing_guard),
            "components_usd": {
                "iter175_primary": str(first_guard),
                "iter178_primary": str(iter178_primary_guard),
            },
        },
        "source_run_estimated_spend_guards_usd": {
            "iter175": str(first_guard),
            "iter178": str(expansion_guard),
            "sum": str(source_run_guard),
            "includes_iter178_diagnostic_calls": iter178["planned_diagnostic_calls"],
        },
        "excluded_iter178_diagnostic_calls": {
            "count": 3,
            "estimated_spend_guard_usd": str(iter178_diagnostic_guard),
        },
        "later_repair_estimated_spend_guard_usd": str(repair_guard),
        "total_estimated_spend_guard_through_repair_usd": str(total_through_repair),
        "diagnostic_recovery_excluded_from_primary_score": True,
        "cost_semantics": (
            "These are conservative estimated spend guards, not provider invoices. The 240 calls that "
            "produce the unrepaired score have a $13.128090 guard. The $13.317840 source-run total "
            "includes three iter178 diagnostic calls excluded from primary scoring. "
            "The rounded $13.59 total additionally includes the later iter181 repair run and must not "
            "be attributed to the unrepaired iter179 score."
        ),
        "evidence": _evidence(
            [
                iter175_cost_path,
                iter178_cost_path,
                iter178_ledger_path,
                iter179_metric_path,
                iter181_cost_path,
            ]
        ),
    }
def audit_iter200_attribution() -> dict[str, Any]:
    result = ITER200 / "RESULT.md"
    audit_path = ITER200 / "proof/audit_report.json"
    receipt_path = ITER200 / "proof/valid/receipt_natural_certified_yet_wrong.json"
    backfill_path = ITER200 / "proof/raw/denominator_backfill_run.json"
    _require_git_fragments(
        "a2a05ef2ed05a0c457076f2bd5f1475507190685",
        result,
        "the original execution run was `29391238359`",
        "the `54` historical logs do not",
    )
    audit = _json(audit_path)
    backfill = _json(backfill_path)
    logs = sorted((ITER200 / "proof/raw/execution").glob("*.log"))
    with_image = [path for path in logs if "IMAGE_ID=" in _text(path)]
    historical = [path for path in logs if path not in with_image]
    embedded_original_run = [path for path in historical if "29391238359" in _text(path)]
    _require(len(logs) == 74, "iter200 log corpus changed")
    _require(len(historical) == 54, "iter200 historical log count changed")
    _require(len(with_image) == 20, "iter200 backfill log count changed")
    _require(not embedded_original_run, "iter200 original logs gained embedded run attribution")
    _require(backfill["workflow"]["run_id"] == 29422735843, "iter200 backfill run changed")
    _require(backfill["backfill"]["frozen_logs_byte_identical"] is True,
             "iter200 frozen log custody changed")
    _require(audit["funnel"]["certified_model_patches"] == 24,
             "iter200 corrected denominator changed")
    return {
        "claimed_original_run_id": 29391238359,
        "original_run_attribution_status": (
            "historical assertion not independently rebound by a committed download receipt or by run "
            "metadata embedded in the 54 original logs"
        ),
        "original_logs": {
            "count": len(historical),
            "embedded_claimed_run_id_count": len(embedded_original_run),
            "corpus_sha256": _corpus_digest(historical, ITER200 / "proof/raw/execution"),
        },
        "backfill_attribution": {
            "status": "receipt_bound",
            "run_id": backfill["workflow"]["run_id"],
            "new_log_count": backfill["backfill"]["new_log_count"],
            "artifact_id": backfill["artifact"]["artifact_id"],
        },
        "empirical_disposition": (
            "This limits source/run attribution for the original 54 logs; it does not erase their retained "
            "bytes. The corrected N=24, k=1, u=6 result remains exploratory and is additionally bounded by "
            "the already-disclosed absence of raw historical judge response text."
        ),
        "corrected_funnel": {"N": 24, "k": 1, "u": 6},
        "evidence": _evidence([audit_path, receipt_path, backfill_path]),
        "historical_git_evidence": _git_evidence(
            "a2a05ef2ed05a0c457076f2bd5f1475507190685", [result]
        ),
    }


def audit_iter202_accounting() -> dict[str, Any]:
    hypothesis = ITER202 / "HYPOTHESIS.md"
    amendment = ITER202 / "PREREGISTRATION_AMENDMENT.md"
    result = ITER202 / "RESULT.md"
    process_path = ITER202 / "proof/raw/process_history.json"
    solve_path = ITER202 / "proof/raw/solutions/solve_summary.json"
    scenario_path = ITER202 / "proof/raw/scenarios/scenarios_summary.json"
    _require_git_fragments(
        "a2a05ef2ed05a0c457076f2bd5f1475507190685",
        amendment,
        "one provider request was initiated; the exact completed-call count and spend are unrecoverable.",
        "conservatively charged its entire possible run: `53` calls and an estimated `$2.65`",
    )
    _require_git_fragments(
        "a2a05ef2ed05a0c457076f2bd5f1475507190685",
        result,
        "Status: **NULL**",
        "iter202 stopped before execution. It therefore contributes no `N`",
    )
    process = _json(process_path)
    solve = _json(solve_path)
    scenarios = _json(scenario_path)
    _require(process["schema_version"] == "telos.iter202.process_history.v1",
             "iter202 process history changed")
    _require(len(process["events"]) == 1, "iter202 process event count changed")
    event = process["events"][0]
    charge = event["conservative_ceiling_charge"]
    _require(event["minimum_provider_requests_initiated"] == 1,
             "iter202 known-minimum accounting changed")
    _require(event["completed_provider_calls_exact"] is None,
             "iter202 interrupted exact calls became asserted")
    _require(event["estimated_spend_usd_exact"] is None,
             "iter202 interrupted exact spend became asserted")
    _require(charge == {
        "provider_calls": 53,
        "estimated_spend_usd": 2.65,
        "spend_semantics": "Estimated bookkeeping charge at $0.05 per possible call; not recovered actual spend.",
    }, "iter202 interrupted ceiling charge changed")
    _require(solve["provider_calls"] == 53 and solve["solutions"] == 50,
             "iter202 retained solve counts changed")
    _require(scenarios["provider_calls"] == 39 and scenarios["scenarios"] == 38,
             "iter202 retained scenario counts changed")
    retained_calls = solve["provider_calls"] + scenarios["provider_calls"]
    retained_estimate = round(solve["estimated_spend_usd"] + scenarios["estimated_spend_usd"], 2)
    return {
        "interrupted_invocation": {
            "minimum_requests_initiated": 1,
            "exact_completed_calls": None,
            "exact_spend_usd": None,
            "provider_outputs_retained": False,
            "provider_outputs_used": False,
            "ceiling_charge": charge,
            "accounting_semantics": (
                "53 calls and $2.65 are conservative bookkeeping ceiling charges, not recovered actual "
                "usage. Actual completed calls and spend remain unknown."
            ),
        },
        "retained_later_run": {
            "solver_calls": solve["provider_calls"],
            "scenario_calls": scenarios["provider_calls"],
            "total_calls": retained_calls,
            "estimated_spend_usd": retained_estimate,
            "model_patches": solve["solutions"],
            "scenario_programs": scenarios["scenarios"],
        },
        "conservative_ledger_total": {
            "charged_calls": retained_calls + charge["provider_calls"],
            "estimated_or_charged_spend_usd": round(
                retained_estimate + charge["estimated_spend_usd"], 2
            ),
            "not_actual_usage_claim": True,
        },
        "result_status": "scenario_safety_protocol_execution_null",
        "N_k_u": {"N": None, "k": None, "u": None},
        "chronology": {
            "first_hypothesis_commit": _first_addition(
                hypothesis,
                "41c4176f7b897678dea2e98e40582e7c03a369e1",
                "2026-07-15T15:23:11+03:00",
            ),
            "provider_contact_preceded_first_git_freeze": True,
        },
        "evidence": _evidence([process_path, solve_path, scenario_path]),
        "historical_git_evidence": _git_evidence(
            "a2a05ef2ed05a0c457076f2bd5f1475507190685",
            [hypothesis, amendment, result],
        ),
    }


def build_outputs() -> dict[Path, dict[str, Any]]:
    _validate_experiment_delta()
    historical_relabels = _historical_relabel_bindings()
    iter192 = audit_iter192()
    iter195 = audit_iter195()
    iter199 = audit_iter199()
    iter196 = audit_iter196()
    iter201 = audit_iter201_disclosure()
    iter179_cost = audit_iter179_cost_attribution()
    iter200 = audit_iter200_attribution()
    iter202 = audit_iter202_accounting()
    correction_payloads = {OUTPUTS["iter192"]: iter192}
    strict_payloads = {OUTPUTS["iter195"]: iter195}
    correction_receipts = []
    for path, payload in sorted(correction_payloads.items()):
        correction_receipts.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "schema_version": payload["schema_version"],
                "sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
                "status": payload["standing_adjudication_status"],
                "literal_trigger_status": payload["literal_falsifier_5_status"],
            }
        )
    strict_receipts = []
    for path, payload in sorted(strict_payloads.items()):
        strict_receipts.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "schema_version": payload["schema_version"],
                "sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
                "status": "fail",
            }
        )
    ledger = {
        "schema_version": "telos.iter207.claim_integrity_correction.v2",
        "experiment_id": EXP.name,
        "status": "active_pre_result",
        "generator_mode": "deterministic_offline_retrospective",
        "custody_rule": (
            "Frozen hypotheses, raw outputs, receipts, logs, patches, retained prompts/responses, provider "
            "checkpoints, and prior Git objects are immutable inputs. Only the exact historical RESULT.md "
            "and learning_record.json paths in historical_public_surface_relabels may be reinterpreted; "
            "their iter206-seal blobs remain hash-bound."
        ),
        "historical_public_surface_relabels": historical_relabels,
        "experiment_delta_guard": {
            "base_commit": ITER206_SEAL_COMMIT,
            "authorized_historical_relabels": sorted(
                path.relative_to(ROOT).as_posix() for path in HISTORICAL_RELABEL_PATHS
            ),
            "authorized_additive_iter206_terminal_nulls": sorted(ADDITIVE_ITER206_PATHS),
            "authorized_iter207_prefix": ITER207_PREFIX,
        },
        "investigation_side_effect_accounting": {
            "provider_calls": 0,
            "credential_reads_or_probes": 0,
            "network_calls": 2,
            "network_call_scope": "authenticated_read_only_github_metadata_gets_for_ci_projection_verification",
            "containers_or_scientific_executions": 0,
            "remote_mutations": 0,
        },
        "interpretive_correction_subreceipts": correction_receipts,
        "strict_protocol_subreceipts": strict_receipts,
        "corrections": {
            "iter192": {
                "standing_adjudication_status": iter192["standing_adjudication_status"],
                "literal_falsifier_5_status": iter192["literal_falsifier_5_status"],
                "correction_id": iter192["correction_id"],
                "retained_findings": iter192["retained_findings"],
            },
            "iter195": {
                "strict_protocol_status": iter195["strict_protocol_status"],
                "failure_ids": [row["id"] for row in iter195["protocol_failures"]],
                "retained_counts": iter195["retained_counts"],
                "retained_exploratory_interpretation": iter195[
                    "retained_exploratory_interpretation"
                ],
            },
            "iter196": iter196,
            "iter199": iter199,
            "iter179_cost_attribution": iter179_cost,
            "iter200": iter200,
            "iter201": iter201,
            "iter202": iter202,
        },
        "publication_rule": (
            "No public surface may describe iter192 as a strict literal-trigger failure or unqualified "
            "pass, or retain a superseded preregistration, gold-blind, global semantic, "
            "run-attribution, or exact-usage claim contradicted by this ledger. No iter207 RESULT exists "
            "until the separate runtime admission recovery and public-surface correction are complete."
        ),
    }
    return {**correction_payloads, **strict_payloads, OUTPUTS["ledger"]: ledger}


def _canonical(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_outputs(outputs: dict[Path, dict[str, Any]]) -> None:
    for path, payload in sorted(outputs.items()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_canonical(payload))


def check_outputs(outputs: dict[Path, dict[str, Any]]) -> list[str]:
    failures = []
    for path, payload in sorted(outputs.items()):
        expected = _canonical(payload)
        if not path.is_file():
            failures.append(f"missing correction artifact: {path.relative_to(ROOT)}")
        elif path.read_bytes() != expected:
            failures.append(f"correction artifact drift: {path.relative_to(ROOT)}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail unless artifacts reproduce exactly")
    args = parser.parse_args(argv)
    try:
        outputs = build_outputs()
    except (ClaimIntegrityError, subprocess.CalledProcessError) as exc:
        print(f"iter207 claim-integrity audit failed: {exc}", file=sys.stderr)
        return 1
    if args.check:
        failures = check_outputs(outputs)
        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 1
        print("iter207 claim-integrity correction artifacts reproduce exactly")
        return 0
    write_outputs(outputs)
    print("iter207 claim-integrity correction artifacts written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
