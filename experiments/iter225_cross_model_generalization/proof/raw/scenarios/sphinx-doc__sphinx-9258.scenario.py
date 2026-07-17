from docutils import nodes
from sphinx.domains.python import PyObject

obj = object.__new__(PyObject)
result = obj.make_xrefs("class", "py", "A|or B")

observable = tuple(
    ("xref", node["reftarget"]) if isinstance(node, nodes.Element)
    else ("text", node.astext())
    for node in result
)
print("RESULT=" + repr(observable))
