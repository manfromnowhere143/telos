import sphinx.builders.gettext as gettext
from docutils import nodes

catalog_type = getattr(gettext, "MessageCatalog", None) or getattr(gettext, "Catalog")
catalog = catalog_type()

for source, uid in (("Case.rst", "one"), ("case.rst", "two")):
    origin = nodes.Element("", source=source, line=7)
    origin.source = source
    origin.line = 7
    origin["uid"] = uid
    catalog.add("message", origin)

print("RESULT=" + repr(next(iter(catalog)).positions))
