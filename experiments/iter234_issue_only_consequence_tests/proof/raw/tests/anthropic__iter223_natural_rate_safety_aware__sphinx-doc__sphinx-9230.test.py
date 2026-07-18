try:
    from docutils import frontend, nodes, utils
    from docutils.parsers.rst import Parser
    from sphinx.util.docfields import _split_type_and_name  # may not exist

    detail = None

    # Build a minimal doctree with an info field list using the type in name form
    from sphinx.testing.util import SphinxTestApp
    raise ImportError("skip heavy path")
except Exception:
    pass

try:
    import re
    from docutils.frontend import OptionParser
    from docutils.utils import new_document
    from docutils.parsers.rst import Parser
    from sphinx.domains.python import PythonDomain
    from sphinx.util.docutils import docutils_namespace

    settings = OptionParser(components=(Parser,)).get_default_values()
    rst = (
        ".. py:function:: foo(opc_meta)\n"
        "\n"
        "   :param dict(str, str) opc_meta: (optional)\n"
    )
    doc = new_document("<test>", settings)
    Parser().parse(rst, doc)

    text = doc.astext()
    # The parameter name must survive intact and the type must be dict(str, str)
    ok_name = "opc_meta" in text
    # Broken rendering would split type: "str) opc_meta" and "dict(str,"
    broken = "str) opc_meta" in text or "dict(str,)" in text
    has_type = "dict(str, str)" in text or "dict(str,str)" in text

    if not ok_name:
        detail = "name missing"
    elif broken:
        detail = "type incorrectly split"
    elif not has_type:
        detail = "type not rendered"

    if detail:
        print(f"RESULT={('FAIL', detail)!r}")
    else:
        print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
