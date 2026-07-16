from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import shutil

import pytest

from scripts import build_iter203_safety_recovery as recovery


@pytest.fixture(scope="module")
def bundle() -> dict:
    return recovery.build_artifacts()


def redirect_outputs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    raw = tmp_path / "proof/raw"
    bridge = raw / "safety_recovery_bridge"
    solutions = raw / "solutions"
    scenarios = raw / "scenarios"
    monkeypatch.setattr(recovery, "RAW", raw)
    monkeypatch.setattr(recovery, "BRIDGE", bridge)
    monkeypatch.setattr(recovery, "PROJECTED_SOLUTIONS", solutions)
    monkeypatch.setattr(recovery, "PROJECTED_SCENARIOS", scenarios)
    monkeypatch.setattr(recovery, "UPSTREAM_INVENTORY", bridge / "upstream_inventory.json")
    monkeypatch.setattr(recovery, "SCENARIO_DISPOSITION", bridge / "scenario_disposition.json")
    monkeypatch.setattr(recovery, "SAFE_SCENARIO_INDEX", bridge / "safe_scenario_index.json")
    monkeypatch.setattr(
        recovery,
        "SOLUTION_PROJECTION_INDEX",
        bridge / "solution_projection_index.json",
    )


def test_uniform_frozen_classifier_and_expected_dispositions() -> None:
    classifier, extractor = recovery._load_upstream_functions()
    calls: list[str] = []

    def observed(source: str) -> list[str]:
        calls.append(source)
        return classifier(source)

    built = recovery.build_artifacts(classifier=observed, extractor=extractor)
    disposition = built["bridge_documents"]["scenario_disposition.json"]
    assert len(calls) == recovery.EXPECTED_GENERATED_SCENARIOS == 38
    assert disposition["counts"] == {
        "generated_scenarios": 38,
        "no_scenario": 1,
        "safe_scenarios": 29,
        "safety_findings": 21,
        "scenario_attempts": 39,
        "unsafe_scenarios": 9,
    }
    assert Counter(row["status"] for row in disposition["dispositions"]) == {
        "safe_scenario": 29,
        "unsafe_scenario": 9,
        "no_scenario": 1,
    }
    assert sum(
        row["safety_finding_count"] for row in disposition["dispositions"]
    ) == 21
    assert all(
        finding["code"]
        in {
            "absolute_or_parent_traversal_path_literal",
            "call_through_unsafe_import_alias",
            "unsafe_dynamic_or_builtin_call",
            "unsafe_import_alias",
            "unsafe_import_root",
            "unsafe_process_network_or_filesystem_call",
        }
        for row in disposition["dispositions"]
        for finding in row["safety_findings"]
    )


def test_bridge_inventories_exact_upstream_and_projection(bundle: dict) -> None:
    documents = bundle["bridge_documents"]
    inventory = documents["upstream_inventory.json"]
    assert inventory["upstream_source_commit"] == recovery.UPSTREAM_SOURCE_COMMIT
    assert (
        inventory["upstream_runtime_manifest_sha256"]
        == recovery.UPSTREAM_RUNTIME_MANIFEST_SHA256
    )
    assert len(inventory["files"]) == 324
    assert inventory["counts"] == {
        "gold_patches": 50,
        "model_patches": 50,
        "scenario_finished_checkpoints": 39,
        "scenario_scripts": 38,
        "scenario_stage_files": 117,
        "scenario_started_checkpoints": 39,
        "solution_finished_checkpoints": 53,
        "solution_stage_files": 207,
        "solution_started_checkpoints": 53,
    }
    assert documents["safe_scenario_index.json"]["count"] == 29
    assert documents["solution_projection_index.json"]["count"] == 50
    assert len(bundle["safe_payloads"]) == 29
    assert len(bundle["solution_payloads"]) == 100


def test_projected_summary_preserves_distinct_missingness_without_unsafe_bytes(
    bundle: dict,
) -> None:
    summary = bundle["projected_scenario_summary"]
    assert summary["schema_version"] == recovery.PROJECTED_SCENARIO_SCHEMA
    assert Counter(row["status"] for row in summary["manifest"]) == {
        "scenario": 29,
        "unsafe_scenario": 9,
        "no_scenario": 1,
    }
    disposition = bundle["bridge_documents"]["scenario_disposition.json"]
    unsafe = {
        row["instance_id"]
        for row in disposition["dispositions"]
        if row["status"] == "unsafe_scenario"
    }
    assert unsafe.isdisjoint(bundle["safe_payloads"])
    assert all(
        row["safe_copy_path"] is None
        for row in disposition["dispositions"]
        if row["status"] != "safe_scenario"
    )


def test_write_check_is_deterministic_and_copies_exact_bytes(
    bundle: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    redirect_outputs(monkeypatch, tmp_path)
    recovery.write_artifacts(bundle)
    first = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.rglob("*"))
        if path.is_file()
    }
    recovery.write_artifacts(bundle)
    recovery.check_artifacts(bundle)
    second = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.rglob("*"))
        if path.is_file()
    }
    assert second == first
    assert len(list(recovery.PROJECTED_SOLUTIONS.glob("*.model.patch"))) == 50
    assert len(list(recovery.PROJECTED_SOLUTIONS.glob("*.gold.patch"))) == 50
    assert len(list(recovery.PROJECTED_SCENARIOS.glob("*.scenario.py"))) == 29

    solution_index = bundle["bridge_documents"]["solution_projection_index.json"]
    for row in solution_index["solutions"]:
        assert (recovery.ROOT / row["upstream_model_path"]).read_bytes() == (
            recovery.PROJECTED_SOLUTIONS / Path(row["model_path"]).name
        ).read_bytes()
        assert (recovery.ROOT / row["upstream_gold_path"]).read_bytes() == (
            recovery.PROJECTED_SOLUTIONS / Path(row["gold_path"]).name
        ).read_bytes()


def test_check_rejects_extra_projection_file(
    bundle: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    redirect_outputs(monkeypatch, tmp_path)
    recovery.write_artifacts(bundle)
    (recovery.PROJECTED_SCENARIOS / "unexpected.scenario.py").write_text(
        'print("RESULT=unexpected")\n'
    )
    with pytest.raises(recovery.RecoveryError, match="file set mismatch"):
        recovery.check_artifacts(bundle)


def test_check_rejects_symlinked_projection_file(
    bundle: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    redirect_outputs(monkeypatch, tmp_path)
    recovery.write_artifacts(bundle)
    scenario = next(recovery.PROJECTED_SCENARIOS.glob("*.scenario.py"))
    target = tmp_path / "outside.py"
    target.write_bytes(scenario.read_bytes())
    scenario.unlink()
    scenario.symlink_to(target)
    with pytest.raises(recovery.RecoveryError, match="symlinked"):
        recovery.check_artifacts(bundle)


def test_strict_json_rejects_duplicate_and_nonfinite(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"value":1,"value":2}\n')
    with pytest.raises(recovery.RecoveryError, match="duplicate JSON key"):
        recovery.load_json_strict(duplicate)

    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"value":NaN}\n')
    with pytest.raises(recovery.RecoveryError, match="non-finite JSON constant"):
        recovery.load_json_strict(nonfinite)


def test_altered_upstream_runtime_manifest_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    altered = tmp_path / "runtime_manifest.json"
    altered.write_bytes(recovery.UPSTREAM_RUNTIME_MANIFEST.read_bytes() + b" ")
    monkeypatch.setattr(recovery, "UPSTREAM_RUNTIME_MANIFEST", altered)
    with pytest.raises(recovery.RecoveryError, match="runtime manifest SHA-256 mismatch"):
        recovery._validate_upstream_source()


def test_altered_checkpoint_bytes_fail_closed(tmp_path: Path) -> None:
    attempts = tmp_path / "provider_attempts"
    shutil.copytree(recovery.UPSTREAM_SCENARIOS / "provider_attempts", attempts)
    started = sorted(attempts.glob("*.started.json"))[0]
    document = json.loads(started.read_text())
    document["runtime_manifest_sha256"] = "0" * 64
    started.write_bytes(recovery.canonical_json_bytes(document))
    summary = recovery.load_json_strict(
        recovery.UPSTREAM_SCENARIOS / "scenarios_summary.json"
    )
    ids = [row["instance_id"] for row in summary["manifest"]]
    with pytest.raises(recovery.RecoveryError, match="malformed scenario_generation started"):
        recovery._attempt_pairs(
            attempts,
            phase="scenario_generation",
            expected_ids=ids,
        )


def test_committed_projection_check_passes(bundle: dict) -> None:
    recovery.check_artifacts(bundle)
    disposition_path = recovery.SCENARIO_DISPOSITION
    assert json.loads(disposition_path.read_text())["counts"]["unsafe_scenarios"] == 9
