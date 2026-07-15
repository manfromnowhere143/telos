from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_guard():
    path = ROOT / "scripts/validate_json.py"
    spec = importlib.util.spec_from_file_location("validate_json_guard", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_strict_json_loader_accepts_unique_keys(tmp_path: Path) -> None:
    guard = load_guard()
    path = tmp_path / "valid.json"
    path.write_text('{"outer":{"left":1,"right":2}}\n')

    assert guard.load_strict_json(path) == {"outer": {"left": 1, "right": 2}}


def test_strict_json_loader_rejects_nested_duplicate_key(tmp_path: Path) -> None:
    guard = load_guard()
    path = tmp_path / "duplicate.json"
    path.write_text('{"outer":{"value":1,"value":2}}\n')

    with pytest.raises(ValueError, match="duplicate object key: 'value'"):
        guard.load_strict_json(path)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_strict_json_loader_rejects_nonfinite_constants(
    tmp_path: Path, constant: str
) -> None:
    guard = load_guard()
    path = tmp_path / "nonfinite.json"
    path.write_text(f'{{"value":{constant}}}\n')

    with pytest.raises(ValueError, match=f"non-finite JSON constant: {constant}"):
        guard.load_strict_json(path)
