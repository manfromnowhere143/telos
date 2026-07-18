from types import SimpleNamespace

try:
    from sphinx.ext.viewcode import collect_pages

    class Highlighter:
        def highlight_block(self, *args, **kwargs):
            return "<div>source</div>"

    env = SimpleNamespace(
        _viewcode_modules={
            "demo": {"used": True, "code": "x = 1\n", "tags": {}}
        },
        config=SimpleNamespace(viewcode_enable_epub=False),
    )
    builder = SimpleNamespace(
        env=env,
        name="singlehtml",
        highlighter=Highlighter(),
        get_relative_uri=lambda *args: "",
    )
    app = SimpleNamespace(builder=builder)
    pages = tuple(page[0] for page in collect_pages(app))
    print(f"RESULT={pages!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
