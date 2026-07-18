import sphinx
from sphinx.builders import linkcheck
from types import SimpleNamespace

try:
    url = "https://example.invalid/missing#anchor"
    request_url = "https://example.invalid/missing"
    message = f"500 Server Error: Internal Server Error for url: {request_url}"

    class Response:
        status_code = 500
        url = request_url
        headers = {}

        def raise_for_status(self):
            raise linkcheck.requests.exceptions.HTTPError(message)

    response = Response()

    class Session:
        def head(self, uri, **kwargs):
            return response

        def get(self, uri, **kwargs):
            return response

    def request_head(uri, **kwargs):
        return response

    def request_get(uri, **kwargs):
        return response

    config = SimpleNamespace(
        linkcheck_anchors=True,
        linkcheck_anchors_ignore=[],
        linkcheck_auth=[],
        linkcheck_request_headers={},
        linkcheck_timeout=1,
        linkcheck_retries=0,
        user_agent="sphinx-linkcheck-test",
    )
    builder = SimpleNamespace(config=config)
    checker = linkcheck.HyperlinkAvailabilityChecker(builder, None, None)
    checker.session = Session()
    linkcheck.requests.head = request_head
    linkcheck.requests.get = request_get

    def anchor_lookup_must_not_run(*args, **kwargs):
        raise AssertionError("anchor-checked")

    checker.check_anchor = anchor_lookup_must_not_run
    result = checker.check_uri(url, "index", 1)

    assert result[0] == "broken", "wrong-status"
    assert result[1] == message, "wrong-error"
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'assertion')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
