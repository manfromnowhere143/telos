import sphinx
from types import SimpleNamespace
from sphinx.util import docfields

try:
    field_type = docfields.TypedField(
        'param',
        names=('param',),
        typenames=('type',),
        label='Parameters',
        can_collapse=True,
    )

    class Domain:
        doc_field_types = [field_type]

    directive = SimpleNamespace(
        domain=Domain(),
        env=None,
        state=SimpleNamespace(inliner=None),
    )

    nodes = docfields.nodes
    field = nodes.field(
        '',
        nodes.field_name('', 'param dict(str, str) opc_meta'),
        nodes.field_body('', nodes.paragraph('', '(optional)')),
    )
    root = nodes.container('', nodes.field_list('', field))

    docfields.DocFieldTransformer(directive, root).transform_all(root)
    rendered = root.astext()

    assert 'opc_meta (dict(str, str)) – (optional)' in rendered
    assert 'str) opc_meta (dict(str,' not in rendered
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    detail = 'typed-param-rendering'
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
