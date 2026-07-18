import typing
from types import SimpleNamespace
from sphinx.ext.autodoc.typehints import process_docstring

try:
    Payload = typing.Dict[str, typing.Any]
    Result = typing.Dict[str, Payload]

    def documented(data, result):
        return result

    documented.__annotations__ = {
        "data": "Payload",
        "result": "Result",
        "return": "Result",
    }

    app = SimpleNamespace(
        config=SimpleNamespace(
            autodoc_typehints="description",
            autodoc_type_aliases={
                "Payload": "fixture.Payload",
                "Result": "fixture.Result",
            },
            autodoc_typehints_format="fully-qualified",
            autodoc_typehints_description_target="all",
        )
    )
    lines = [
        ":param data: Input payload.",
        ":param result: Existing result.",
        ":returns: Updated result.",
    ]
    process_docstring(app, "function", "documented", documented, SimpleNamespace(), lines)
    rendered = "\n".join(lines)

    assert ":type data:" in rendered and "fixture.Payload" in rendered
    assert ":type result:" in rendered and "fixture.Result" in rendered
    assert ":rtype:" in rendered and "fixture.Result" in rendered
    assert "Dict[str, Any]" not in rendered
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    detail = "aliases"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
