from docutils import nodes
from sphinx.util.docfields import DocFieldTransformer, TypedField

typed_field = TypedField(
    'parameter',
    names=('param',),
    typenames=('type',),
    label='Parameters',
    rolename=None,
    typerolename=None,
    can_collapse=True,
)


class Domain:
    name = 'test'


class Directive:
    domain = Domain()

    def get_field_type_map(self):
        return {'param': (typed_field, False)}


field_list = nodes.field_list()
field_list += nodes.field(
    '',
    nodes.field_name('', 'param list of str value'),
    nodes.field_body('', nodes.paragraph('', 'description')),
)

root = nodes.container()
root += field_list

DocFieldTransformer(Directive()).transform(field_list)

print('RESULT=' + repr(root.astext()))
