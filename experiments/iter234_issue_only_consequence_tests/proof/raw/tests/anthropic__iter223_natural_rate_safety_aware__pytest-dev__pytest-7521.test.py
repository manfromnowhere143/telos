import pytest

def test_cafd_carriage_return(capfd):
    print('Greetings from DOS', end='\r')
    out, err = capfd.readouterr()
    assert out == 'Greetings from DOS\r', repr(out)

def test_cafd_crlf(capfd):
    print('line', end='\r\n')
    out, err = capfd.readouterr()
    assert out == 'line\r\n', repr(out)

def test_capsys_carriage_return(capsys):
    print('data', end='\r')
    out, err = capsys.readouterr()
    assert out == 'data\r', repr(out)

try:
    results = []

    class Collector:
        def pytest_runtest_logreport(self, report):
            if report.when == 'call':
                results.append((report.nodeid, report.outcome))

    plugin = Collector()
    ret = pytest.main(
        ['-p', 'no:cacheprovider', '-x', '-q', __file__ + '::test_cafd_carriage_return',
         __file__ + '::test_cafd_crlf', __file__ + '::test_capsys_carriage_return'],
        plugins=[plugin],
    )

    outcomes = {nid: oc for nid, oc in results}
    assert len(outcomes) == 3, f"ran {len(outcomes)} tests"
    failed = [nid for nid, oc in outcomes.items() if oc != 'passed']
    assert not failed, f"failed: {failed}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
