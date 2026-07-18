from types import SimpleNamespace
from sphinx.builders import linkcheck

try:
    url = "https://example.invalid/missing.html#missing"

    class Response:
        headers = {"Content-Type": "text/html"}
        content = b"<html><body></body></html>"
        text = "<html><body></body></html>"
        encoding = "utf-8"

        def raise_for_status(self):
            raise linkcheck.requests.exceptions.HTTPError(
                "404 Client Error: Not Found for url: https://example.invalid/missing.html"
            )

        def iter_content(self, chunk_size=1, decode_unicode=False):
            yield self.text if decode_unicode else self.content

    def failing_request(*args, **kwargs):
        return Response()

    linkcheck.requests.get = failing_request
    linkcheck.requests.head = failing_request

    def run(anchors):
        config = SimpleNamespace(
            linkcheck_anchors=anchors,
            linkcheck_anchors_ignore=[],
            linkcheck_auth=[],
            linkcheck_timeout=1,
            linkcheck_retries=1,
            linkcheck_request_headers={},
            linkcheck_allowed_redirects=True,
        )
        builder = SimpleNamespace(app=SimpleNamespace(config=config))
        return linkcheck.CheckExternalLinksBuilder.check_uri(builder, url)

    observed = (run(True), run(False))
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
