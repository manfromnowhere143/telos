import contextlib
import io

from pylint.checkers.similar import Similar

similar = Similar(0, False, False, True)
similar.append_stream("first.py", io.StringIO("value = 1\n"))
similar.append_stream("second.py", io.StringIO("value = 1\n"))

output = io.StringIO()
with contextlib.redirect_stdout(output):
    similar.run()

print(f"RESULT={output.getvalue()!r}")
