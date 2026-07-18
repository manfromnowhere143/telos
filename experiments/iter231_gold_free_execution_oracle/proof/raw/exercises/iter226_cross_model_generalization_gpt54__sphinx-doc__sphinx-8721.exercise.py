import types

from sphinx.ext import viewcode

try:
    def run(builder_name, enabled):
        entry = {
            'code': 'x = 1\n',
            'tags': {},
            'used': True,
            'refname': 'index',
        }
        builder = types.SimpleNamespace(
            name=builder_name,
            env=types.SimpleNamespace(_viewcode_modules={'sample.module': entry}),
            highlighter=types.SimpleNamespace(
                highlight_block=lambda *args, **kwargs: '<pre>x = 1</pre>'
            ),
            get_relative_uri=lambda *args: 'index.html',
        )
        app = types.SimpleNamespace(
            builder=builder,
            config=types.SimpleNamespace(viewcode_enable_epub=enabled),
        )
        return tuple(page[0] for page in viewcode.collect_pages(app))

    result = (
        ('html_disabled', run('html', False)),
        ('epub_disabled', run('epub', False)),
        ('epub_enabled', run('epub', True)),
    )
    print('RESULT=' + repr(result))
except Exception as exc:
    print('RESULT=' + repr(('ERROR', type(exc).__name__)))
