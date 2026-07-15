import requests
from requests.models import PreparedRequest

request = PreparedRequest()

try:
    request.prepare_url("http://.example.com", None)
    result = ("ok", request.url)
except Exception as exc:
    result = (type(exc).__name__, str(exc))

print("RESULT=" + repr(result))
