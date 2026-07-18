import pytest

try:
    test_status = {}

    def my_test(capfd):
        try:
            print("Greetings from DOS\r", end="")
            out, err = capfd.readouterr()
            
            if out == "Greetings from DOS\r":
                test_status["status"] = "PASS"
            else:
                test_status["status"] = "FAIL"
                test_status["detail"] = f"Expected 'Greetings from DOS\\r', got {out!r}"
        except Exception as e:
            test_status["status"] = "ERROR"
            test_status["detail"] = str(e)

    class InjectPlugin:
        def pytest_collection_modifyitems(self, session, config, items):
            try:
                try:
                    func = pytest.Function.from_parent(session, name="my_test", callobj=my_test)
                except AttributeError:
                    func = pytest.Function(name="my_test", parent=session, callobj=my_test)
                
                items.clear()
                items.append(func)
            except Exception as e:
                test_status["status"] = "ERROR"
                test_status["detail"] = f"Modifyitems error: {e}"

    # -p no:terminal completely disables pytest's standard stdout reporting.
    # --noconftest ensures test isolation from the surrounding filesystem.
    pytest.main(
        ["-p", "no:terminal", "--disable-warnings", "--noconftest"],
        plugins=[InjectPlugin()]
    )
    
    if not test_status:
        print(f"RESULT={('FAIL', 'Test did not run')!r}")
    elif test_status.get("status") == "PASS":
        print(f"RESULT={('PASS',)!r}")
    elif test_status.get("status") == "FAIL":
        print(f"RESULT={('FAIL', test_status.get('detail', 'Unknown'))!r}")
    else:
        print(f"RESULT={('ERROR', test_status.get('detail', 'Unknown'))!r}")

except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
