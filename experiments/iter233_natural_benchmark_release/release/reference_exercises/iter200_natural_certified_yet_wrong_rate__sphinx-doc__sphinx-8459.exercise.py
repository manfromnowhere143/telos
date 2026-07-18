import sphinx
from sphinx.util import inspect, typing

try:
    def sample(data: "JSONObject") -> "JSONObject":
        return data

    sig = inspect.signature(
        sample,
        type_aliases={"JSONObject": "types.JSONObject"},
    )
    observed = (
        typing.stringify(sig.parameters["data"].annotation),
        typing.stringify(sig.return_annotation),
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
