from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    path = ROOT / "scripts/build_iter200_solve_targets.py"
    spec = importlib.util.spec_from_file_location("iter200_target_builder", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_iter200_frozen_target_manifest_reproduces_exactly() -> None:
    builder = load_builder()
    committed = json.loads(builder.OUT.read_text())

    assert builder.build_manifest() == committed
    assert builder.check_manifest()
    assert committed["eligible_count"] == 200
    assert committed["eligible_repo_count"] == 9
    assert committed["count"] == 39
    assert committed["excluded_target_union_count"] == 66
    assert [row["path"] for row in committed["implementation_sources"]] == [
        "scripts/build_iter200_solve_targets.py",
        "scripts/run_iter200_solver.py",
        "scripts/run_certified_resolved_adversary.py",
    ]
    assert len({row["instance_id"] for row in committed["targets"]}) == 39


def test_iter200_selection_is_lexicographic_and_capped() -> None:
    builder = load_builder()
    manifest = builder.build_manifest()
    targets = manifest["targets"]
    repo_order = [row["repo"] for row in targets]

    assert repo_order == sorted(repo_order)
    for repo in sorted(set(repo_order)):
        ids = [row["instance_id"] for row in targets if row["repo"] == repo]
        assert ids == sorted(ids)
        assert len(ids) <= builder.CAP_PER_REPO


def test_iter200_check_rejects_manifest_drift(tmp_path: Path) -> None:
    builder = load_builder()
    drifted = builder.build_manifest()
    drifted["targets"] = list(reversed(drifted["targets"]))
    path = tmp_path / "solve_targets.json"
    path.write_text(json.dumps(drifted))

    assert builder.check_manifest(path) is False
    builder.OUT = path
    assert builder.main(["--check"]) == 1
