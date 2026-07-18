try:
    from sphinx.ext import viewcode

    class ReadyEnv:
        def __init__(self):
            self._viewcode_modules = {}

    class EmptyEnv:
        pass

    class Builder:
        name = "html"
        highlighter = None

        def __init__(self):
            self.accesses = 0

        @property
        def env(self):
            self.accesses += 1
            if self.accesses == 1:
                return ReadyEnv()
            return EmptyEnv()

        def get_relative_uri(self, fromuri, touri):
            return touri

    class App:
        def __init__(self):
            self.builder = Builder()

    app = App()
    if hasattr(viewcode, "collect_pages"):
        pages = list(viewcode.collect_pages(app))
        result = (pages, app.builder.accesses)
    else:
        result = ("ERROR", "AttributeError")
    print(f"RESULT={result!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
