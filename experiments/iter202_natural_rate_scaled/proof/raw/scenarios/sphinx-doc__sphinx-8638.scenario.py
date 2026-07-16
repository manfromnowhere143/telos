from docutils import nodes
from sphinx import addnodes
from sphinx.domains.python import PyObject

directive = PyObject.__new__(PyObject)
field = next(item for item in directive.doc_field_types if item.name == 'variable')
result = field.make_field(
    {},
    'py',
    [('somename', [nodes.Text('description')])],
)
print(f"RESULT={(field.rolename, len(list(result.findall(addnodes.pending_xref))))!r}")
