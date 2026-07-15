import urllib.request

from _pytest.pastebin import create_new_paste

captured = []


class Response:
    def read(self):
        return b'<a href="/raw/testpaste">'


def fake_urlopen(url, data=None):
    captured.append((url, data))
    return Response()


urllib.request.urlopen = fake_urlopen

result = create_new_paste("=== pytest output ===\n\x00not python code\n")
print("RESULT=" + repr((result, captured[0])))
