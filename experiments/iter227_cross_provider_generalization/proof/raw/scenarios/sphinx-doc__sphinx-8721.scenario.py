import sphinx.ext.viewcode as viewcode


class Highlighter:
    def highlight_block(self, code, language, linenos=False):
        return "<div>demo</div>"


class Config:
    viewcode_enable_epub = False


class Env:
    config = Config()
    _viewcode_modules = {"demo": ("x = 1\n", {}, True, None)}


class Builder:
    name = "singlehtml"
    env = Env()
    highlighter = Highlighter()

    def get_relative_uri(self, from_, to):
        return to


class App:
    builder = Builder()
    verbosity = 0


def stable_status_iterator(iterable, *args, **kwargs):
    return iterable


viewcode.status_iterator = stable_status_iterator
pages = list(viewcode.collect_pages(App()))
print("RESULT=" + repr([page[0] for page in pages]))
