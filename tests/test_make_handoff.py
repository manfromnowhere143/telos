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


def test_normalize_worktree_status_filters_handoff_self_write() -> None:
    make_handoff = load_make_handoff_module()

    assert make_handoff.normalize_worktree_status(" M HANDOFF.md") == "clean"
    assert make_handoff.normalize_worktree_status("M HANDOFF.md") == "clean"
    assert (
        make_handoff.normalize_worktree_status(" M README.md\n M HANDOFF.md")
        == " M README.md"
    )
