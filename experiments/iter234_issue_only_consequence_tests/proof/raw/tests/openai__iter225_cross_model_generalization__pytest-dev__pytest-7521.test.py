import pytest

try:
    class Plugin:
        def pytest_collection(self, session):
            def test_capfd_preserves_embedded_and_successive_carriage_returns(capfd):
                print("left\rright", end="\r")
                out, err = capfd.readouterr()
                assert out == "left\rright\r"
                assert err == ""

                print("\rnext\rvalue", end="")
                out, err = capfd.readouterr()
                assert out == "\rnext\rvalue"
                assert err == ""

            item = pytest.Function.from_parent(
                session,
                name="test_capfd_preserves_embedded_and_successive_carriage_returns",
                callobj=test_capfd_preserves_embedded_and_successive_carriage_returns,
            )
            session.items = [item]
            session.testscollected = 1
            return True

    result = pytest.main(["-p", "no:terminal"], plugins=[Plugin()])
    assert result == 0, "pytest exit"
except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except BaseException as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
