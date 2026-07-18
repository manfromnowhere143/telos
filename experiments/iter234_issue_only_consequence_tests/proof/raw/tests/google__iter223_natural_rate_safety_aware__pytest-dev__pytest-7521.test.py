import pytest

results = []

class CapturePlugin:
    def pytest_collection(self, session):
        # We hook into pytest_collection to run our capture test and exit early,
        # avoiding any filesystem traversal or test collection entirely.
        capman = session.config.pluginmanager.getplugin("capturemanager")
        if not capman:
            results.append("no capturemanager found")
            pytest.exit("done")
            
        try:
            # Clear any existing capture buffers
            capman.read_global_capture()
            
            # Print a carriage return (the issue is that FDCapture converts \r to \n)
            print("Greetings from DOS\r", end="", flush=True)
            
            # Read back the captured output
            out, err = capman.read_global_capture()
            
            if out.endswith("Greetings from DOS\r"):
                results.append("PASS")
            else:
                # If the regression is present, 'out' will end with a newline '\n' instead
                results.append(f"output altered, got {out!r}")
        except Exception as e:
            results.append(f"exception {type(e).__name__}: {e}")
            
        # Abort the pytest run cleanly before it tries to collect anything
        pytest.exit("done")

try:
    # Run pytest in-process with FDCapture globally enabled (mimicking capfd)
    pytest.main(["--capture=fd", "-q"], plugins=[CapturePlugin()])
    
    if "PASS" in results:
        print(f"RESULT={('PASS',)!r}")
    elif results:
        print(f"RESULT={('FAIL', results[0])!r}")
    else:
        print(f"RESULT={('FAIL', 'Plugin did not execute')!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
