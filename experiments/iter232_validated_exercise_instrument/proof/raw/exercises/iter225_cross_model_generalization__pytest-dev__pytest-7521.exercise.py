try:
    import pytest

    seen = []

    def probe(capfd):
        print("carriage", end="\r")
        first = capfd.readouterr()
        print("pair", end="\r\n")
        second = capfd.readouterr()
        seen.append((first.out, first.err, second.out, second.err))

    class Plugin:
        @pytest.hookimpl(tryfirst=True)
        def pytest_collection(self, session):
            session.items = [
                pytest.Function.from_parent(session, name="probe", callobj=probe)
            ]
            return True

    pytest.main(["-p", "no:terminal"], plugins=[Plugin()])
    observed = seen[0]
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
