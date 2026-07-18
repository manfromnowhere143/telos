import re
from sphinx.util.docfields import DocFieldTransformer, TypedField, nodes

try:
    class Directive:
        domain = 'py'
        objtype = 'function'
        env = None

        def get_field_type_map(self):
            field = TypedField(
                'parameter',
                label='Parameters',
                names=('param',),
                typenames=('type',),
                can_collapse=True,
            )
            return {'param': (field, False)}

    def render(specification):
        field = nodes.field(
            '',
            nodes.field_name('', f'param {specification}'),
            nodes.field_body('', nodes.paragraph('', '(optional)')),
        )
        fields = nodes.field_list('', field)
        root = nodes.container('', fields)
        DocFieldTransformer(Directive()).transform(fields)
        return re.sub(r'\s+', '', root.astext())

    simple = render('dict(str, str) opc_meta')
    nested = render('dict(str, tuple(int, str)) metadata')

    assert 'opc_meta(dict(str,str))–(optional)' in simple, 'simple'
    assert 'metadata(dict(str,tuple(int,str)))–(optional)' in nested, 'nested'
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or 'assertion'
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
