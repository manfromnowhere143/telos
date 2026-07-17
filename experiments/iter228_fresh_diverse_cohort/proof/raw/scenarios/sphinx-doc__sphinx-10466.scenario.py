from types import SimpleNamespace

from sphinx.builders.gettext import Catalog

catalog = Catalog()
for source, line, uid in (("z.rst", 9, "u1"), ("a.rst", 1, "u2"), ("z.rst", 9, "u3")):
    catalog.add(
        "message",
        SimpleNamespace(source=source, line=line, uuid=uid, uid=uid),
    )

print("RESULT=" + repr(next(iter(catalog)).positions))
