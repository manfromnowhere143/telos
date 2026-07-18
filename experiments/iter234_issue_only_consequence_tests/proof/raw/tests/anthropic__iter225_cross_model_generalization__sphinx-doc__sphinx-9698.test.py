try:
    from docutils.frontend import OptionParser
    from docutils.utils import new_document
    from sphinx.domains.python import PyMethod
    from docutils.parsers.rst import Parser as RSTParser

    def get_index_text(objtype, options):
        # Build a minimal document with a directive instance
        settings = OptionParser(components=(RSTParser,)).get_default_values()
        document = new_document('<test>', settings)

        class FakeState:
            def __init__(self):
                self.document = document

        directive = PyMethod(
            name='py:method',
            arguments=['Foo.bar'],
            options=options,
            content=[],
            lineno=1,
            content_offset=0,
            block_text='',
            state=FakeState(),
            state_machine=None,
        )
        directive.env = None
        directive.domain = 'py'
        directive.objtype = 'method'
        return directive.get_index_text('', ('Foo.bar', 'bar'))

    text_prop = get_index_text('method', {'property': True})
    text_method = get_index_text('method', {})

    assert '(' not in text_prop, f"property index has parens: {text_prop!r}"
    assert '(' in text_method, f"method index missing parens: {text_method!r}"

    print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
