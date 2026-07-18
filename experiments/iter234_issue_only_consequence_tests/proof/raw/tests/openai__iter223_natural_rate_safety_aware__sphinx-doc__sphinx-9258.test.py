try:
    from sphinx import addnodes
    from sphinx.domains.python import PyTypedField

    try:
        field = PyTypedField(
            'parameter',
            names=('param',),
            typenames=('type',),
            label='Parameters',
            rolename='obj',
            typerolename='class',
        )
        text = 'bytes | str | int'
        content = addnodes.literal_emphasis('', text)
        result = field.make_xrefs(
            'class', 'py', text, addnodes.literal_emphasis, content
        )

        targets = []

        def visit(node):
            if hasattr(node, 'get'):
                target = node.get('reftarget')
                if target is not None:
                    targets.append(target)
            for child in getattr(node, 'children', ()):
                visit(child)

        for node in result:
            visit(node)

        assert targets == ['bytes', 'str', 'int']
        print(f"RESULT={('PASS',)!r}")
    except AssertionError:
        print(f"RESULT={('FAIL', 'union targets')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
