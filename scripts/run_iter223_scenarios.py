#!/usr/bin/env python3
"""iter200 Phase A (part 2): gold-vs-model witnessing scenarios for the neutral-solve patches.

Reuses the iter195 scenario generator, comparing the gold patch against the MODEL patch. Only patches that
differ from gold need a scenario (identical ones cannot diverge). Gold is used at ground-truth time only.
Reads OPENAI_API_KEY. Ceiling: <=50 calls, <=$15.00.
"""

from __future__ import annotations

import os

import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / os.environ.get("TELOS_NAT_EXP", "iter200_natural_certified_yet_wrong_rate")
SOLS = EXP / "proof" / "raw" / "solutions"
STAGE = EXP / "proof" / "raw" / "scenarios"
SNAPSHOT = (
    ROOT
    / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
)
_spec = importlib.util.spec_from_file_location("scen195", ROOT / "scripts" / "run_iter195_scenario_generator.py")
scen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scen)
_checkpoint_spec = importlib.util.spec_from_file_location(
    "iter202_checkpointing", ROOT / "scripts" / "run_iter200_solver.py"
)
checkpoint = importlib.util.module_from_spec(_checkpoint_spec)
_checkpoint_spec.loader.exec_module(checkpoint)
sys.path.insert(0, str(ROOT))
from scripts.validate_iter202_runtime_freeze import (  # noqa: E402
    RuntimeFreezeError,
    require_valid_runtime_freeze,
)

CALL_CEILING = 50
SPEND_CEILING = 15.00
FROZEN_MODEL = "gpt-5.6-terra"
ITER202_EXP = "iter202_natural_rate_scaled"


def _after_attempt_checkpoint() -> None:
    """Test seam immediately after raw outcome retention and before parsing."""


def _after_secure_stage_preflight() -> None:
    """Test seam before any scenario credential or provider request."""


def _before_provider_request() -> None:
    """Test seam followed by a binding check immediately before provider I/O."""


def _assert_runtime_freeze() -> str:
    """Reject an unreviewed iter202 runtime before accepting checkpoints or credentials."""

    try:
        runtime_manifest_sha256 = require_valid_runtime_freeze()
    except RuntimeFreezeError as exc:
        raise checkpoint.CheckpointError(f"iter202 runtime freeze is invalid: {exc}") from exc
    if (
        not isinstance(runtime_manifest_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", runtime_manifest_sha256) is None
    ):
        raise checkpoint.CheckpointError(
            "iter202 runtime freeze returned a malformed manifest SHA-256"
        )
    return runtime_manifest_sha256


def _assert_solver_module_binding() -> None:
    """Prove the imported checkpoint helper addresses this experiment's frozen paths."""

    expected = {
        "experiment": EXP,
        "snapshot": SNAPSHOT,
        "solutions": SOLS,
        "targets": EXP / "proof/raw/solve_targets.json",
    }
    actual = {
        "experiment": checkpoint.EXP,
        "snapshot": checkpoint.SNAPSHOT,
        "solutions": checkpoint.STAGE,
        "targets": checkpoint.TARGETS,
    }
    mismatches = [
        label
        for label in expected
        if Path(os.path.abspath(os.fspath(expected[label])))
        != Path(os.path.abspath(os.fspath(actual[label])))
    ]
    if mismatches or checkpoint.adv.MODEL != FROZEN_MODEL:
        raise checkpoint.CheckpointError(
            "scenario checkpoint helper is not bound to the frozen iter202 solver "
            f"(path mismatches={mismatches})"
        )


def _require_iter202_path_contract() -> None:
    """Bind the paid scenario stage to the canonical frozen experiment."""

    expected_experiment = ROOT / "experiments" / ITER202_EXP
    expected = {
        "experiment": expected_experiment,
        "scenarios": expected_experiment / "proof/raw/scenarios",
        "solutions": expected_experiment / "proof/raw/solutions",
    }
    actual = {"experiment": EXP, "scenarios": STAGE, "solutions": SOLS}
    mismatches = [
        label
        for label, expected_path in expected.items()
        if Path(os.path.abspath(os.fspath(actual[label])))
        != Path(os.path.abspath(os.fspath(expected_path)))
    ]
    if mismatches:
        raise checkpoint.CheckpointError(
            "iter202 scenario entrypoint is not bound to the canonical experiment paths: "
            f"{mismatches}"
        )
    checkpoint._require_iter202_path_contract()


def _require_exact_files(
    *,
    directory: Path,
    expected: dict[Path, bytes],
    patterns: tuple[str, ...],
    label: str,
    secure_stage: checkpoint.SecureCheckpointStage | None = None,
) -> None:
    """Require an exact regular-file set and exact bytes without repairing downstream input."""

    if secure_stage is None:
        with checkpoint._open_secure_stage(directory, create=False) as opened:
            return _require_exact_files(
                directory=directory,
                expected=expected,
                patterns=patterns,
                label=label,
                secure_stage=opened,
            )
    suffixes = tuple(pattern.removeprefix("*") for pattern in patterns)
    actual_names = secure_stage.matching_regular_names(suffixes)
    expected_names = {path.name for path in expected}
    if actual_names != expected_names:
        missing = sorted(expected_names - actual_names)
        extra = sorted(actual_names - expected_names)
        raise checkpoint.CheckpointError(
            f"{label} file set differs from checkpoint evidence: missing={missing}, extra={extra}"
        )
    for path, payload in expected.items():
        if Path(os.path.abspath(os.fspath(path.parent))) != secure_stage.path:
            raise checkpoint.CheckpointError(f"{label} path escapes retained stage: {path}")
        if secure_stage.read_bytes(path.name) != payload:
            raise checkpoint.CheckpointError(
                f"{label} bytes differ from checkpoint evidence: {path}"
            )


def _reconstruct_solver_state_locked(
    runtime_manifest_sha256: str,
    solution_stage: checkpoint.SecureCheckpointStage | None = None,
) -> dict:
    """Rebuild and exact-compare terminal solver state while the solver lock is held."""

    if solution_stage is None:
        with checkpoint._open_secure_stage(SOLS, create=False) as opened:
            return _reconstruct_solver_state_locked(
                runtime_manifest_sha256, solution_stage=opened
            )
    _assert_solver_module_binding()
    work, specs = checkpoint._solver_work(runtime_manifest_sha256)
    complete = checkpoint._load_complete_attempts(solution_stage, specs)
    if len(complete) != len(specs):
        raise checkpoint.CheckpointError(
            "scenario generation requires every planned solver attempt to have terminal checkpoint evidence"
        )
    expected_summary, expected_artifacts = checkpoint._solver_state(work, complete)
    summary_path = SOLS / "solve_summary.json"
    expected_summary_bytes = checkpoint._canonical_json_bytes(expected_summary)
    if (
        not solution_stage.regular_file_exists(summary_path.name)
        or solution_stage.read_bytes(summary_path.name) != expected_summary_bytes
    ):
        raise checkpoint.CheckpointError(
            "solve summary does not exactly reproduce from frozen targets and solver checkpoints"
        )
    _require_exact_files(
        directory=SOLS,
        expected=expected_artifacts,
        patterns=("*.model.patch", "*.gold.patch"),
        label="solver artifact",
        secure_stage=solution_stage,
    )
    return expected_summary


def _scenario_work_from_solver_summary(
    summary: dict,
    runtime_manifest_sha256: str,
    solution_stage: checkpoint.SecureCheckpointStage | None = None,
) -> tuple[list[dict], list[dict], int]:
    if solution_stage is None:
        with checkpoint._open_secure_stage(SOLS, create=False) as opened:
            return _scenario_work_from_solver_summary(
                summary,
                runtime_manifest_sha256,
                solution_stage=opened,
            )
    if (
        not isinstance(runtime_manifest_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", runtime_manifest_sha256) is None
    ):
        raise checkpoint.CheckpointError("scenario runtime manifest SHA-256 is malformed")
    snapshot = checkpoint._load_json_strict(SNAPSHOT)
    rows = snapshot.get("rows")
    if not isinstance(rows, list):
        raise checkpoint.CheckpointError("frozen SWE-bench snapshot rows are malformed")
    by_id: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("instance_id"), str):
            raise checkpoint.CheckpointError("frozen SWE-bench snapshot contains a malformed row")
        iid = row["instance_id"]
        if iid in by_id:
            raise checkpoint.CheckpointError(f"frozen SWE-bench snapshot duplicates {iid}")
        by_id[iid] = row

    manifest = summary.get("manifest")
    solution_count = summary.get("solutions")
    target_count = summary.get("targets")
    if (
        summary.get("schema_version") != "telos.iter200.solve_summary.v1"
        or summary.get("checkpoint_schema")
        != {
            "finished": checkpoint.FINISHED_SCHEMA,
            "started": checkpoint.STARTED_SCHEMA,
        }
        or summary.get("solver_model") != FROZEN_MODEL
        or not isinstance(manifest, list)
        or not isinstance(solution_count, int)
        or isinstance(solution_count, bool)
        or not isinstance(target_count, int)
        or isinstance(target_count, bool)
        or target_count != len(manifest)
        or solution_count
        != sum(isinstance(row, dict) and row.get("status") == "solution" for row in manifest)
    ):
        raise checkpoint.CheckpointError("solve summary is malformed or internally inconsistent")
    seen: set[str] = set()
    diffs: list[str] = []
    solution_by_id: dict[str, dict] = {}
    for entry in manifest:
        if not isinstance(entry, dict) or not isinstance(entry.get("instance_id"), str):
            raise checkpoint.CheckpointError("solve summary contains a malformed manifest row")
        iid = entry["instance_id"]
        if iid in seen:
            raise checkpoint.CheckpointError(f"solve summary duplicates {iid}")
        seen.add(iid)
        status = entry.get("status")
        if status not in {
            "budget_stopped",
            "empty_fix",
            "no_patch",
            "no_region",
            "no_single_src",
            "provider_error",
            "solution",
        }:
            raise checkpoint.CheckpointError(
                f"scenario generation cannot start from solver status {status!r}"
            )
        if status == "solution":
            if not isinstance(entry.get("identical_to_gold"), bool):
                raise checkpoint.CheckpointError(
                    f"solve summary has invalid gold-equivalence metadata for {iid}"
                )
            if not entry["identical_to_gold"]:
                diffs.append(iid)
                solution_by_id[iid] = entry

    work: list[dict] = []
    specs: list[dict] = []
    for iid in diffs:
        entry = solution_by_id[iid]
        stem = iid.replace("/", "__")
        row = by_id.get(iid)
        if row is None:
            raise checkpoint.CheckpointError(
                f"differing solution is absent from frozen source snapshot: {iid}"
            )
        gold_path = SOLS / f"{stem}.gold.patch"
        model_path = SOLS / f"{stem}.model.patch"
        if not solution_stage.regular_file_exists(
            gold_path.name
        ) or not solution_stage.regular_file_exists(model_path.name):
            raise checkpoint.CheckpointError(f"differing solution evidence is missing for {iid}")
        gold_bytes = solution_stage.read_bytes(gold_path.name)
        model_bytes = solution_stage.read_bytes(model_path.name)
        expected_gold = (
            row["patch"] + ("\n" if not row["patch"].endswith("\n") else "")
        ).encode("utf-8")
        if gold_bytes != expected_gold:
            raise checkpoint.CheckpointError(
                f"gold solution artifact does not match frozen source for {iid}"
            )
        if (
            not model_bytes.endswith(b"\n")
            or not isinstance(entry.get("model_patch_sha256"), str)
            or hashlib.sha256(model_bytes[:-1]).hexdigest()
            != entry["model_patch_sha256"]
        ):
            raise checkpoint.CheckpointError(
                f"model solution artifact does not match solve summary for {iid}"
            )
        gold_patch = gold_bytes.decode("utf-8")
        model_patch = model_bytes.decode("utf-8")
        src_files = [
            line[6:]
            for line in model_patch.splitlines()
            if line.startswith("+++ b/")
            and "/test" not in line
            and "test_" not in line.split("/")[-1]
        ]
        src_file = src_files[0] if src_files else None
        func = "the changed function"
        for line in model_patch.splitlines():
            if line.startswith("@@") and ("def " in line or "class " in line):
                match = re.search(r"(?:def|class)\s+(\w+)", line)
                if match:
                    func = match.group(1)
        if not src_file:
            work.append({"instance_id": iid, "offline_status": "no_src"})
            continue
        problem = row.get("problem_statement") or ""
        if not isinstance(problem, str) or not isinstance(row.get("repo"), str):
            raise checkpoint.CheckpointError(f"frozen source row is malformed for {iid}")
        prompt = scen.PROMPT.format(
            repo=row["repo"],
            src_file=src_file,
            func=func,
            problem=problem[:1000],
            gold_hunk=scen.hunk(gold_patch, src_file)[:2500],
            variant_hunk=scen.hunk(model_patch, src_file)[:2500],
        )
        sequence = len(specs) + 1
        spec = {
            "estimated_spend_usd": scen.EST_USD_PER_CALL,
            "experiment_id": EXP.name,
            "instance_id": iid,
            "model": scen.MODEL,
            "phase": "scenario_generation",
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "runtime_manifest_sha256": runtime_manifest_sha256,
            "sequence": sequence,
        }
        specs.append(spec)
        work.append(
            {
                "func": func,
                "instance_id": iid,
                "prompt": prompt,
                "repo": row["repo"],
                "sequence": sequence,
            }
        )
    return work, specs, len(diffs)


def _scenario_work() -> tuple[list[dict], list[dict], int]:
    """Return scenario work only from checkpoint-reconstructed, frozen solver evidence."""

    runtime_manifest_sha256 = checkpoint._runtime_manifest_sha256()
    with checkpoint._open_secure_stage(SOLS, create=False) as solution_stage:
        with checkpoint._exclusive_stage_lock(solution_stage):
            summary = _reconstruct_solver_state_locked(
                runtime_manifest_sha256, solution_stage
            )
            return _scenario_work_from_solver_summary(
                summary, runtime_manifest_sha256, solution_stage
            )


def _scenario_state(
    work: list[dict],
    complete: dict[str, tuple[dict, dict]],
    differing_solutions: int,
) -> tuple[dict, dict[Path, bytes]]:
    manifest: list[dict] = []
    artifacts: dict[Path, bytes] = {}
    for item in work:
        iid = item["instance_id"]
        if "offline_status" in item:
            manifest.append({"instance_id": iid, "status": item["offline_status"]})
            continue
        if item["sequence"] > CALL_CEILING or (
            item["sequence"] * scen.EST_USD_PER_CALL > SPEND_CEILING
        ):
            continue
        retained = complete.get(iid)
        if retained is None:
            continue
        started, finished = retained
        if finished["outcome"] == "provider_error":
            manifest.append(
                {
                    "detail": finished["error"]["message"][:160],
                    "instance_id": iid,
                    "provider_attempt_id": started["attempt_id"],
                    "status": "provider_error",
                }
            )
            continue
        raw = finished["raw_response"]
        script = scen.extract_code(raw)
        if not script.strip() or "RESULT=" not in script:
            manifest.append(
                {
                    "instance_id": iid,
                    "provider_attempt_id": started["attempt_id"],
                    "status": "no_scenario",
                }
            )
            continue
        stem = iid.replace("/", "__")
        artifacts[STAGE / f"{stem}.scenario.py"] = (script + "\n").encode("utf-8")
        manifest.append(
            {
                "func": item["func"],
                "instance_id": iid,
                "provider_attempt_id": started["attempt_id"],
                "provider_response_sha256": finished["raw_response_sha256"],
                "provider_usage": finished["provider_usage"],
                "repo": item["repo"],
                "scenario_sha256": hashlib.sha256(script.encode("utf-8")).hexdigest(),
                "status": "scenario",
            }
        )
    calls = len(complete)
    spend = round(
        sum(float(started["accounting"]["estimated_spend_usd"]) for started, _ in complete.values()),
        4,
    )
    return (
        {
            "checkpoint_schema": {
                "finished": checkpoint.FINISHED_SCHEMA,
                "started": checkpoint.STARTED_SCHEMA,
            },
            "differing_solutions": differing_solutions,
            "estimated_spend_usd": spend,
            "manifest": manifest,
            "model": scen.MODEL,
            "provider_calls": calls,
            "scenarios": sum(row["status"] == "scenario" for row in manifest),
            "schema_version": "telos.iter200.scenarios_summary.v1",
        },
        artifacts,
    )


def _validate_and_materialize_artifacts(
    artifacts: dict[Path, bytes],
    secure_stage: checkpoint.SecureCheckpointStage | None = None,
) -> None:
    if secure_stage is None:
        with checkpoint._open_secure_stage(STAGE, create=True) as opened:
            return _validate_and_materialize_artifacts(artifacts, opened)
    expected_names = {path.name for path in artifacts}
    if any(
        Path(os.path.abspath(os.fspath(path.parent))) != secure_stage.path
        for path in artifacts
    ):
        raise checkpoint.CheckpointError(
            "reconstructed scenario artifact escapes retained stage"
        )
    actual_names = secure_stage.matching_regular_names((".scenario.py",))
    extras = sorted(actual_names - expected_names)
    if extras:
        raise checkpoint.CheckpointError(
            "scenario outputs exist without complete checkpoint evidence: "
            f"{[str(secure_stage.path / name) for name in extras]}"
        )
    for path, payload in artifacts.items():
        if secure_stage.regular_file_exists(path.name) and secure_stage.read_bytes(path.name) != payload:
            raise checkpoint.CheckpointError(f"retained scenario hash mismatch: {path}")
    for path, payload in artifacts.items():
        secure_stage.retain_exact(path.name, payload)


def _planned_scenario_attempts(specs: list[dict]) -> int:
    return sum(
        spec["sequence"] <= CALL_CEILING
        and spec["sequence"] * scen.EST_USD_PER_CALL <= SPEND_CEILING
        for spec in specs
    )


def _require_exact_scenario_state(
    work: list[dict],
    specs: list[dict],
    differing_solutions: int,
    scenario_stage: checkpoint.SecureCheckpointStage | None = None,
) -> dict:
    """Rebuild terminal scenario state and reject any derived-state drift."""

    if scenario_stage is None:
        with checkpoint._open_secure_stage(STAGE, create=False) as opened:
            return _require_exact_scenario_state(
                work, specs, differing_solutions, scenario_stage=opened
            )
    complete = checkpoint._load_complete_attempts(scenario_stage, specs)
    planned = _planned_scenario_attempts(specs)
    if len(complete) != planned:
        raise checkpoint.CheckpointError(
            "spec extraction requires every planned scenario attempt to have terminal checkpoint evidence "
            f"(expected={planned}, retained={len(complete)})"
        )
    expected_summary, expected_artifacts = _scenario_state(
        work, complete, differing_solutions
    )
    summary_path = STAGE / "scenarios_summary.json"
    if (
        not scenario_stage.regular_file_exists(summary_path.name)
        or scenario_stage.read_bytes(summary_path.name)
        != checkpoint._canonical_json_bytes(expected_summary)
    ):
        raise checkpoint.CheckpointError(
            "scenario summary does not exactly reproduce from solver evidence and scenario checkpoints"
        )
    _require_exact_files(
        directory=STAGE,
        expected=expected_artifacts,
        patterns=("*.scenario.py",),
        label="scenario artifact",
        secure_stage=scenario_stage,
    )
    return expected_summary


def reconstruct_stage_inputs_for_specs(
    runtime_manifest_sha256: str,
) -> tuple[dict, dict]:
    """Reconstruct terminal stage inputs after the caller validates the runtime freeze."""

    if (
        not isinstance(runtime_manifest_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", runtime_manifest_sha256) is None
    ):
        raise checkpoint.CheckpointError(
            "spec reconstruction requires a valid runtime manifest SHA-256"
        )
    with checkpoint._open_secure_stage(
        SOLS, create=False, enforce_trusted_root=True
    ) as solution_stage:
        with checkpoint._open_secure_stage(
            STAGE, create=True, enforce_trusted_root=True
        ) as scenario_stage:
            with checkpoint._exclusive_stage_lock(solution_stage):
                with checkpoint._exclusive_stage_lock(scenario_stage):
                    solve_summary = _reconstruct_solver_state_locked(
                        runtime_manifest_sha256, solution_stage
                    )
                    work, specs, differing_solutions = _scenario_work_from_solver_summary(
                        solve_summary, runtime_manifest_sha256, solution_stage
                    )
                    scenarios_summary = _require_exact_scenario_state(
                        work, specs, differing_solutions, scenario_stage
                    )
    return solve_summary, scenarios_summary


def validated_stage_inputs_for_specs() -> tuple[dict, dict]:
    """Self-gated compatibility wrapper for terminal iter202 stage reconstruction."""

    return reconstruct_stage_inputs_for_specs(_assert_runtime_freeze())


def _run_iter202_locked(
    runtime_manifest_sha256: str,
    solution_stage: checkpoint.SecureCheckpointStage,
    scenario_stage: checkpoint.SecureCheckpointStage,
) -> tuple[dict, int]:
    solve_summary = _reconstruct_solver_state_locked(
        runtime_manifest_sha256, solution_stage
    )
    work, specs, differing_solutions = _scenario_work_from_solver_summary(
        solve_summary, runtime_manifest_sha256, solution_stage
    )
    complete = checkpoint._load_complete_attempts(scenario_stage, specs)
    if len(complete) > CALL_CEILING:
        raise checkpoint.CheckpointError("retained scenario attempts exceed the call ceiling")
    checkpoint._validate_existing_summary(
        STAGE / "scenarios_summary.json",
        "telos.iter200.scenarios_summary.v1",
        len(complete),
        secure_stage=scenario_stage,
    )
    summary, artifacts = _scenario_state(work, complete, differing_solutions)
    _validate_and_materialize_artifacts(artifacts, scenario_stage)
    if complete:
        checkpoint._atomic_replace_bytes(
            STAGE / "scenarios_summary.json",
            checkpoint._canonical_json_bytes(summary),
            secure_stage=scenario_stage,
        )

    scenario_stage.hold_directory(checkpoint.ATTEMPT_DIRNAME, create=True)
    _after_secure_stage_preflight()
    solution_stage.verify_binding()
    scenario_stage.verify_binding()
    key: str | None = None
    for item, spec in zip(
        [candidate for candidate in work if "sequence" in candidate], specs, strict=True
    ):
        iid = item["instance_id"]
        if iid in complete or item["sequence"] > CALL_CEILING:
            continue
        if item["sequence"] * scen.EST_USD_PER_CALL > SPEND_CEILING:
            continue
        solution_stage.verify_binding()
        scenario_stage.verify_binding()
        if key is None:
            key = scen._key()
        solution_stage.verify_binding()
        scenario_stage.verify_binding()
        started = checkpoint._started_record(**spec)
        checkpoint._checkpoint_started(scenario_stage, started)
        _before_provider_request()
        solution_stage.verify_binding()
        scenario_stage.verify_binding()
        try:
            raw, usage = scen.gen(item["prompt"], key)
            if not isinstance(raw, str):
                raise TypeError("provider returned a non-string response")
            finished = checkpoint._finished_response_record(
                started, raw, usage, (key,)
            )
        except Exception as exc:
            finished = checkpoint._finished_error_record(started, exc, (key,))
        checkpoint._checkpoint_finished(scenario_stage, finished)
        complete[iid] = (started, finished)
        _after_attempt_checkpoint()
        solution_stage.verify_binding()
        scenario_stage.verify_binding()
        summary, artifacts = _scenario_state(work, complete, differing_solutions)
        _validate_and_materialize_artifacts(artifacts, scenario_stage)
        checkpoint._atomic_replace_bytes(
            STAGE / "scenarios_summary.json",
            checkpoint._canonical_json_bytes(summary),
            secure_stage=scenario_stage,
        )

    summary, artifacts = _scenario_state(work, complete, differing_solutions)
    _validate_and_materialize_artifacts(artifacts, scenario_stage)
    checkpoint._atomic_replace_bytes(
        STAGE / "scenarios_summary.json",
        checkpoint._canonical_json_bytes(summary),
        secure_stage=scenario_stage,
    )
    return summary, differing_solutions


def _main_iter202() -> int:
    _require_iter202_path_contract()
    runtime_manifest_sha256 = _assert_runtime_freeze()
    # Hold the solver lock for the full scenario stage: a sanctioned solver process cannot race
    # the exact upstream reconstruction or mutate its derived summary between validation and use.
    with checkpoint._open_secure_stage(
        SOLS, create=False, enforce_trusted_root=True
    ) as solution_stage:
        with checkpoint._open_secure_stage(
            STAGE, create=True, enforce_trusted_root=True
        ) as scenario_stage:
            with checkpoint._exclusive_stage_lock(solution_stage):
                with checkpoint._exclusive_stage_lock(scenario_stage):
                    summary, differing_solutions = _run_iter202_locked(
                        runtime_manifest_sha256, solution_stage, scenario_stage
                    )
    print(
        f"iter200 scenarios: {summary['scenarios']} from {differing_solutions} differing solutions, "
        f"{summary['provider_calls']} calls, ~${summary['estimated_spend_usd']:.2f}"
    )
    return 0


def _main_legacy() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    summary = json.loads((SOLS / "solve_summary.json").read_text())
    # only patches that differ from gold can diverge behaviorally
    diffs = [m["instance_id"] for m in summary["manifest"] if m["status"] == "solution" and not m["identical_to_gold"]]

    key = scen._key()
    calls = 0
    est = 0.0
    manifest: list[dict] = []
    for iid in diffs:
        if calls >= CALL_CEILING or est >= SPEND_CEILING:
            break
        stem = iid.replace("/", "__")
        row = by_id[iid]
        gold_patch = (SOLS / f"{stem}.gold.patch").read_text()
        model_patch = (SOLS / f"{stem}.model.patch").read_text()
        src_files = [
            line[6:] for line in model_patch.splitlines()
            if line.startswith("+++ b/") and "/test" not in line and "test_" not in line.split("/")[-1]
        ]
        src_file = src_files[0] if src_files else None
        func = "the changed function"
        for line in model_patch.splitlines():
            if line.startswith("@@") and ("def " in line or "class " in line):
                mm = re.search(r"(?:def|class)\s+(\w+)", line)
                if mm:
                    func = mm.group(1)
        if not src_file:
            manifest.append({"instance_id": iid, "status": "no_src"})
            continue
        prompt = scen.PROMPT.format(
            repo=row["repo"], src_file=src_file, func=func,
            problem=(row["problem_statement"] or "")[:1000],
            gold_hunk=scen.hunk(gold_patch, src_file)[:2500],
            variant_hunk=scen.hunk(model_patch, src_file)[:2500],
        )
        calls += 1
        est += scen.EST_USD_PER_CALL
        try:
            raw, usage = scen.gen(prompt, key)
        except Exception as exc:
            manifest.append({"instance_id": iid, "status": "provider_error", "detail": str(exc)[:160]})
            continue
        script = scen.extract_code(raw)
        if not script.strip() or "RESULT=" not in script:
            manifest.append({"instance_id": iid, "status": "no_scenario"})
            continue
        (STAGE / f"{stem}.scenario.py").write_text(script + "\n")
        manifest.append({"instance_id": iid, "status": "scenario", "repo": row["repo"], "func": func,
                         "scenario_sha256": hashlib.sha256(script.encode()).hexdigest(), "provider_usage": usage})

    out = {"schema_version": "telos.iter200.scenarios_summary.v1", "model": scen.MODEL,
           "differing_solutions": len(diffs), "provider_calls": calls, "estimated_spend_usd": round(est, 4),
           "scenarios": sum(1 for m in manifest if m["status"] == "scenario"), "manifest": manifest}
    (STAGE / "scenarios_summary.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"iter200 scenarios: {out['scenarios']} from {len(diffs)} differing solutions, {calls} calls, ~${est:.2f}")
    return 0


def main() -> int:
    if scen.MODEL != FROZEN_MODEL:
        raise SystemExit(
            f"natural-rate scenario model is frozen to {FROZEN_MODEL}; "
            "unset TELOS_ADVERSARY_MODEL"
        )
    if EXP.name == ITER202_EXP:
        return _main_iter202()
    return _main_legacy()


if __name__ == "__main__":
    sys.exit(main())
