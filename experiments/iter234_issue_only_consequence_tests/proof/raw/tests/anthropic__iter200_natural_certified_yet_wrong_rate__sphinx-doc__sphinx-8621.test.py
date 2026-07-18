try:
    import re
    from sphinx.testing.util import assert_node
    from docutils import nodes
    from sphinx.util.docutils import docutils_namespace
    from sphinx.application import Sphinx
    from docutils.frontend import OptionParser
    from docutils.utils import new_document
    from docutils.parsers.rst import Parser
    from sphinx.parsers import RSTParser

    # Build minimal machinery to render a kbd role to HTML via the writer.
    # Instead, parse and inspect the doctree nodes.
    from docutils.core import publish_doctree

    def render(rst):
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document('<test>', settings)
        Parser().parse(rst, doc)
        return doc

    # Count kbd nodes (docutils inline with kbd class) by rendering to HTML.
    from sphinx.writers.html import HTMLTranslator

    def count_kbd(rst):
        # Use publish to HTML fragment
        from docutils.core import publish_parts
        parts = publish_parts(rst, writer_name='html')
        body = parts['body']
        return body.count('<kbd')

    detail = None

    # (1) single "-" should produce exactly one kbd element
    c1 = count_kbd(':kbd:`-`')
    if c1 != 1:
        detail = f"single '-' produced {c1} kbd elements"

    # (2) single "+" should produce exactly one kbd element
    c2 = count_kbd(':kbd:`+`')
    if detail is None and c2 != 1:
        detail = f"single '+' produced {c2} kbd elements"

    # (3) Shift-+ : outer kbd + Shift + '+' = 3 kbd elements
    c3 = count_kbd(':kbd:`Shift-+`')
    if detail is None and c3 != 3:
        detail = f"'Shift-+' produced {c3} kbd elements (expected 3)"

    if detail is None:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
