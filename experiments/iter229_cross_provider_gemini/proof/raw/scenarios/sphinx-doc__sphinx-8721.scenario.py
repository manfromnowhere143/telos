from sphinx.ext.viewcode import collect_pages


class FirstEnv:
    _viewcode_modules = {}


class SecondEnv:
    pass


class Builder:
    name = "html"

    def __init__(self):
        self.env_reads = 0
        self.highlighter_reads = 0

    @property
    def env(self):
        self.env_reads += 1
        return FirstEnv() if self.env_reads == 1 else SecondEnv()

    @property
    def highlighter(self):
        self.highlighter_reads += 1
        return None

    def get_relative_uri(self, *args):
        return ""


class App:
    def __init__(self):
        self.builder = Builder()


app = App()
pages = list(collect_pages(app))
print("RESULT=%r" % ((pages, app.builder.env_reads, app.builder.highlighter_reads),))
