import os
import tempfile

try:
    from _pytest.capture import EncodedFile

    fd, path = tempfile.mkstemp()
    os.close(fd)
    try:
        with open(path, "w+b") as raw:
            wrapped = EncodedFile(raw, "utf-8")
            assert "b" in raw.mode
            assert "b" not in wrapped.mode
            wrapped.write("π")
            wrapped.flush()
            raw.seek(0)
            assert raw.read() == "π".encode("utf-8")
        print("PROP_PASS")
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
except Exception:
    print("PROP_FAIL")
