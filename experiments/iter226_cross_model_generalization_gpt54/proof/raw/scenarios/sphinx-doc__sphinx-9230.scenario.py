from types import SimpleNamespace

from docutils import nodes
from docutils.utils import new_document
from sphinx.util.docfields import DocFieldTransformer, TypedField

document = new_document("test")
field_list = nodes.field_list()
field = nodes.field()
field += nodes.field_name("", "param dict[str, str] value")
field += nodes.field_body("", nodes.paragraph("", "description"))
field_list += field
document += field_list

typed_field = TypedField(
    "parameter",
    names=("param",),
    typenames=("type",),
    label="Parameters",
    rolename=None,
    typerolename=None,
    can_collapse=True,
)

transformer = DocFieldTransformer.__new__(DocFieldTransformer)
transformer.typemap = {"param": typed_field}
transformer.domain = None
transformer.directive = SimpleNamespace(env=None)

transformer.transform(field_list)
print("RESULT=" + repr(document.astext()))
