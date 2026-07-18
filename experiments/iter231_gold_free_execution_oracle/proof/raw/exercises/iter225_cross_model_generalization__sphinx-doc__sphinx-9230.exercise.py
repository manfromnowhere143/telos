from sphinx.util import docfields

try:
    nodes = docfields.nodes

    typed = docfields.TypedField(
        'parameter',
        names=('param',),
        typenames=('type',),
        label='Parameters',
        rolename=None,
        typerolename=None,
    )

    class Directive:
        doc_field_types = [typed]
        domain = None
        env = None

        class state:
            inliner = None

        def get_field_type_map(self):
            return {
                'param': (typed, False),
                'type': (typed, True),
            }

    fields = nodes.field_list()
    for text in (
        'param dict(str, str) opc_meta',
        'param dict(str,str) compact',
        'param dict(list(str, str), str) nested',
    ):
        field = nodes.field()
        field += nodes.field_name('', text)
        field += nodes.field_body('', nodes.paragraph('', '(optional)'))
        fields += field

    root = nodes.container()
    root += fields
    docfields.DocFieldTransformer(Directive()).transform(fields)
    print('RESULT=' + repr(root.astext()))
except Exception as exc:
    print('RESULT=' + repr(('ERROR', type(exc).__name__)))
