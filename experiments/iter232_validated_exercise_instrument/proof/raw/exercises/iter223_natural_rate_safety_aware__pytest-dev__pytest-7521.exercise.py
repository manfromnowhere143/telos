try:
    import pytest

    observed = []

    def probe(capfd):
        print("CR", end="\r")
        first = capfd.readouterr()
        print("CRLF", end="\r\n")
        second = capfd.readouterr()
        observed.append((first.out, first.err, second.out, second.err))

    class Plugin:
        def pytest_ignore_collect(self, path, config):
            return True

        def pytest_collection_modifyitems(self, session, config, items):
            items[:] = [
                pytest.Function.from_parent(session, name="probe", callobj=probe)
            ]

    status = pytest.main(
        ["-p", "no:terminal", "--noconftest"],
        plugins=[Plugin()],
    )
    print(f"RESULT={(status, tuple(observed))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
