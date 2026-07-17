from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_iter223_scenario_safety import scenario_ast_errors

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / "experiments/iter223_natural_rate_safety_aware/proof/raw/cohort.json"
_R = 'print("RESULT=1")\n'


def _e(src: str) -> list[str]:
    return scenario_ast_errors(src + _R)


def test_in_class_domain_libraries_are_admitted() -> None:
    assert _e("from docutils import nodes\nx = nodes\n") == []
    assert _e("from mpl_toolkits.axes_grid1.inset_locator import inset_axes\nx = inset_axes\n") == []


def test_pure_stdlib_test_idioms_are_admitted() -> None:
    assert _e("from types import SimpleNamespace\nr = SimpleNamespace(a=1)\n") == []
    assert _e("from uuid import UUID\nu = UUID('12345678-1234-5678-1234-567812345678')\n") == []
    assert _e('v = getattr(object(), "real", None)\n') == []


def test_real_dangers_stay_rejected() -> None:
    for bad in ("import os\nos.system('x')\n", "import sys\ns = sys\n", "import subprocess\n",
                "import tempfile\n", "import socket\n", "eval('1')\n", "exec('1')\n",
                "open('/etc/passwd')\n", "n='x'\nv = getattr(object(), n)\n", "__import__('os')\n"):
        assert _e(bad), bad


def test_forbidden_filesystem_attribute_calls_stay_rejected() -> None:
    assert _e("import pathlib\npathlib.Path('x').mkdir()\n")


def test_cohort_reuses_real_evidence_with_honest_split() -> None:
    c = json.loads(COHORT.read_text())
    assert c["solve_patches"] == 53
    assert c["safe_witnessable_scenarios"] == 36
    assert c["excluded_unsafe_count"] == 2
    excluded = {e["instance_id"] for e in c["excluded_unsafe"]}
    assert excluded == {"pytest-dev__pytest-7982", "sympy__sympy-19346"}
    for e in c["excluded_unsafe"]:
        assert e["unsafe_reason"]


def test_the_two_excluded_are_genuinely_unsafe_and_the_safe_ones_pass() -> None:
    scen = ROOT / "experiments/iter202_natural_rate_scaled/proof/raw/scenarios"
    for iid in ("pytest-dev__pytest-7982", "sympy__sympy-19346"):
        assert scenario_ast_errors((scen / f"{iid}.scenario.py").read_text()), iid
    c = json.loads(COHORT.read_text())
    kept = ROOT / "experiments/iter223_natural_rate_safety_aware/proof/raw/scenarios"
    assert len(list(kept.glob("*.scenario.py"))) == c["safe_witnessable_scenarios"]
