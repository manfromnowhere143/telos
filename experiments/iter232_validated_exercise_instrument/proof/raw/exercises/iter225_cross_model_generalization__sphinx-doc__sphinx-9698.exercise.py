try:
    from types import SimpleNamespace
    from sphinx.domains.python import PyMethod

    directive = SimpleNamespace(options={'property': None})
    result = (
        PyMethod.get_index_text(directive, '', ('bar', 'Foo')),
        PyMethod.get_index_text(directive, 'pkg', ('bar', 'Foo')),
    )
    print('RESULT=' + repr(result))
except Exception as exc:
    print('RESULT=' + repr(('ERROR', type(exc).__name__)))
