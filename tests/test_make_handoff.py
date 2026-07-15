from __future__ import annotations

import importlib.util
from pathlib import Path
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


def test_handoff_status_filter_allows_only_its_own_regeneration() -> None:
    validate_handoff = load_validate_handoff_module()

    assert validate_handoff.worktree_changes_except_handoff(" M HANDOFF.md") == []
    assert validate_handoff.worktree_changes_except_handoff("M  HANDOFF.md") == []
    assert validate_handoff.worktree_changes_except_handoff(
        " M HANDOFF.md\n M README.md"
    ) == [" M README.md"]


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
    gate = tmp_path / "gate.md"
    gate.write_text("# Gate\n", encoding="utf-8")
    continuity = tmp_path / "CONTINUITY.md"
    continuity.write_text("Current gate:\n\n- `gate.md`\n", encoding="utf-8")
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

Active gate: `gate.md`
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(validate_handoff, "ROOT", tmp_path)
    monkeypatch.setattr(validate_handoff, "HANDOFF", handoff)
    monkeypatch.setattr(validate_handoff, "CONTINUITY", continuity)
    monkeypatch.setattr(validate_handoff, "current_branch", lambda: "actual-branch")
    monkeypatch.setattr(validate_handoff, "current_commit", lambda: "b" * 40)
    monkeypatch.setattr(validate_handoff, "git_is_ancestor", lambda *_args: True)
    monkeypatch.setattr(validate_handoff, "git_output", lambda _args: "")

    assert validate_handoff.main() == 1
    assert "source=declared-branch target=master actual=actual-branch" in (
        capsys.readouterr().out
    )
