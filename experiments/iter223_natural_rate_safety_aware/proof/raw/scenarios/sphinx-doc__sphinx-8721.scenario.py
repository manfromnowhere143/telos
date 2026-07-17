from types import SimpleNamespace

from sphinx.ext.viewcode import collect_pages


class App:
    def __init__(self):
        self.config_accessed = False
        self._config = SimpleNamespace(viewcode_enable_epub=False)
        self.builder = SimpleNamespace(
            name="singlehtml",
            env=SimpleNamespace(
                _viewcode_modules={},
                config=SimpleNamespace(viewcode_enable_epub=False),
            ),
            highlighter=object(),
            get_relative_uri=lambda _from, _to: "",
        )

    @property
    def config(self):
        self.config_accessed = True
        return self._config


app = App()
pages = list(collect_pages(app))
print("RESULT=" + repr((pages, app.config_accessed)))
