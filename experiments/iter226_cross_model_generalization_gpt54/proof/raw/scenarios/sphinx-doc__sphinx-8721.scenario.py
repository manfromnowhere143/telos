from types import SimpleNamespace

from sphinx.ext.viewcode import collect_pages


class ProbeModules:
    def __len__(self):
        return 1

    def items(self):
        raise RuntimeError("viewcode modules were inspected")


env = SimpleNamespace(
    _viewcode_modules=ProbeModules(),
    config=SimpleNamespace(viewcode_enable_epub=False),
)
builder = SimpleNamespace(
    env=env,
    name="epub3",
    highlighter=object(),
    get_relative_uri=lambda source, target: target,
)
app = SimpleNamespace(
    builder=builder,
    config=SimpleNamespace(viewcode_enable_epub=False),
)

try:
    output = tuple(collect_pages(app))
    result = ("pages", output)
except Exception as exc:
    result = ("error", type(exc).__name__, exc.args)

print("RESULT=" + repr(result))
