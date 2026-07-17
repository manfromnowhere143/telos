from types import SimpleNamespace

from sphinx.ext.viewcode import collect_pages

builder = SimpleNamespace(
    name="singlehtml",
    env=SimpleNamespace(
        _viewcode_modules={
            "demo": (
                "def item():\n    pass\n",
                {},
                {"item": "index"},
                "demo",
            )
        }
    ),
    highlighter=SimpleNamespace(
        highlight_block=lambda code, language, linenos=False: "<pre>%s</pre>" % code
    ),
    get_relative_uri=lambda source, target: target,
)
app = SimpleNamespace(builder=builder, verbosity=0)

print("RESULT=%r" % [page[0] for page in collect_pages(app)])
