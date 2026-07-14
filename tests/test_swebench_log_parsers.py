"""Regression tests for the vendored SWE-bench log parsers.

These lock the parsers to the behavior they were vendored from (swebench 4.1.0), so iter194 certification
and wrongness decisions parse test output exactly as the official grader does. The expected maps below were
confirmed identical to `swebench.harness.log_parsers` output at vendoring time.
"""

from __future__ import annotations

from telos.swebench_log_parsers import (
    TestStatus,
    parse_log_django,
    parse_log_matplotlib,
    parse_log_pytest_v2,
)


def test_parse_log_django_statuses() -> None:
    log = "\n".join(
        [
            "test_basic_context (template_tests.test_engine.RenderToStringTest) ... ok",
            "test_autoescape_off (template_tests.test_engine.RenderToStringTest) ... FAIL",
            "test_error (template_tests.test_engine.OtherTest) ... ERROR",
            "test_skip (template_tests.test_engine.OtherTest) ... skipped 'reason'",
        ]
    )
    got = parse_log_django(log)
    assert got["test_basic_context (template_tests.test_engine.RenderToStringTest)"] == TestStatus.PASSED
    assert got["test_autoescape_off (template_tests.test_engine.RenderToStringTest)"] == TestStatus.FAILED
    assert got["test_error (template_tests.test_engine.OtherTest)"] == TestStatus.ERROR
    assert got["test_skip (template_tests.test_engine.OtherTest)"] == TestStatus.SKIPPED


def test_parse_log_pytest_v2_leading_and_trailing() -> None:
    log = "\n".join(
        [
            "PASSED astropy/utils/tests/test_misc.py::test_isiterable",
            "FAILED astropy/utils/tests/test_misc.py::test_warn - AssertionError",
            "astropy/utils/tests/test_misc.py::test_old_style PASSED",
        ]
    )
    got = parse_log_pytest_v2(log)
    assert got["astropy/utils/tests/test_misc.py::test_isiterable"] == TestStatus.PASSED
    assert got["astropy/utils/tests/test_misc.py::test_warn"] == TestStatus.FAILED
    assert got["astropy/utils/tests/test_misc.py::test_old_style"] == TestStatus.PASSED


def test_parse_log_matplotlib_status_first() -> None:
    log = "\n".join(
        [
            "PASSED lib/matplotlib/tests/test_patches.py::test_clip_to_bbox",
            "FAILED lib/matplotlib/tests/test_patches.py::test_shadow - assert 0",
        ]
    )
    got = parse_log_matplotlib(log)
    assert got["lib/matplotlib/tests/test_patches.py::test_clip_to_bbox"] == TestStatus.PASSED
    assert got["lib/matplotlib/tests/test_patches.py::test_shadow"] == TestStatus.FAILED


def test_parse_log_pytest_and_options_and_sympy() -> None:
    from telos.swebench_log_parsers import (
        parse_log_pytest,
        parse_log_pytest_options,
        parse_log_sympy,
    )

    py = parse_log_pytest(
        "PASSED xarray/tests/test_a.py::test_one\nFAILED xarray/tests/test_a.py::test_two - err"
    )
    assert py["xarray/tests/test_a.py::test_one"] == TestStatus.PASSED
    assert py["xarray/tests/test_a.py::test_two"] == TestStatus.FAILED

    opt = parse_log_pytest_options("PASSED requests/tests/test_x.py::test_p[GET]")
    assert opt["requests/tests/test_x.py::test_p[GET]"] == TestStatus.PASSED

    sy = parse_log_sympy("test_foo ok\ntest_bar F\ntest_baz E")
    assert sy["test_foo"] == TestStatus.PASSED
    assert sy["test_bar"] == TestStatus.FAILED
    assert sy["test_baz"] == TestStatus.ERROR


def test_empty_log_is_empty_map() -> None:
    assert parse_log_django("") == {}
    assert parse_log_pytest_v2("") == {}
    assert parse_log_matplotlib("") == {}
