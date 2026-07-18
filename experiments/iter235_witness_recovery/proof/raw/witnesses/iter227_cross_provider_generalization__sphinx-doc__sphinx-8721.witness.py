import types

try:
    import sphinx.ext.viewcode as viewcode

    if not hasattr(viewcode, "collect_pages"):
        raise RuntimeError("collect_pages unavailable")

    class Highlighter:
        def highlight_block(self, code, language, linenos=False):
            return "<div><pre>" + code + "</pre></div>"

    builder = types.SimpleNamespace()
    builder.name = "singlehtml"
    builder.highlighter = Highlighter()
    builder.get_relative_uri = lambda *args: ""

    env = types.SimpleNamespace()
    env.config = types.SimpleNamespace(viewcode_enable_epub=False)
    setattr(env, "_viewcode_modules", {
        "sample": {
            "code": "x = 1",
            "tags": {},
            "used": {"index"},
            "refnames": {},
        }
    })
    builder.env = env
    app = types.SimpleNamespace(builder=builder)

    pages = [page[0] for page in viewcode.collect_pages(app)]
    print(f"RESULT={pages!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
