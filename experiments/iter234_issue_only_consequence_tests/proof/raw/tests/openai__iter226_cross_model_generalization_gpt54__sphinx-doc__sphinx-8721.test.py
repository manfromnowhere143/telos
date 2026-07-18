import types

try:
    from sphinx.ext import viewcode

    class App:
        def __init__(self):
            self.callbacks = {}

        def add_config_value(self, *args, **kwargs):
            pass

        def connect(self, event, callback, *args, **kwargs):
            self.callbacks[event] = callback

    class Highlighter:
        def highlight_block(self, source, language, **kwargs):
            return source

    app = App()
    viewcode.setup(app)
    app.config = types.SimpleNamespace(viewcode_enable_epub=False)
    app.builder = types.SimpleNamespace(
        name="epub",
        format="html",
        highlighter=Highlighter(),
    )
    app.env = types.SimpleNamespace(
        _viewcode_modules={"example.module": ("value = 1\n", {}, True, "index")}
    )

    pages = list(app.callbacks["html-collect-pages"](app))
    if pages:
        raise AssertionError("epub module page created")
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
