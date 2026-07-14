from requests.models import PreparedRequest

request = PreparedRequest()
request.prepare(method="OPTIONS", url="http://example.com/")
print(f"RESULT={request.headers.get('Content-Length')!r}")
