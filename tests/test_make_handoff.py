from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess

import pytest


def load_make_handoff_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "make_handoff.py"
    spec = importlib.util.spec_from_file_location("make_handoff", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validate_handoff_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "validate_handoff.py"
    spec = importlib.util.spec_from_file_location("validate_handoff", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalize_worktree_status_filters_handoff_self_write() -> None:
    make_handoff = load_make_handoff_module()

    assert make_handoff.normalize_worktree_status(" M HANDOFF.md") == "clean"
    assert make_handoff.normalize_worktree_status("M HANDOFF.md") == "clean"
    assert (
        make_handoff.normalize_worktree_status(" M README.md\n M HANDOFF.md")
        == " M README.md"
    )
    assert make_handoff.normalize_worktree_status(" M CONTINUITY.md") == (
        " M CONTINUITY.md"
    )


def test_repository_banner_is_explicit_and_self_contained() -> None:
    make_handoff = load_make_handoff_module()

    banner = make_handoff.repository_banner()
    assert banner == (
        "TELOS is a standalone repository at "
        "`/Users/danielwahnich/workspace/telos`. "
        "Run every TELOS command from this repository."
    )
    assert ("a" + "web") not in banner.casefold()


def test_active_and_frozen_upstream_gates_are_independently_bound(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_make_handoff_module()
    monkeypatch.chdir(tmp_path)
    active = "experiments/iter203/HYPOTHESIS.md"
    frozen = "experiments/iter202/HYPOTHESIS.md"
    for gate in (active, frozen):
        path = tmp_path / gate
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Gate\n", encoding="utf-8")
    (tmp_path / "CONTINUITY.md").write_text(
        f"Current gate:\n\n- `{frozen}`\n", encoding="utf-8"
    )
    contract = tmp_path / "mission" / "loop.json"
    contract.parent.mkdir()
    contract.write_text(
        json.dumps({"active_gate": active, "frozen_upstream_gate": frozen}),
        encoding="utf-8",
    )

    assert make_handoff.frozen_upstream_gate() == frozen
    assert make_handoff.active_gate() == active

    contract.write_text(
        json.dumps({"active_gate": active, "frozen_upstream_gate": active}),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="frozen upstream gates disagree"):
        make_handoff.active_gate()


def test_operational_handoff_evidence_is_pinned_to_published_runs() -> None:
    make_handoff = load_make_handoff_module()

    assert make_handoff.HARDENING_PULL_REQUEST == 4
    assert (
        make_handoff.HARDENING_MERGE_COMMIT
        == "8b8809ed6b358d16eb08fe38f0f2edf4a284af0e"
    )
    assert make_handoff.PRIMARY_CI_RUN_ID == "29454446264"
    assert (
        make_handoff.NODE24_BACKFILL_SOURCE_COMMIT
        == "b4a565d0f0bb61cff460ea4faa51f58e75a2c2fe"
    )
    assert make_handoff.NODE24_BACKFILL_RUN_ID == "29452243832"


def test_rendered_handoff_records_the_exact_ordered_operational_gate(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_make_handoff_module()
    source_commit = "b" * 40
    source_branch = "agent/iter203-safety-recovery"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(make_handoff, "current_branch", lambda: source_branch)
    monkeypatch.setattr(
        make_handoff,
        "source_provenance",
        lambda _branch: (source_branch, source_commit),
    )
    monkeypatch.setattr(make_handoff, "run", lambda _args: "")
    monkeypatch.setattr(
        make_handoff,
        "active_gate",
        lambda: "experiments/iter203_iter202_safety_recovery/HYPOTHESIS.md",
    )
    monkeypatch.setattr(
        make_handoff,
        "frozen_upstream_gate",
        lambda: "experiments/iter202_natural_rate_scaled/HYPOTHESIS.md",
    )
    monkeypatch.setattr(make_handoff, "experiment_status", lambda _gate: [])

    make_handoff.main()
    handoff = (tmp_path / "HANDOFF.md").read_text(encoding="utf-8")

    for evidence in (
        "8b8809ed6b358d16eb08fe38f0f2edf4a284af0e",
        "29454446264",
        "b4a565d0f0bb61cff460ea4faa51f58e75a2c2fe",
        "29452243832",
        "governed credential readiness was verified",
        "`53/53` solver calls",
        "`39/39` eligible scenario calls",
        "`50` model patches",
        "`38` extracted scenario programs",
        "admitted `29` programs and rejected `9` with `21` findings",
        "Zero scenario execution and zero official-harness certification execution occurred",
        "scenario-safety protocol/execution null",
        "bridge and all-`50` certification specs are ready",
        "A second dispatch for the same commit is forbidden",
        'gh workflow run iter203-execute.yml --ref master -f expected_primary_sha="$HEAD_SHA"',
        'gh run rerun "$RUN_ID"',
        "scripts/collect_iter203_execution.py check",
        "scripts/adjudicate_iter203_safety_recovery.py",
        "scripts/run_iter203_safety_recovery_blind_judge.py",
    ):
        assert evidence in handoff

    assert "Active gate: `experiments/iter203_iter202_safety_recovery/HYPOTHESIS.md`" in handoff
    assert (
        "Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: "
        "`experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`"
    ) in handoff
    assert re.search(r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET)\b", handoff) is None

    next_action_start = handoff.index("- Next action:")
    next_action_end = handoff.index("- Autonomous goal-tracking note:")
    next_action = " ".join(handoff[next_action_start:next_action_end].split())
    ordered_markers = (
        "review the iter203 source",
        "commit the bounded recovery changes",
        "pull request",
        "green primary-branch CI",
        "iter203 execution workflow",
    )
    assert [next_action.index(marker) for marker in ordered_markers] == sorted(
        next_action.index(marker) for marker in ordered_markers
    )
    assert "Never dispatch the frozen iter202 workflow" in next_action
    dispatch = handoff[handoff.index("## Exact Authorized Iter203 Dispatch") :]
    assert dispatch.index("git switch master") < dispatch.index(
        "gh workflow run iter203-execute.yml"
    )
    assert dispatch.index('gh run watch "$RUN_ID" --exit-status') < dispatch.index(
        'gh run rerun "$RUN_ID"'
    )
    assert dispatch.index('gh run download "$RUN_ID"') < dispatch.index(
        "scripts/collect_iter203_execution.py check"
    )
    assert dispatch.index("scripts/collect_iter203_execution.py check") < dispatch.index(
        "scripts/adjudicate_iter203_safety_recovery.py"
    )
    assert dispatch.index("scripts/adjudicate_iter203_safety_recovery.py") < dispatch.index(
        "scripts/run_iter203_safety_recovery_blind_judge.py"
    )
    assert dispatch.count('RUN_COUNT="$(gh run list') == 3
    assert dispatch.count('RUN_ID="$(gh run list') == 4
    assert dispatch.count("git pull --ff-only origin master") == 3
    assert dispatch.count('test -z "$(git status --porcelain)"') == 3
    assert dispatch.count('test "$HEAD_SHA" = "$(git rev-parse origin/master)"') == 3
    assert 'test "$RUN_COUNT" -eq 1' in dispatch
    assert '"completed success"' in dispatch
    assert ("a" + "web") not in handoff.casefold()


def test_handoff_status_filter_allows_only_its_own_regeneration() -> None:
    validate_handoff = load_validate_handoff_module()

    assert validate_handoff.worktree_changes_except_handoff(" M HANDOFF.md") == []
    assert validate_handoff.worktree_changes_except_handoff("M  HANDOFF.md") == []
    assert validate_handoff.worktree_changes_except_handoff(
        " M HANDOFF.md\n M README.md"
    ) == [" M README.md"]


def test_handoff_recovery_content_rejects_stale_or_identifying_credential_text() -> None:
    validate_handoff = load_validate_handoff_module()
    bounded = "\n".join(validate_handoff.REQUIRED_RECOVERY_FACTS)

    assert validate_handoff.recovery_content_failures(bounded) == []
    assert "HANDOFF.md names a credential variable" in (
        validate_handoff.recovery_content_failures(bounded + "\nPROVIDER_API_KEY")
    )
    assert "HANDOFF.md describes credentials as unavailable" in (
        validate_handoff.recovery_content_failures(bounded + "\nCredentials are missing.")
    )
    unsafe_dispatch = bounded.replace(
        "Never dispatch the frozen iter202 workflow",
        "Dispatch the frozen iter202 workflow now.",
    )
    assert "HANDOFF.md is missing bounded recovery fact: Never dispatch the frozen iter202 workflow" in (
        validate_handoff.recovery_content_failures(unsafe_dispatch)
    )


def test_handoff_snapshot_parser_is_exact() -> None:
    validate_handoff = load_validate_handoff_module()

    assert validate_handoff.declared_worktree_changes(
        "# Handoff\n\nWorking tree:\n\n```text\nclean\n```\n"
    ) == []
    assert validate_handoff.declared_worktree_changes(
        "# Handoff\n\nWorking tree:\n\n```text\n M README.md\n?? new.txt\n```\n"
    ) == [" M README.md", "?? new.txt"]
    duplicate = (
        "Working tree:\n\n```text\nclean\n```\n\n"
        "Working tree:\n\n```text\nclean\n```\n"
    )
    with pytest.raises(ValueError, match="exactly one working-tree snapshot"):
        validate_handoff.declared_worktree_changes(duplicate)


def test_handoff_generator_fails_closed_on_git_error(monkeypatch) -> None:
    make_handoff = load_make_handoff_module()

    def failed_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: no repository")

    monkeypatch.setattr(make_handoff.subprocess, "run", failed_run)
    with pytest.raises(RuntimeError, match="exit 128.*fatal: no repository"):
        make_handoff.run(["git", "status", "--short"])


def test_handoff_generator_rejects_detached_head(monkeypatch) -> None:
    make_handoff = load_make_handoff_module()
    monkeypatch.setattr(make_handoff, "run", lambda _args: "HEAD")

    with pytest.raises(RuntimeError, match="cannot generate handoff"):
        make_handoff.current_branch()


def test_handoff_generator_freezes_feature_source_and_preserves_it_on_master(
    tmp_path: Path, monkeypatch
) -> None:
    make_handoff = load_make_handoff_module()
    source_commit = "a" * 40
    monkeypatch.setattr(make_handoff, "current_commit", lambda: source_commit)
    assert make_handoff.source_provenance("agent/research-gate") == (
        "agent/research-gate",
        source_commit,
    )

    monkeypatch.chdir(tmp_path)
    (tmp_path / "HANDOFF.md").write_text(
        "source_branch: agent/research-gate\n"
        f"source_commit: {source_commit}\n"
        "publication_target: master\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        make_handoff.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "", ""),
    )
    assert make_handoff.source_provenance("master") == (
        "agent/research-gate",
        source_commit,
    )

    monkeypatch.setattr(
        make_handoff.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", ""),
    )
    with pytest.raises(RuntimeError, match="not an ancestor"):
        make_handoff.source_provenance("master")


def test_declared_branch_parser_is_exact() -> None:
    validate_handoff = load_validate_handoff_module()
    source_commit = "a" * 40
    handoff = """# Handoff

## Repository State

```text
source_branch: agent/research-gate
source_commit: SOURCE_COMMIT
publication_target: master
```
""".replace("SOURCE_COMMIT", source_commit)

    assert validate_handoff.declared_branch(handoff) == "agent/research-gate"
    assert validate_handoff.declared_repository_state(handoff) == {
        "source_branch": "agent/research-gate",
        "source_commit": source_commit,
        "publication_target": "master",
    }
    with pytest.raises(ValueError, match="non-master feature branch"):
        validate_handoff.declared_repository_state(
            handoff.replace("agent/research-gate", "master")
        )
    with pytest.raises(ValueError, match="full lowercase Git commit"):
        validate_handoff.declared_repository_state(
            handoff.replace(source_commit, "a" * 39)
        )
    with pytest.raises(ValueError, match="publication_target must be master"):
        validate_handoff.declared_repository_state(
            handoff.replace("publication_target: master", "publication_target: main")
        )


def test_handoff_validator_fails_closed_on_git_error(monkeypatch) -> None:
    validate_handoff = load_validate_handoff_module()

    def failed_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: no repository")

    monkeypatch.setattr(validate_handoff.subprocess, "run", failed_run)
    with pytest.raises(RuntimeError, match="exit 128.*fatal: no repository"):
        validate_handoff.git_output(["git", "status", "--short"])


def test_handoff_ancestry_distinguishes_miss_from_git_failure(monkeypatch) -> None:
    validate_handoff = load_validate_handoff_module()

    monkeypatch.setattr(
        validate_handoff.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", ""),
    )
    assert validate_handoff.git_is_ancestor("a" * 40, "b" * 40) is False

    monkeypatch.setattr(
        validate_handoff.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 128, "", "fatal: bad object"
        ),
    )
    with pytest.raises(RuntimeError, match="exit 128.*fatal: bad object"):
        validate_handoff.git_is_ancestor("a" * 40, "b" * 40)


def test_handoff_validator_uses_github_source_branch_on_detached_head(monkeypatch) -> None:
    validate_handoff = load_validate_handoff_module()
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "HEAD")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", "agent/research-gate")
    monkeypatch.setenv("GITHUB_REF_NAME", "123/merge")

    assert validate_handoff.current_branch() == "agent/research-gate"


def test_handoff_validator_uses_github_push_branch_and_rejects_local_detachment(
    monkeypatch,
) -> None:
    validate_handoff = load_validate_handoff_module()
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "HEAD")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    monkeypatch.setenv("GITHUB_REF_NAME", "master")
    assert validate_handoff.current_branch() == "master"

    monkeypatch.delenv("GITHUB_ACTIONS")
    with pytest.raises(RuntimeError, match="cannot verify handoff branch"):
        validate_handoff.current_branch()


def test_publication_lineage_accepts_only_source_or_master_with_ancestry(
    monkeypatch,
) -> None:
    validate_handoff = load_validate_handoff_module()
    source_commit = "a" * 40
    head_commit = "b" * 40
    state = {
        "source_branch": "agent/research-gate",
        "source_commit": source_commit,
        "publication_target": "master",
    }
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "")
    monkeypatch.setattr(validate_handoff, "git_is_ancestor", lambda *_args: True)

    assert validate_handoff.publication_lineage_failures(
        state, "agent/research-gate", head_commit
    ) == []
    assert validate_handoff.publication_lineage_failures(
        state, "master", head_commit
    ) == []
    assert validate_handoff.publication_lineage_failures(
        state, "agent/unrelated", head_commit
    ) == [
        "HANDOFF.md branch is outside its publication lineage: "
        "source=agent/research-gate target=master actual=agent/unrelated"
    ]

    monkeypatch.setattr(validate_handoff, "git_is_ancestor", lambda *_args: False)
    assert validate_handoff.publication_lineage_failures(
        state, "master", head_commit
    ) == [
        "HANDOFF.md source_commit is not an ancestor of repository HEAD: "
        f"source_commit={source_commit} HEAD={head_commit}"
    ]


def test_handoff_validator_rejects_declared_branch_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    validate_handoff = load_validate_handoff_module()
    gate = tmp_path / "active.md"
    gate.write_text("# Active gate\n", encoding="utf-8")
    frozen_gate = tmp_path / "frozen.md"
    frozen_gate.write_text("# Frozen gate\n", encoding="utf-8")
    continuity = tmp_path / "CONTINUITY.md"
    continuity.write_text("Current gate:\n\n- `frozen.md`\n", encoding="utf-8")
    contract = tmp_path / "mission" / "loop.json"
    contract.parent.mkdir()
    contract.write_text(
        json.dumps({"active_gate": "active.md", "frozen_upstream_gate": "frozen.md"}),
        encoding="utf-8",
    )
    facts = "\n".join(validate_handoff.REQUIRED_RECOVERY_FACTS)
    handoff = tmp_path / "HANDOFF.md"
    handoff.write_text(
        f"""# Handoff

{validate_handoff.REPOSITORY_DECLARATION}

## Repository State

```text
source_branch: declared-branch
source_commit: {"a" * 40}
publication_target: master
```

Working tree:

```text
clean
```

Active gate: `active.md`
Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `frozen.md`

{facts}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(validate_handoff, "ROOT", tmp_path)
    monkeypatch.setattr(validate_handoff, "HANDOFF", handoff)
    monkeypatch.setattr(validate_handoff, "CONTINUITY", continuity)
    monkeypatch.setattr(validate_handoff, "MISSION_CONTRACT", contract)
    monkeypatch.setattr(validate_handoff, "current_branch", lambda: "actual-branch")
    monkeypatch.setattr(validate_handoff, "current_commit", lambda: "b" * 40)
    monkeypatch.setattr(validate_handoff, "git_is_ancestor", lambda *_args: True)
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "")

    assert validate_handoff.main() == 1
    assert "source=declared-branch target=master actual=actual-branch" in (
        capsys.readouterr().out
    )
