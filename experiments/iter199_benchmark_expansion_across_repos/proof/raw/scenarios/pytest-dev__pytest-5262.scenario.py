import os
import tempfile

from _pytest.capture import EncodedFile

fd, path = tempfile.mkstemp()
os.close(fd)
try:
    with open(path, "wb") as buffer:
        result = EncodedFile(buffer, "utf-8").mode
    print("RESULT=" + repr(result))
finally:
    os.unlink(path)
