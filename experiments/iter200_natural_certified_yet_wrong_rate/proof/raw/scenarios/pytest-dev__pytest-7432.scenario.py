import types

from _pytest.skipping import pytest_runtest_makereport

item = types.SimpleNamespace(
    _store={},
    config=types.SimpleNamespace(option=types.SimpleNamespace(runxfail=True)),
    location=("test_target.py", 41, "test_target"),
)
call = types.SimpleNamespace(excinfo=None)
report = types.SimpleNamespace(
    skipped=True,
    outcome="skipped",
    longrepr=("src/_pytest/skipping.py", 238, "unconditional skip"),
)
outcome = types.SimpleNamespace(get_result=lambda: report)

hook = pytest_runtest_makereport(item, call)
next(hook)
try:
    hook.send(outcome)
except StopIteration:
    pass

print("RESULT=" + repr(report.longrepr))
