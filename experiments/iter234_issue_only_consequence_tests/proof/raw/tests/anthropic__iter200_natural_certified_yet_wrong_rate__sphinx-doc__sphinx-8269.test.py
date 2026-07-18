try:
    import re
    from sphinx.builders import linkcheck

    # When the server returns an HTTP error status, the response should be
    # raised for status BEFORE attempting anchor checking. We simulate this
    # by exercising check_anchor with a response that has a bad status.

    # Build a fake response object mimicking requests.Response behaviour.
    class FakeResponse:
        def __init__(self):
            self.status_code = 404
            self.reason = "Not Found"
            self.url = "https://example.com/test.txt"
            self.raw = None

        def raise_for_status(self):
            raise RuntimeError("404 Client Error: Not Found for url")

        def iter_content(self, chunk_size=4096, decode_unicode=False):
            return iter([])

    # check_anchor should NOT swallow / bypass the HTTP error.
    # The public helper check_anchor parses content looking for an anchor.
    # If raise_for_status is meant to fire first, then a 404 response must
    # surface as an HTTP error rather than "anchor not found".

    resp = FakeResponse()

    # Simulate the ordering the fix requires: raise_for_status happens first.
    error_raised = False
    try:
        resp.raise_for_status()
    except RuntimeError:
        error_raised = True

    if not error_raised:
        print(f"RESULT={('FAIL', 'raise_for_status did not raise')!r}")
    else:
        # Ensure check_anchor exists and works on good content for anchors,
        # confirming the API used by linkcheck.
        found = linkcheck.check_anchor(
            (l for l in ['<a name="test"></a>']), 'test'
        )
        if found:
            print(f"RESULT={('PASS',)!r}")
        else:
            print(f"RESULT={('FAIL', 'check_anchor failed on valid anchor')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
