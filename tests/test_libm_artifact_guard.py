from __future__ import annotations

from pathlib import Path

from scripts import validate_libm_artifact_comparisons as guard

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/iter237"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_iter219_known_bad_fixture_reproduces_exact_wilson_bug() -> None:
    violations = guard.scan_source(
        _fixture("iter219_bit_exact_wilson.py.txt"),
        path="iter219_bit_exact_wilson.py",
    )

    assert len(violations) == 2
    assert {violation.code for violation in violations} == {"LIBM001"}
    assert {violation.line for violation in violations} == {7, 12}


def test_iter236_known_bad_fixture_reproduces_exact_artifact_bug() -> None:
    violations = guard.scan_source(
        _fixture("iter236_bit_exact_artifact.py.txt"),
        path="iter236_bit_exact_artifact.py",
    )

    assert len(violations) == 1
    assert violations[0].code == "LIBM002"
    assert violations[0].line == 19


def test_import_aliases_do_not_evade_the_guard() -> None:
    source = """
from math import sqrt as platform_root

def check(stored):
    rebuilt = platform_root(2.0)
    return stored == rebuilt
"""

    violations = guard.scan_source(source, path="aliased.py")

    assert [violation.code for violation in violations] == ["LIBM001"]


def test_approved_tolerant_comparators_are_taint_barriers() -> None:
    source = """
import math
from telos.json_compare import compare_json

def check(stored):
    rebuilt = {"root": math.sqrt(2.0)}
    return compare_json(stored, rebuilt) == []
"""

    assert guard.scan_source(source, path="tolerant.py") == []


def test_unrelated_exact_fields_remain_allowed_in_libm_module() -> None:
    source = """
import math

def build(n):
    return {"n": n, "root": math.sqrt(n)}

def check_schema(document):
    return document["schema"] == "example.v1"
"""

    assert guard.scan_source(source, path="exact_fields.py") == []


def test_every_active_repository_python_file_passes() -> None:
    paths = guard.active_python_paths(ROOT)

    assert paths
    assert ROOT / "scripts/build_iter236_transfer_analysis.py" in paths
    assert ROOT / "scripts/adjudicate_iter231.py" in paths
    assert guard.scan_repository(ROOT) == []
