from __future__ import annotations

from scripts.measure_iter219_temporal_yield import (
    build_derangement,
    changed_old_lines,
    enclosing_symbols,
    is_source_path,
    is_test_path,
    permutation_key,
    extract_test_function_identifiers,
)

MIXED_PATCH = """diff --git a/pkg/core.py b/pkg/core.py
--- a/pkg/core.py
+++ b/pkg/core.py
@@ -10,7 +10,8 @@ class Widget:
     def render(self):
-        return self.a
+        return self.b
+        # extra

@@ -40,0 +41,2 @@ def helper():
+def brand_new():
+    pass
"""

SOURCE = """
class Widget:
    def render(self):
        x = 1
        return x

    def other(self):
        pass

def free_func():
    return 2
"""

TESTS = """
import pytest

@pytest.mark.parametrize("x", [1])
def test_render_regression(x):
    w = Widget()
    assert w.render() == 1

class TestGroup:
    def test_other_thing(self):
        assert helper_symbol()

def not_a_test():
    assert render()
"""


def test_pure_insertion_hunk_never_attributes_the_untouched_preceding_line() -> None:
    # ``@@ -40,0 +41,2 @@`` inserts after original line 40.  Line 39 is untouched and
    # must never enter the symbol set; attributing it would inflate the measured yield.
    assert changed_old_lines(MIXED_PATCH) == {"pkg/core.py": {11, 40}}


def test_deleted_files_contribute_no_changed_lines() -> None:
    patch = (
        "--- a/pkg/gone.py\n"
        "+++ /dev/null\n"
        "@@ -1,3 +0,0 @@\n"
        "-a = 1\n"
        "-b = 2\n"
        "-c = 3\n"
    )
    assert changed_old_lines(patch) == {}


def test_changed_lines_are_tracked_per_file() -> None:
    patch = (
        "--- a/x.py\n"
        "+++ b/x.py\n"
        "@@ -5,2 +5,2 @@\n"
        "-old\n"
        "+new\n"
        "--- a/tests/test_x.py\n"
        "+++ b/tests/test_x.py\n"
        "@@ -1,1 +1,2 @@\n"
        " keep\n"
        "+added\n"
    )
    assert changed_old_lines(patch) == {"x.py": {5}, "tests/test_x.py": {1}}


def test_enclosing_symbol_is_the_innermost_definition() -> None:
    assert enclosing_symbols(SOURCE, {4}) == {"render"}
    assert enclosing_symbols(SOURCE, {11}) == {"free_func"}
    assert enclosing_symbols(SOURCE, {2}) == {"Widget"}


def test_module_level_lines_contribute_no_symbol() -> None:
    assert enclosing_symbols("x = 1\ny = 2\n", {1, 2}) == set()


def test_only_test_prefixed_functions_are_collected_with_decorator_text() -> None:
    collected = extract_test_function_identifiers(TESTS)

    assert sorted(collected) == ["TestGroup.test_other_thing", "test_render_regression"]
    assert "not_a_test" not in collected
    assert "render" in collected["test_render_regression"]
    assert "parametrize" in collected["test_render_regression"]
    assert "helper_symbol" in collected["TestGroup.test_other_thing"]


def test_unparseable_test_module_yields_no_functions() -> None:
    assert extract_test_function_identifiers("def test_x( :\n") == {}


def test_frozen_test_path_convention() -> None:
    for path in (
        "tests/test_a.py",
        "pkg/tests/foo.py",
        "a/b_test.py",
        "conftest.py",
        "pkg/testing/x.py",
    ):
        assert is_test_path(path), path
        assert not is_source_path(path), path

    assert is_source_path("pkg/core.py")
    assert not is_test_path("pkg/core.py")
    assert not is_source_path("README.md")


def test_permutation_key_is_deterministic_and_salt_bound() -> None:
    assert permutation_key(1) == permutation_key(1)
    assert permutation_key(1) != permutation_key(2)


def test_derangement_is_a_bijection_without_fixed_points_or_same_repo_pairs() -> None:
    ids = [f"i{n}" for n in range(10)]
    repo_of = {f"i{n}": ("A" if n < 5 else "B") for n in range(10)}

    pairing = build_derangement(ids, repo_of)

    assert sorted(pairing.values()) == sorted(ids)
    for source, dest in pairing.items():
        assert dest != source
        assert repo_of[dest] != repo_of[source]


def test_derangement_is_stable_across_calls() -> None:
    ids = [f"i{n}" for n in range(12)]
    repo_of = {f"i{n}": ("A" if n % 3 == 0 else "B" if n % 3 == 1 else "C") for n in range(12)}

    assert build_derangement(ids, repo_of) == build_derangement(ids, repo_of)


# --------------------------------------------------------------------------- #
# Positive controls: every guard must FAIL on a broken input, or it guards nothing.
# --------------------------------------------------------------------------- #

import copy  # noqa: E402

import pytest  # noqa: E402

from scripts import validate_iter219_temporal_consequence_test_yield as guard  # noqa: E402
from telos.tcp1 import exact_one_sided_mcnemar, wilson_interval  # noqa: E402


def _synthetic_report() -> dict:
    rows = [
        {"instance_id": "a__1", "repo": "org/a", "control_partner": "b__1", "real": True,
         "control": False, "backward_control": False,
         "symbol_count": 2, "forward_added_tests": 4, "backward_added_tests": 3},
        {"instance_id": "b__1", "repo": "org/b", "control_partner": "a__1", "real": False,
         "control": False, "backward_control": False,
         "symbol_count": 1, "forward_added_tests": 2, "backward_added_tests": 1},
    ]
    pairs = [(r["real"], r["control"]) for r in rows]
    back_pairs = [(r["real"], r["backward_control"]) for r in rows]
    block = {
        "n": 2,
        "real_hits": 1,
        "real_yield": 0.5,
        "real_wilson_95": list(wilson_interval(1, 2)),
        "control_hits": 0,
        "control_yield": 0.0,
        "control_wilson_95": list(wilson_interval(0, 2)),
        "yield_difference": 0.5,
        "mcnemar_real_gt_control": exact_one_sided_mcnemar(pairs),
        "backward_control_hits": 0,
        "backward_control_yield": 0.0,
        "backward_control_wilson_95": list(wilson_interval(0, 2)),
        "backward_yield_difference": 0.5,
        "mcnemar_real_gt_backward": exact_one_sided_mcnemar(back_pairs),
        "exposure": {
            "forward_added_tests_total": 6,
            "backward_added_tests_total": 4,
            "forward_added_tests_median": 3.0,
            "backward_added_tests_median": 2.0,
            "forward_over_backward_total_ratio": 1.5,
            "instances_with_zero_forward_tests": 0,
            "instances_with_zero_backward_tests": 0,
            "symbol_count_median": 1.5,
        },
        "per_repo_real_hits": {"org/a": 1},
        "max_single_repo_share_of_hits": 1.0,
        "rows": rows,
    }
    return {
        "schema_version": "telos.iter219.yield_report.v1",
        "deltas_days": list(guard.DELTAS_DAYS),
        "permutation_salt": guard.PERMUTATION_SALT,
        "instances_seen": 3,
        "instances_included": 2,
        "instances_excluded": 1,
        "exclusion_counts": {"no_enclosing_symbol": 1},
        "results_by_delta": {str(d): copy.deepcopy(block) for d in guard.DELTAS_DAYS},
        "provider_calls": 0,
        "gpu_allocations": 0,
        "containers_built": 0,
        "repository_test_executions": 0,
        "scientific_result_claimed": False,
    }


def test_clean_synthetic_report_passes_every_guard() -> None:
    report = _synthetic_report()
    guard.check_report_recomputes(report)
    guard.check_zero_action(report)


def test_guard_fires_when_instance_accounting_does_not_close() -> None:
    report = _synthetic_report()
    report["instances_excluded"] = 5
    with pytest.raises(guard.Iter219ValidationError, match="does not close"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_reported_hits_disagree_with_rows() -> None:
    report = _synthetic_report()
    report["results_by_delta"]["365"]["real_hits"] = 2
    with pytest.raises(guard.Iter219ValidationError, match="real_hits"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_a_confidence_interval_is_tampered_with() -> None:
    report = _synthetic_report()
    report["results_by_delta"]["365"]["real_wilson_95"] = [0.99, 1.0]
    with pytest.raises(guard.Iter219ValidationError, match="Wilson"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_the_paired_test_is_tampered_with() -> None:
    report = _synthetic_report()
    report["results_by_delta"]["365"]["mcnemar_real_gt_control"]["one_sided_exact_p_value"] = 0.0
    with pytest.raises(guard.Iter219ValidationError, match="McNemar"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_an_instance_is_its_own_control() -> None:
    report = _synthetic_report()
    report["results_by_delta"]["365"]["rows"][0]["control_partner"] = "a__1"
    with pytest.raises(guard.Iter219ValidationError, match="its own control"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_the_control_shares_the_instance_repository() -> None:
    report = _synthetic_report()
    report["results_by_delta"]["365"]["rows"][1]["repo"] = "org/a"
    with pytest.raises(guard.Iter219ValidationError, match="within its own repository"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_the_window_set_drifts_from_the_instrument() -> None:
    report = _synthetic_report()
    report["deltas_days"] = [365]
    with pytest.raises(guard.Iter219ValidationError, match="windows drifted"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_the_permutation_salt_drifts() -> None:
    report = _synthetic_report()
    report["permutation_salt"] = "retuned-salt:"
    with pytest.raises(guard.Iter219ValidationError, match="salt drifted"):
        guard.check_report_recomputes(report)


@pytest.mark.parametrize(
    "field", ["provider_calls", "gpu_allocations", "containers_built", "repository_test_executions"]
)
def test_guard_fires_on_any_forbidden_action(field: str) -> None:
    report = _synthetic_report()
    report[field] = 1
    with pytest.raises(guard.Iter219ValidationError, match=field):
        guard.check_zero_action(report)


def test_guard_fires_when_the_result_overclaims() -> None:
    with pytest.raises(guard.Iter219ValidationError, match="forbidden claim"):
        guard.check_claim_boundary("This screen establishes the state of the art.")


def test_guard_fires_when_the_result_drops_the_screen_framing() -> None:
    with pytest.raises(guard.Iter219ValidationError, match="screen"):
        guard.check_claim_boundary("Later tests reference task symbols.")


def test_sealed_hypothesis_matches_the_instrument_constants() -> None:
    assert guard.validate(preflight=True) == []


def test_sealed_rules_guard_fires_when_prose_and_code_disagree() -> None:
    text = guard.HYPOTHESIS.read_text(encoding="utf-8").replace(
        "primary window is `Δ = 365`", "primary window is `Δ = 180`"
    )
    with pytest.raises(guard.Iter219ValidationError, match="primary window"):
        guard.check_sealed_rules_match_instrument(text)


# --------------------------------------------------------------------------- #
# Amendment A1: the confound that would have faked the entire result.
# --------------------------------------------------------------------------- #

from scripts.measure_iter219_temporal_yield import own_test_functions  # noqa: E402

TEST_PATCH = """diff --git a/tests/test_widget.py b/tests/test_widget.py
--- a/tests/test_widget.py
+++ b/tests/test_widget.py
@@ -1,3 +1,9 @@
 import pytest
+
+def test_render_after_fix():
+    assert Widget().render() == 1
+
+async def test_async_render():
+    assert True
"""


def test_own_fixing_pr_tests_are_identified_for_exclusion() -> None:
    assert own_test_functions(TEST_PATCH) == {
        ("tests/test_widget.py", "test_render_after_fix"),
        ("tests/test_widget.py", "test_async_render"),
    }


def test_own_test_functions_ignores_deleted_test_files() -> None:
    patch = "--- a/tests/test_gone.py\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-def test_x():\n-    pass\n"
    assert own_test_functions(patch) == set()


def test_own_test_functions_ignores_non_test_helpers() -> None:
    patch = (
        "--- a/tests/test_w.py\n+++ b/tests/test_w.py\n@@ -1,0 +1,2 @@\n"
        "+def helper_thing():\n+    pass\n"
    )
    assert own_test_functions(patch) == set()


def test_guard_fires_if_the_hypothesis_ever_drops_amendment_a1() -> None:
    # Without A1 the forward window silently readmits the task's own fixing-PR tests and
    # the primary yield becomes a tautology.  The guard must refuse that hypothesis.
    text = guard.normalize(guard.HYPOTHESIS.read_text(encoding="utf-8")).replace(
        "visible grader, not a hidden consequence test", "hidden consequence test"
    )
    with pytest.raises(guard.Iter219ValidationError, match="amendment A1"):
        guard.check_sealed_rules_match_instrument(text)


def test_guard_fires_if_the_hypothesis_drops_the_backward_control() -> None:
    text = guard.HYPOTHESIS.read_text(encoding="utf-8").replace("Y_backward", "Y_removed")
    with pytest.raises(guard.Iter219ValidationError, match="amendment A2"):
        guard.check_sealed_rules_match_instrument(text)


def test_amendment_records_that_no_outcome_existed_when_written() -> None:
    import json as _json

    amendment = _json.loads(guard.AMENDMENT.read_text(encoding="utf-8"))
    guard.check_amendment(amendment)


def test_guard_fires_if_the_amendment_claims_a_moved_threshold() -> None:
    import copy as _copy
    import json as _json

    amendment = _json.loads(guard.AMENDMENT.read_text(encoding="utf-8"))
    tampered = _copy.deepcopy(amendment)
    tampered["amendments"][0]["changes_thresholds"] = True
    with pytest.raises(guard.Iter219ValidationError, match="must not move a sealed threshold"):
        guard.check_amendment(tampered)


def test_guard_fires_if_the_amendment_was_written_after_observation() -> None:
    import copy as _copy
    import json as _json

    amendment = _json.loads(guard.AMENDMENT.read_text(encoding="utf-8"))
    tampered = _copy.deepcopy(amendment)
    tampered["observation_state_at_amendment"]["instances_measured"] = 500
    with pytest.raises(guard.Iter219ValidationError, match="no outcome existed"):
        guard.check_amendment(tampered)


def test_guard_fires_when_the_backward_control_is_tampered_with() -> None:
    report = _synthetic_report()
    report["results_by_delta"]["365"]["backward_control_hits"] = 2
    with pytest.raises(guard.Iter219ValidationError, match="backward_control_hits"):
        guard.check_report_recomputes(report)


def test_sealed_rule_scan_survives_markdown_rewrapping() -> None:
    # A wrapped sentence silently defeated a required-phrase scan in this repository
    # before.  Rewrapping the sealed prose must not change any verdict.
    raw = guard.HYPOTHESIS.read_text(encoding="utf-8")
    rewrapped = raw.replace("visible grader, not a hidden", "visible\n   grader,\n   not a hidden")

    guard.check_sealed_rules_match_instrument(raw)
    guard.check_sealed_rules_match_instrument(rewrapped)


# --------------------------------------------------------------------------- #
# L1: exposure imbalance must be visible, or a growth artifact reads as a result.
# --------------------------------------------------------------------------- #

from scripts.measure_iter219_temporal_yield import exposure_diagnostic  # noqa: E402


def test_exposure_diagnostic_reports_the_forward_backward_imbalance() -> None:
    rows = [
        {"forward_added_tests": 10, "backward_added_tests": 2, "symbol_count": 3},
        {"forward_added_tests": 0, "backward_added_tests": 0, "symbol_count": 1},
    ]
    exposure = exposure_diagnostic(rows)

    assert exposure["forward_added_tests_total"] == 10
    assert exposure["backward_added_tests_total"] == 2
    assert exposure["forward_over_backward_total_ratio"] == 5.0
    assert exposure["instances_with_zero_forward_tests"] == 1
    assert exposure["instances_with_zero_backward_tests"] == 1


def test_exposure_diagnostic_handles_an_empty_backward_side() -> None:
    rows = [{"forward_added_tests": 5, "backward_added_tests": 0, "symbol_count": 1}]
    assert exposure_diagnostic(rows)["forward_over_backward_total_ratio"] == float("inf")


def test_guard_fires_when_the_exposure_diagnostic_is_missing() -> None:
    report = _synthetic_report()
    del report["results_by_delta"]["365"]["exposure"]
    with pytest.raises(guard.Iter219ValidationError, match="exposure diagnostic missing"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_exposure_totals_are_tampered_with() -> None:
    report = _synthetic_report()
    report["results_by_delta"]["365"]["exposure"]["forward_added_tests_total"] = 999
    with pytest.raises(guard.Iter219ValidationError, match="forward exposure total"):
        guard.check_report_recomputes(report)


def test_guard_fires_when_a_known_limitation_is_dropped() -> None:
    import copy as _copy
    import json as _json

    amendment = _json.loads(guard.AMENDMENT.read_text(encoding="utf-8"))
    tampered = _copy.deepcopy(amendment)
    tampered["known_limitations_disclosed_not_fixed"] = [
        item for item in tampered["known_limitations_disclosed_not_fixed"] if item["id"] != "L1"
    ]
    with pytest.raises(guard.Iter219ValidationError, match="must remain disclosed"):
        guard.check_amendment(tampered)


def test_guard_fires_when_a_limitation_hides_its_direction_of_bias() -> None:
    import copy as _copy
    import json as _json

    amendment = _json.loads(guard.AMENDMENT.read_text(encoding="utf-8"))
    tampered = _copy.deepcopy(amendment)
    tampered["known_limitations_disclosed_not_fixed"][0]["direction_of_bias"] = ""
    with pytest.raises(guard.Iter219ValidationError, match="direction of bias"):
        guard.check_amendment(tampered)
