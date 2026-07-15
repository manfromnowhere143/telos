from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNTIME_MANIFEST_SHA256 = "f" * 64


def load_script(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def source_row() -> dict[str, Any]:
    return {
        "FAIL_TO_PASS": json.dumps(["tests/test_bug.py::test_fix"]),
        "PASS_TO_PASS": json.dumps(["tests/test_other.py::test_regression"]),
        "base_commit": "a" * 40,
        "instance_id": "demo__demo-1",
        "patch": "\n".join(
            [
                "diff --git a/pkg.py b/pkg.py",
                "--- a/pkg.py",
                "+++ b/pkg.py",
                "@@ -1 +1,2 @@",
                " old_code()",
                "+gold_fix()",
                "",
            ]
        ),
        "problem_statement": "Fix the demonstrated bug.",
        "repo": "demo/demo",
    }


def configure_solver(
    module: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    experiment_name: str = "iter202_natural_rate_scaled",
) -> Path:
    experiment = tmp_path / "experiments" / experiment_name
    targets = experiment / "proof/raw/solve_targets.json"
    snapshot = tmp_path / "snapshot.json"
    write_json(
        targets,
        {
            "count": 1,
            "schema_version": "telos.iter202.solve_targets.v1",
            "targets": [{"instance_id": "demo__demo-1", "repo": "demo/demo"}],
        },
    )
    write_json(snapshot, {"rows": [source_row()]})
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "EXP", experiment)
    monkeypatch.setattr(module, "STAGE", experiment / "proof/raw/solutions")
    monkeypatch.setattr(module, "TARGETS", targets)
    monkeypatch.setattr(module, "SNAPSHOT", snapshot)
    monkeypatch.setattr(
        module,
        "require_valid_runtime_freeze",
        lambda: module._runtime_manifest_sha256(),
    )
    monkeypatch.setattr(module.adv, "MODEL", module.FROZEN_MODEL)
    monkeypatch.setattr(module.adv, "EST_USD_PER_CALL", 0.05)
    return experiment


class InjectedCrash(RuntimeError):
    pass


def test_solver_crash_after_raw_checkpoint_resumes_without_duplicate_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    solver = load_script("run_iter200_solver.py", "solver_crash_resume")
    experiment = configure_solver(solver, monkeypatch, tmp_path)
    calls: list[str] = []
    key_reads: list[bool] = []

    monkeypatch.setattr(solver.adv, "_key", lambda: key_reads.append(True) or "test-key")

    def generate(system: str, prompt: str, key: str) -> tuple[str, dict]:
        assert system == solver.SOLVE_SYS
        assert key == "test-key"
        calls.append(prompt)
        return "```python\nmodel_fix()\n```", {"total_tokens": 17}

    monkeypatch.setattr(solver.adv, "gen", generate)
    monkeypatch.setattr(
        solver,
        "_after_attempt_checkpoint",
        lambda: (_ for _ in ()).throw(InjectedCrash("after checkpoint")),
    )

    with pytest.raises(InjectedCrash, match="after checkpoint"):
        solver.main()

    attempt_dir = experiment / "proof/raw/solutions/provider_attempts"
    assert len(list(attempt_dir.glob("*.started.json"))) == 1
    finished = list(attempt_dir.glob("*.finished.json"))
    assert len(finished) == 1
    finished_doc = json.loads(finished[0].read_text())
    assert finished_doc["raw_response"] == "```python\nmodel_fix()\n```"
    assert finished_doc["provider_usage"] == {
        "status": "valid",
        "value": {"total_tokens": 17},
    }
    assert not (experiment / "proof/raw/solutions/solve_summary.json").exists()
    assert calls == [calls[0]]
    assert key_reads == [True]

    monkeypatch.setattr(solver, "_after_attempt_checkpoint", lambda: None)
    monkeypatch.setattr(
        solver.adv,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("resume read credentials")),
    )
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: (_ for _ in ()).throw(AssertionError("duplicate provider call")),
    )

    assert solver.main() == 0
    summary = json.loads(
        (experiment / "proof/raw/solutions/solve_summary.json").read_text()
    )
    assert summary["provider_calls"] == 1
    assert summary["estimated_spend_usd"] == 0.05
    assert summary["solutions"] == 1
    assert summary["manifest"][0]["provider_response_sha256"] == finished_doc[
        "raw_response_sha256"
    ]
    assert calls == [calls[0]]
    assert (experiment / "proof/raw/solutions/demo__demo-1.model.patch").is_file()
    assert (experiment / "proof/raw/solutions/demo__demo-1.gold.patch").is_file()


def test_solver_provider_error_accounting_survives_crash_and_resume(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    solver = load_script("run_iter200_solver.py", "solver_error_resume")
    experiment = configure_solver(solver, monkeypatch, tmp_path)
    provider_calls = 0

    monkeypatch.setattr(solver.adv, "_key", lambda: "do-not-retain-this-key")

    def fail_provider(*_args: Any) -> tuple[str, dict]:
        nonlocal provider_calls
        provider_calls += 1
        raise RuntimeError("transport failed for do-not-retain-this-key")

    monkeypatch.setattr(solver.adv, "gen", fail_provider)
    monkeypatch.setattr(
        solver,
        "_after_attempt_checkpoint",
        lambda: (_ for _ in ()).throw(InjectedCrash("after error checkpoint")),
    )
    with pytest.raises(InjectedCrash, match="after error checkpoint"):
        solver.main()

    finished_path = next(
        (experiment / "proof/raw/solutions/provider_attempts").glob("*.finished.json")
    )
    finished = json.loads(finished_path.read_text())
    assert finished["outcome"] == "provider_error"
    assert "do-not-retain-this-key" not in finished_path.read_text()

    monkeypatch.setattr(solver, "_after_attempt_checkpoint", lambda: None)
    monkeypatch.setattr(
        solver.adv,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("resume read credentials")),
    )
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: (_ for _ in ()).throw(AssertionError("provider error was retried")),
    )
    assert solver.main() == 0
    summary = json.loads(
        (experiment / "proof/raw/solutions/solve_summary.json").read_text()
    )
    assert provider_calls == 1
    assert summary["provider_calls"] == 1
    assert summary["estimated_spend_usd"] == 0.05
    assert summary["manifest"][0]["status"] == "provider_error"


def test_solver_inflight_crash_is_accounted_and_fails_closed_without_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    solver = load_script("run_iter200_solver.py", "solver_inflight_crash")
    experiment = configure_solver(solver, monkeypatch, tmp_path)
    provider_calls = 0
    monkeypatch.setattr(solver.adv, "_key", lambda: "test-key")

    def interrupt(*_args: Any) -> tuple[str, dict]:
        nonlocal provider_calls
        provider_calls += 1
        raise KeyboardInterrupt

    monkeypatch.setattr(solver.adv, "gen", interrupt)
    with pytest.raises(KeyboardInterrupt):
        solver.main()

    attempt_dir = experiment / "proof/raw/solutions/provider_attempts"
    started_path = next(attempt_dir.glob("*.started.json"))
    started = json.loads(started_path.read_text())
    assert started["accounting"] == {
        "estimated_spend_usd": 0.05,
        "provider_calls": 1,
    }
    assert not list(attempt_dir.glob("*.finished.json"))

    monkeypatch.setattr(
        solver.adv,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("incomplete resume read credentials")),
    )
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: (_ for _ in ()).throw(AssertionError("inflight call was repeated")),
    )
    with pytest.raises(solver.CheckpointError, match="incomplete provider checkpoint"):
        solver.main()
    assert provider_calls == 1
    assert json.loads(started_path.read_text())["accounting"]["provider_calls"] == 1


@pytest.mark.parametrize("damage", ["malformed", "duplicate"])
def test_solver_corrupt_or_duplicate_checkpoint_fails_before_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, damage: str
) -> None:
    solver = load_script("run_iter200_solver.py", f"solver_corrupt_{damage}")
    experiment = configure_solver(solver, monkeypatch, tmp_path)
    monkeypatch.setattr(solver.adv, "_key", lambda: "test-key")
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: ("```python\nmodel_fix()\n```", {"total_tokens": 2}),
    )
    assert solver.main() == 0
    attempt_dir = experiment / "proof/raw/solutions/provider_attempts"
    finished = next(attempt_dir.glob("*.finished.json"))
    if damage == "malformed":
        finished.write_text("{\"broken\":\n")
    else:
        started = next(attempt_dir.glob("*.started.json"))
        shutil.copyfile(started, attempt_dir / ("duplicate-" + started.name))

    monkeypatch.setattr(
        solver.adv,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("corrupt state read credentials")),
    )
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: (_ for _ in ()).throw(AssertionError("corrupt state called provider")),
    )
    with pytest.raises(solver.CheckpointError):
        solver.main()


def test_solver_runtime_freeze_blocks_before_stage_lock_or_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    solver = load_script("run_iter200_solver.py", "solver_runtime_freeze_gate")
    experiment = configure_solver(solver, monkeypatch, tmp_path)
    stage = experiment / "proof/raw/solutions"
    observed: list[str] = []

    def reject_freeze() -> None:
        observed.append("freeze")
        raise solver.RuntimeFreezeError("stale frozen byte")

    monkeypatch.setattr(solver, "require_valid_runtime_freeze", reject_freeze)
    monkeypatch.setattr(
        solver,
        "_exclusive_stage_lock",
        lambda _stage: (_ for _ in ()).throw(AssertionError("stage lock acquired")),
    )
    monkeypatch.setattr(
        solver,
        "_solver_work",
        lambda: (_ for _ in ()).throw(AssertionError("frozen inputs read")),
    )
    monkeypatch.setattr(
        solver.adv,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("credentials read")),
    )
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: (_ for _ in ()).throw(AssertionError("provider called")),
    )

    with pytest.raises(
        solver.CheckpointError, match="runtime freeze preflight failed"
    ):
        solver.main()

    assert observed == ["freeze"]
    assert not stage.exists()


@pytest.mark.parametrize(
    "selector",
    ["nested/iter202_natural_rate_scaled", "../iter202_natural_rate_scaled"],
)
def test_solver_rejects_noncanonical_iter202_selector_before_freeze_or_credentials(
    monkeypatch: pytest.MonkeyPatch, selector: str
) -> None:
    monkeypatch.setenv("TELOS_NAT_EXP", selector)
    solver = load_script(
        "run_iter200_solver.py",
        f"solver_noncanonical_{selector.replace('/', '_')}",
    )
    touched: list[str] = []

    monkeypatch.setattr(
        solver,
        "require_valid_runtime_freeze",
        lambda: touched.append("freeze") or TEST_RUNTIME_MANIFEST_SHA256,
    )
    monkeypatch.setattr(
        solver.adv,
        "_key",
        lambda: touched.append("key") or "test-key",
    )
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: touched.append("provider") or ("response", {}),
    )

    with pytest.raises(solver.CheckpointError, match="canonical experiment paths"):
        solver.main()

    assert touched == []


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_solver_checkpoint_loader_rejects_nonfinite_json(
    tmp_path: Path, constant: str
) -> None:
    solver = load_script("run_iter200_solver.py", f"solver_nonfinite_{constant}")
    path = tmp_path / "checkpoint.json"
    path.write_text('{"value":' + constant + "}\n")
    with pytest.raises(solver.CheckpointError, match="non-finite JSON constant"):
        solver._load_json_strict(path)


def test_solver_retains_raw_response_when_usage_metadata_is_invalid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    solver = load_script("run_iter200_solver.py", "solver_invalid_usage_retention")
    experiment = configure_solver(solver, monkeypatch, tmp_path)
    raw = "```python\nmodel_fix()\n```"
    provider_calls = 0

    monkeypatch.setattr(solver.adv, "_key", lambda: "sensitive-test-key")

    def generate(*_args: Any) -> tuple[str, dict[str, float]]:
        nonlocal provider_calls
        provider_calls += 1
        return raw, {"total_tokens": float("nan")}

    monkeypatch.setattr(solver.adv, "gen", generate)
    assert solver.main() == 0

    stage = experiment / "proof/raw/solutions"
    finished_path = next((stage / "provider_attempts").glob("*.finished.json"))
    finished = json.loads(finished_path.read_text())
    assert finished["outcome"] == "response"
    assert finished["raw_response"] == raw
    assert finished["raw_response_sha256"] == hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()
    assert finished["provider_usage"]["status"] == "invalid"
    assert set(finished["provider_usage"]) == {"error", "status"}
    assert "sensitive-test-key" not in finished_path.read_text()

    summary = json.loads((stage / "solve_summary.json").read_text())
    assert summary["provider_calls"] == 1
    assert summary["estimated_spend_usd"] == 0.05
    assert summary["solutions"] == 1
    assert summary["manifest"][0]["provider_usage"]["status"] == "invalid"

    monkeypatch.setattr(
        solver.adv,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("resume read credentials")),
    )
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: (_ for _ in ()).throw(AssertionError("response repeated")),
    )
    assert solver.main() == 0
    assert provider_calls == 1


@pytest.mark.parametrize("component", ["stage", "attempts"])
def test_solver_rejects_preexisting_checkpoint_symlink_before_credentials(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    component: str,
) -> None:
    solver = load_script("run_iter200_solver.py", f"solver_symlink_{component}")
    experiment = configure_solver(solver, monkeypatch, tmp_path)
    stage = experiment / "proof/raw/solutions"
    attacker = tmp_path / "attacker-solver"
    attacker.mkdir()
    if component == "stage":
        stage.symlink_to(attacker, target_is_directory=True)
    else:
        stage.mkdir(parents=True)
        (stage / solver.ATTEMPT_DIRNAME).symlink_to(
            attacker, target_is_directory=True
        )
    key_reads: list[str] = []
    provider_calls: list[str] = []
    monkeypatch.setattr(solver.adv, "_key", lambda: key_reads.append("key") or "key")
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: provider_calls.append("call") or ("response", {}),
    )

    with pytest.raises(solver.CheckpointError):
        solver.main()

    assert key_reads == []
    assert provider_calls == []
    assert list(attacker.iterdir()) == []


def test_solver_parent_swap_fails_before_credentials_without_external_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    solver = load_script("run_iter200_solver.py", "solver_parent_swap")
    experiment = configure_solver(solver, monkeypatch, tmp_path)
    raw = experiment / "proof/raw"
    parked = experiment / "proof/raw-retained"
    attacker = tmp_path / "attacker-solver-swap"
    attacker.mkdir()
    key_reads: list[str] = []
    provider_calls: list[str] = []

    def swap_parent() -> None:
        raw.rename(parked)
        raw.symlink_to(attacker, target_is_directory=True)

    monkeypatch.setattr(solver, "_after_secure_stage_preflight", swap_parent)
    monkeypatch.setattr(solver.adv, "_key", lambda: key_reads.append("key") or "key")
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: provider_calls.append("call") or ("response", {}),
    )

    with pytest.raises(solver.CheckpointError, match="binding|symlink|traverse|verified"):
        solver.main()

    assert key_reads == []
    assert provider_calls == []
    assert list(attacker.iterdir()) == []
    assert (parked / "solutions" / solver.ATTEMPT_DIRNAME).is_dir()


def configure_scenarios(
    module: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Path:
    experiment = tmp_path / "experiments/iter202_natural_rate_scaled"
    solutions = experiment / "proof/raw/solutions"
    scenarios = experiment / "proof/raw/scenarios"
    targets = experiment / "proof/raw/solve_targets.json"
    snapshot = tmp_path / "snapshot.json"
    row = source_row()
    write_json(
        targets,
        {
            "count": 1,
            "schema_version": "telos.iter202.solve_targets.v1",
            "targets": [{"instance_id": row["instance_id"], "repo": row["repo"]}],
        },
    )
    write_json(snapshot, {"rows": [row]})
    solutions.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "EXP", experiment)
    monkeypatch.setattr(module, "SOLS", solutions)
    monkeypatch.setattr(module, "STAGE", scenarios)
    monkeypatch.setattr(module, "SNAPSHOT", snapshot)
    monkeypatch.setattr(
        module,
        "_assert_runtime_freeze",
        lambda: TEST_RUNTIME_MANIFEST_SHA256,
    )
    monkeypatch.setattr(module.scen, "MODEL", module.FROZEN_MODEL)
    monkeypatch.setattr(module.scen, "EST_USD_PER_CALL", 0.05)

    solver = module.checkpoint
    monkeypatch.setattr(solver, "ROOT", tmp_path)
    monkeypatch.setattr(solver, "EXP", experiment)
    monkeypatch.setattr(solver, "STAGE", solutions)
    monkeypatch.setattr(solver, "TARGETS", targets)
    monkeypatch.setattr(solver, "SNAPSHOT", snapshot)
    monkeypatch.setattr(solver.adv, "MODEL", module.FROZEN_MODEL)
    monkeypatch.setattr(solver.adv, "EST_USD_PER_CALL", 0.05)
    work, specs = solver._solver_work(TEST_RUNTIME_MANIFEST_SHA256)
    started = solver._started_record(**specs[0])
    finished = solver._finished_response_record(
        started,
        "```python\nmodel_fix()\n```",
        {"total_tokens": 7},
        ("fixture-key",),
    )
    solver._checkpoint_started(solutions, started)
    solver._checkpoint_finished(solutions, finished)
    summary, artifacts = solver._solver_state(
        work, {row["instance_id"]: (started, finished)}
    )
    for path, payload in artifacts.items():
        solver._retain_exact_bytes(path, payload)
    solver._atomic_replace_bytes(
        solutions / "solve_summary.json", solver._canonical_json_bytes(summary)
    )
    return experiment


@pytest.mark.parametrize("component", ["stage", "attempts"])
def test_scenario_rejects_preexisting_checkpoint_symlink_before_credentials(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    component: str,
) -> None:
    scenarios = load_script(
        "run_iter200_scenarios.py", f"scenario_symlink_{component}"
    )
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    stage = experiment / "proof/raw/scenarios"
    attacker = tmp_path / "attacker-scenario"
    attacker.mkdir()
    if component == "stage":
        stage.symlink_to(attacker, target_is_directory=True)
    else:
        stage.mkdir(parents=True)
        (stage / scenarios.checkpoint.ATTEMPT_DIRNAME).symlink_to(
            attacker, target_is_directory=True
        )
    key_reads: list[str] = []
    provider_calls: list[str] = []
    monkeypatch.setattr(
        scenarios.scen, "_key", lambda: key_reads.append("key") or "key"
    )
    monkeypatch.setattr(
        scenarios.scen,
        "gen",
        lambda *_args: provider_calls.append("call") or ("response", {}),
    )

    with pytest.raises(scenarios.checkpoint.CheckpointError):
        scenarios.main()

    assert key_reads == []
    assert provider_calls == []
    assert list(attacker.iterdir()) == []


def test_scenario_parent_swap_fails_before_credentials_without_external_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", "scenario_parent_swap")
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    raw = experiment / "proof/raw"
    parked = experiment / "proof/raw-retained"
    attacker = tmp_path / "attacker-scenario-swap"
    attacker.mkdir()
    key_reads: list[str] = []
    provider_calls: list[str] = []

    def swap_parent() -> None:
        raw.rename(parked)
        raw.symlink_to(attacker, target_is_directory=True)

    monkeypatch.setattr(scenarios, "_after_secure_stage_preflight", swap_parent)
    monkeypatch.setattr(
        scenarios.scen, "_key", lambda: key_reads.append("key") or "key"
    )
    monkeypatch.setattr(
        scenarios.scen,
        "gen",
        lambda *_args: provider_calls.append("call") or ("response", {}),
    )

    with pytest.raises(
        scenarios.checkpoint.CheckpointError,
        match="binding|symlink|traverse|verified",
    ):
        scenarios.main()

    assert key_reads == []
    assert provider_calls == []
    assert list(attacker.iterdir()) == []
    assert (
        parked / "scenarios" / scenarios.checkpoint.ATTEMPT_DIRNAME
    ).is_dir()


def test_scenario_crash_after_raw_checkpoint_resumes_without_duplicate_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", "scenario_crash_resume")
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    provider_calls = 0
    monkeypatch.setattr(scenarios.scen, "_key", lambda: "test-key")

    def generate(prompt: str, key: str) -> tuple[str, dict]:
        nonlocal provider_calls
        assert "GOLD hunk" in prompt
        assert key == "test-key"
        provider_calls += 1
        return "```python\nprint('RESULT=ok')\n```", {"total_tokens": 11}

    monkeypatch.setattr(scenarios.scen, "gen", generate)
    monkeypatch.setattr(
        scenarios,
        "_after_attempt_checkpoint",
        lambda: (_ for _ in ()).throw(InjectedCrash("scenario checkpoint")),
    )
    with pytest.raises(InjectedCrash, match="scenario checkpoint"):
        scenarios.main()

    stage = experiment / "proof/raw/scenarios"
    assert len(list((stage / "provider_attempts").glob("*.finished.json"))) == 1
    assert not (stage / "scenarios_summary.json").exists()

    monkeypatch.setattr(scenarios, "_after_attempt_checkpoint", lambda: None)
    monkeypatch.setattr(
        scenarios.scen,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("scenario resume read credentials")),
    )
    monkeypatch.setattr(
        scenarios.scen,
        "gen",
        lambda *_args: (_ for _ in ()).throw(AssertionError("scenario call repeated")),
    )
    assert scenarios.main() == 0
    summary = json.loads((stage / "scenarios_summary.json").read_text())
    assert provider_calls == 1
    assert summary["provider_calls"] == 1
    assert summary["estimated_spend_usd"] == 0.05
    assert summary["scenarios"] == 1
    assert (stage / "demo__demo-1.scenario.py").read_text() == (
        "print('RESULT=ok')\n"
    )


def test_scenario_work_binds_each_model_patch_to_its_own_manifest_row(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", "scenario_per_row_binding")
    experiment = tmp_path / "iter202_natural_rate_scaled"
    solutions = experiment / "proof/raw/solutions"
    stage = experiment / "proof/raw/scenarios"
    snapshot = tmp_path / "snapshot.json"
    solutions.mkdir(parents=True)

    rows: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    for number in (1, 2):
        row = source_row()
        iid = f"demo__demo-{number}"
        row["instance_id"] = iid
        row["patch"] = row["patch"].replace("gold_fix()", f"gold_fix_{number}()")
        rows.append(row)
        stem = iid.replace("/", "__")
        gold_patch = row["patch"]
        model_patch = gold_patch.replace(
            f"gold_fix_{number}()", f"model_fix_{number}()"
        )
        (solutions / f"{stem}.gold.patch").write_text(gold_patch)
        (solutions / f"{stem}.model.patch").write_text(model_patch + "\n")
        manifest.append(
            {
                "identical_to_gold": False,
                "instance_id": iid,
                "model_patch_sha256": hashlib.sha256(model_patch.encode()).hexdigest(),
                "status": "solution",
            }
        )

    write_json(snapshot, {"rows": rows})
    solve_summary = {
        "checkpoint_schema": {
            "finished": scenarios.checkpoint.FINISHED_SCHEMA,
            "started": scenarios.checkpoint.STARTED_SCHEMA,
        },
        "estimated_spend_usd": 0.1,
        "manifest": manifest,
        "provider_calls": 2,
        "schema_version": "telos.iter200.solve_summary.v1",
        "solutions": 2,
        "solver_model": scenarios.FROZEN_MODEL,
        "targets": 2,
    }
    write_json(solutions / "solve_summary.json", solve_summary)
    monkeypatch.setattr(scenarios, "EXP", experiment)
    monkeypatch.setattr(scenarios, "SOLS", solutions)
    monkeypatch.setattr(scenarios, "STAGE", stage)
    monkeypatch.setattr(scenarios, "SNAPSHOT", snapshot)
    monkeypatch.setattr(scenarios.scen, "MODEL", scenarios.FROZEN_MODEL)
    monkeypatch.setattr(scenarios.scen, "EST_USD_PER_CALL", 0.05)

    work, specs, differing = scenarios._scenario_work_from_solver_summary(
        solve_summary, TEST_RUNTIME_MANIFEST_SHA256
    )
    assert differing == 2
    assert [row["instance_id"] for row in work] == [
        "demo__demo-1",
        "demo__demo-2",
    ]
    assert [row["instance_id"] for row in specs] == [
        "demo__demo-1",
        "demo__demo-2",
    ]
    assert {
        row["runtime_manifest_sha256"] for row in specs
    } == {TEST_RUNTIME_MANIFEST_SHA256}


def test_scenario_runtime_freeze_blocks_before_locks_or_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", "scenario_runtime_freeze_gate")
    real_gate = scenarios._assert_runtime_freeze
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    monkeypatch.setattr(scenarios, "_assert_runtime_freeze", real_gate)
    observed: list[str] = []

    def reject_freeze() -> None:
        observed.append("freeze")
        raise scenarios.RuntimeFreezeError("stale or missing manifest")

    monkeypatch.setattr(scenarios, "require_valid_runtime_freeze", reject_freeze)
    monkeypatch.setattr(
        scenarios.checkpoint,
        "_exclusive_stage_lock",
        lambda _stage: (_ for _ in ()).throw(AssertionError("stage lock acquired")),
    )
    monkeypatch.setattr(
        scenarios.scen,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("credentials read")),
    )
    with pytest.raises(
        scenarios.checkpoint.CheckpointError, match="runtime freeze is invalid"
    ):
        scenarios.main()

    assert observed == ["freeze"]
    assert not (experiment / "proof/raw/scenarios").exists()


@pytest.mark.parametrize(
    "selector",
    ["nested/iter202_natural_rate_scaled", "../iter202_natural_rate_scaled"],
)
def test_scenario_rejects_noncanonical_iter202_selector_before_freeze_or_credentials(
    monkeypatch: pytest.MonkeyPatch, selector: str
) -> None:
    monkeypatch.setenv("TELOS_NAT_EXP", selector)
    scenarios = load_script(
        "run_iter200_scenarios.py",
        f"scenario_noncanonical_{selector.replace('/', '_')}",
    )
    touched: list[str] = []

    monkeypatch.setattr(
        scenarios,
        "require_valid_runtime_freeze",
        lambda: touched.append("freeze") or TEST_RUNTIME_MANIFEST_SHA256,
    )
    monkeypatch.setattr(
        scenarios.scen,
        "_key",
        lambda: touched.append("key") or "test-key",
    )
    monkeypatch.setattr(
        scenarios.scen,
        "gen",
        lambda *_args: touched.append("provider") or ("response", {}),
    )

    with pytest.raises(
        scenarios.checkpoint.CheckpointError, match="canonical experiment paths"
    ):
        scenarios.main()

    assert touched == []


@pytest.mark.parametrize("mutation", ["accounting", "identity", "artifact", "extra_artifact"])
def test_scenario_rejects_solver_derived_state_drift_before_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", f"scenario_solver_drift_{mutation}")
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    solutions = experiment / "proof/raw/solutions"
    summary_path = solutions / "solve_summary.json"
    summary = json.loads(summary_path.read_text())
    if mutation == "accounting":
        summary["provider_calls"] = 0
        write_json(summary_path, summary)
    elif mutation == "identity":
        summary["manifest"][0]["instance_id"] = "outside__cohort-1"
        write_json(summary_path, summary)
    elif mutation == "artifact":
        (solutions / "demo__demo-1.model.patch").write_text("tampered\n")
    else:
        (solutions / "outside__cohort-1.model.patch").write_text("extra\n")

    monkeypatch.setattr(
        scenarios.scen,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("drift read credentials")),
    )
    monkeypatch.setattr(
        scenarios.scen,
        "gen",
        lambda *_args: (_ for _ in ()).throw(AssertionError("drift called provider")),
    )
    with pytest.raises(scenarios.checkpoint.CheckpointError):
        scenarios.main()
    assert not (experiment / "proof/raw/scenarios/provider_attempts").exists()


def test_scenario_solver_lock_race_fails_before_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", "scenario_solver_lock_race")
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    monkeypatch.setattr(
        scenarios.scen,
        "_key",
        lambda: (_ for _ in ()).throw(AssertionError("race read credentials")),
    )
    with scenarios.checkpoint._exclusive_stage_lock(
        experiment / "proof/raw/solutions"
    ):
        with pytest.raises(
            scenarios.checkpoint.CheckpointError, match="another iter202 process owns"
        ):
            scenarios.main()


def test_scenario_uses_canonical_solver_then_scenario_lock_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", "scenario_lock_order")
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    events: list[tuple[str, str]] = []

    @contextmanager
    def observed_lock(stage: Path):
        events.append(("enter", stage.name))
        try:
            yield
        finally:
            events.append(("exit", stage.name))

    monkeypatch.setattr(scenarios.checkpoint, "_exclusive_stage_lock", observed_lock)
    monkeypatch.setattr(scenarios.scen, "_key", lambda: "test-key")
    monkeypatch.setattr(
        scenarios.scen,
        "gen",
        lambda *_args: ("```python\nprint('RESULT=ok')\n```", {"total_tokens": 3}),
    )
    assert scenarios.main() == 0
    assert events == [
        ("enter", "solutions"),
        ("enter", "scenarios"),
        ("exit", "scenarios"),
        ("exit", "solutions"),
    ]
    assert (experiment / "proof/raw/scenarios/scenarios_summary.json").is_file()


def test_scenario_retains_raw_response_when_usage_metadata_is_invalid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", "scenario_invalid_usage_retention")
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    raw = "```python\nprint('RESULT=ok')\n```"
    monkeypatch.setattr(scenarios.scen, "_key", lambda: "sensitive-scenario-key")
    monkeypatch.setattr(
        scenarios.scen,
        "gen",
        lambda *_args: (raw, {"total_tokens": float("nan")}),
    )
    assert scenarios.main() == 0

    stage = experiment / "proof/raw/scenarios"
    finished_path = next((stage / "provider_attempts").glob("*.finished.json"))
    finished = json.loads(finished_path.read_text())
    assert finished["outcome"] == "response"
    assert finished["raw_response"] == raw
    assert finished["provider_usage"]["status"] == "invalid"
    assert "sensitive-scenario-key" not in finished_path.read_text()
    summary = json.loads((stage / "scenarios_summary.json").read_text())
    assert summary["provider_calls"] == 1
    assert summary["manifest"][0]["provider_usage"]["status"] == "invalid"


@pytest.mark.parametrize("mutation", ["denominator_shrink", "scenario_accounting"])
def test_iter202_extractor_reconstructs_stages_and_rejects_derived_shrinkage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str
) -> None:
    scenarios = load_script("run_iter200_scenarios.py", f"extract_stage_{mutation}")
    experiment = configure_scenarios(scenarios, monkeypatch, tmp_path)
    monkeypatch.setattr(scenarios.scen, "_key", lambda: "test-key")
    monkeypatch.setattr(
        scenarios.scen,
        "gen",
        lambda *_args: ("```python\nprint('RESULT=ok')\n```", {"total_tokens": 5}),
    )
    assert scenarios.main() == 0

    extract = load_script("extract_iter200_specs.py", f"extractor_{mutation}")
    monkeypatch.setattr(extract, "EXP", experiment)
    monkeypatch.setattr(extract, "SCEN", experiment / "proof/raw/scenarios")
    monkeypatch.setattr(extract, "OUT", experiment / "proof/raw/specs")
    monkeypatch.setattr(extract, "iter202_stages", scenarios)
    solve, scenario = extract.stage_summaries_for_specs(
        TEST_RUNTIME_MANIFEST_SHA256
    )
    assert solve["solutions"] == 1
    assert scenario["provider_calls"] == 1

    if mutation == "denominator_shrink":
        path = experiment / "proof/raw/solutions/solve_summary.json"
        changed = json.loads(path.read_text())
        changed["manifest"] = []
        changed["solutions"] = 0
        write_json(path, changed)
    else:
        path = experiment / "proof/raw/scenarios/scenarios_summary.json"
        changed = json.loads(path.read_text())
        changed["provider_calls"] = 0
        write_json(path, changed)

    with pytest.raises(scenarios.checkpoint.CheckpointError):
        extract.stage_summaries_for_specs(TEST_RUNTIME_MANIFEST_SHA256)
    assert not extract.OUT.exists()


def test_iter202_extractor_runtime_gate_precedes_swebench_and_stage_work(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extract = load_script("extract_iter200_specs.py", "extractor_runtime_gate")
    experiment = tmp_path / "iter202_natural_rate_scaled"
    observed: list[str] = []
    monkeypatch.setattr(extract, "EXP", experiment)
    monkeypatch.setattr(extract, "OUT", experiment / "proof/raw/specs")

    def reject_freeze() -> str:
        observed.append("freeze")
        raise extract.RuntimeFreezeError("stale manifest")

    monkeypatch.setattr(extract, "require_valid_runtime_freeze", reject_freeze)
    monkeypatch.setattr(
        extract.metadata,
        "version",
        lambda _name: (_ for _ in ()).throw(AssertionError("swebench inspected")),
    )
    monkeypatch.setattr(
        extract.iter202_stages,
        "reconstruct_stage_inputs_for_specs",
        lambda _sha: (_ for _ in ()).throw(AssertionError("stage evidence accepted")),
    )

    assert extract.main() == 2
    assert observed == ["freeze"]
    assert not extract.OUT.exists()


def test_iter200_path_keeps_legacy_noncheckpoint_behavior(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    solver = load_script("run_iter200_solver.py", "solver_iter200_legacy")
    experiment = configure_solver(
        solver,
        monkeypatch,
        tmp_path,
        experiment_name="iter200_natural_certified_yet_wrong_rate",
    )
    monkeypatch.setattr(solver.adv, "_key", lambda: "test-key")
    monkeypatch.setattr(
        solver.adv,
        "gen",
        lambda *_args: ("```python\nmodel_fix()\n```", {"total_tokens": 3}),
    )

    assert solver.main() == 0
    stage = experiment / "proof/raw/solutions"
    summary = json.loads((stage / "solve_summary.json").read_text())
    assert summary["provider_calls"] == 1
    assert "checkpoint_schema" not in summary
    assert not (stage / "provider_attempts").exists()
