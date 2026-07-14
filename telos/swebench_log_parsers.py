"""Vendored SWE-bench test-log parsers (django, pytest-v2, matplotlib).

Provenance: copied verbatim in behavior from `swebench.harness.log_parsers` in the `swebench` package,
version 4.1.0 (SWE-bench, MIT License, https://github.com/princeton-nlp/SWE-bench). Vendored so that
iter194 adjudication is hermetic and reproducible without an external dependency, and so that Telos parses
test output with the exact logic the official grader uses to decide `resolved`. The `test_spec` parameter
of the originals is unused in these three functions and is dropped here.

Only the three parsers Telos needs (the repos in the iter193/iter194 candidate set) are vendored. Do not
extend this file with new behavior; if a new repo is needed, vendor its official parser with attribution.
"""

from __future__ import annotations

import re


class TestStatus:
    FAILED = "FAILED"
    PASSED = "PASSED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    XFAIL = "XFAIL"


_ALL_STATUSES = (
    TestStatus.FAILED,
    TestStatus.PASSED,
    TestStatus.SKIPPED,
    TestStatus.ERROR,
    TestStatus.XFAIL,
)


def parse_log_django(log: str) -> dict[str, str]:
    """Parser for test logs generated with the Django test framework (swebench 4.1.0)."""

    test_status_map: dict[str, str] = {}
    lines = log.split("\n")

    prev_test = None
    for line in lines:
        line = line.strip()

        if "--version is equivalent to version" in line:
            test_status_map["--version is equivalent to version"] = TestStatus.PASSED

        if " ... " in line:
            prev_test = line.split(" ... ")[0]

        pass_suffixes = (" ... ok", " ... OK", " ...  OK")
        for suffix in pass_suffixes:
            if line.endswith(suffix):
                if line.strip().startswith(
                    "Applying sites.0002_alter_domain_unique...test_no_migrations"
                ):
                    line = line.split("...", 1)[-1].strip()
                test = line.rsplit(suffix, 1)[0]
                test_status_map[test] = TestStatus.PASSED
                break
        if " ... skipped" in line:
            test = line.split(" ... skipped")[0]
            test_status_map[test] = TestStatus.SKIPPED
        if line.endswith(" ... FAIL"):
            test = line.split(" ... FAIL")[0]
            test_status_map[test] = TestStatus.FAILED
        if line.startswith("FAIL:"):
            test = line.split()[1].strip()
            test_status_map[test] = TestStatus.FAILED
        if line.endswith(" ... ERROR"):
            test = line.split(" ... ERROR")[0]
            test_status_map[test] = TestStatus.ERROR
        if line.startswith("ERROR:"):
            test = line.split()[1].strip()
            test_status_map[test] = TestStatus.ERROR

        if line.lstrip().startswith("ok") and prev_test is not None:
            test = prev_test
            test_status_map[test] = TestStatus.PASSED

    patterns = [
        r"^(.*?)\s\.\.\.\sTesting\ against\ Django\ installed\ in\ ((?s:.*?))\ silenced\)\.\nok$",
        r"^(.*?)\s\.\.\.\sInternal\ Server\ Error:\ \/(.*)\/\nok$",
        r"^(.*?)\s\.\.\.\sSystem check identified no issues \(0 silenced\)\nok$",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, log, re.MULTILINE):
            test_name = match.group(1)
            test_status_map[test_name] = TestStatus.PASSED
    return test_status_map


def parse_log_pytest_v2(log: str) -> dict[str, str]:
    """Parser for test logs generated with a later PyTest version (swebench 4.1.0)."""

    test_status_map: dict[str, str] = {}
    escapes = "".join([chr(char) for char in range(1, 32)])
    for line in log.split("\n"):
        line = re.sub(r"\[(\d+)m", "", line)
        translator = str.maketrans("", "", escapes)
        line = line.translate(translator)
        if any(line.startswith(x) for x in _ALL_STATUSES):
            if line.startswith(TestStatus.FAILED):
                line = line.replace(" - ", " ")
            test_case = line.split()
            if len(test_case) >= 2:
                test_status_map[test_case[1]] = test_case[0]
        elif any(line.endswith(x) for x in _ALL_STATUSES):
            test_case = line.split()
            if len(test_case) >= 2:
                test_status_map[test_case[0]] = test_case[1]
    return test_status_map


def parse_log_matplotlib(log: str) -> dict[str, str]:
    """Parser for matplotlib test logs generated with the PyTest framework (swebench 4.1.0)."""

    test_status_map: dict[str, str] = {}
    for line in log.split("\n"):
        line = line.replace("MouseButton.LEFT", "1")
        line = line.replace("MouseButton.RIGHT", "3")
        if any(line.startswith(x) for x in _ALL_STATUSES):
            if line.startswith(TestStatus.FAILED):
                line = line.replace(" - ", " ")
            test_case = line.split()
            if len(test_case) <= 1:
                continue
            test_status_map[test_case[1]] = test_case[0]
    return test_status_map


PARSER_BY_REPO = {
    "django/django": parse_log_django,
    "astropy/astropy": parse_log_pytest_v2,
    "matplotlib/matplotlib": parse_log_matplotlib,
}
