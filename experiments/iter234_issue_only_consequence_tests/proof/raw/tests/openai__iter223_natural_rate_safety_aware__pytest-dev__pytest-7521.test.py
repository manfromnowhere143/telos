import pytest

try:
    def check_capture(capfd):
        print("first", end="\r")
        print("second", end="\r\n")
        print("third", end="")
        out, err = capfd.readouterr()
        assert out == "first\rsecond\r\nthird"
        assert err == ""
        print("again", end="\r")
        out, err = capfd.readouterr()
        assert out == "again\r"
        assert err == ""

    class Plugin:
        def pytest_ignore_collect(self, path, config):
            return True

        def pytest_collection_modifyitems(self, session, config, items):
            item = pytest.Function.from_parent(
                session, name="test_capfd_carriage_returns", callobj=check_capture
            )
            items[:] = [item]

    result = pytest.main(["-p", "no:terminal"], plugins=[Plugin()])
    assert result == pytest.ExitCode.OK, "capture failed"
except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
