import types

try:
    import sphinx.ext.viewcode as viewcode

    class Used:
        def __bool__(self):
            return True

        def items(self):
            return ()

    class Highlighter:
        def highlight_block(self, *args, **kwargs):
            return "<div>source</div>"

    def relative_uri(*args, **kwargs):
        return ""

    env = types.SimpleNamespace(
        config=types.SimpleNamespace(viewcode_enable_epub=False)
    )
    setattr(
        env,
        "_viewcode_modules",
        {
            "example": {
                "used": Used(),
                "code": "x = 1\n",
                "tags": {},
            }
        },
    )
    builder = types.SimpleNamespace(
        name="singlehtml",
        env=env,
        highlighter=Highlighter(),
        get_relative_uri=relative_uri,
    )
    app = types.SimpleNamespace(
        builder=builder,
        config=types.SimpleNamespace(viewcode_enable_epub=False),
    )

    if not hasattr(viewcode, "collect_pages"):
        raise RuntimeError("collect_pages unavailable")
    result = len(list(viewcode.collect_pages(app)))
    print(f"RESULT={result!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
