from __future__ import annotations

import importlib.util
from pathlib import Path


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
