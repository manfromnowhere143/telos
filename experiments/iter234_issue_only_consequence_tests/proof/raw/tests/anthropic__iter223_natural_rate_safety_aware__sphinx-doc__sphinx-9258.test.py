try:
    from sphinx.domains.python import _pseudo_parse_arglist  # noqa
    import re
    from docutils.frontend import OptionParser
    from docutils.utils import new_document
    from docutils.parsers.rst import Parser
    from sphinx.util.docutils import docutils_namespace
    import sphinx

    # Build a small rst doc using an info field list with a piped type.
    rst = (
        ".. py:function:: foo(text)\n"
        "\n"
        "   :param text: a text\n"
        "   :type text: bytes | str\n"
    )

    from docutils.parsers.rst import Parser as RSTParser
    from docutils import nodes
    from sphinx.testing.util import SphinxTestApp  # public-ish testing helper
    raise ImportError("skip heavy path")
except Exception:
    pass

try:
    from docutils import nodes
    from docutils.parsers.rst import Parser
    from docutils.frontend import OptionParser
    from docutils.utils import new_document
    from sphinx.domains.python import PyObject, PyXrefMixin

    # Use PyXrefMixin.make_xrefs to parse a piped type string; a correct
    # implementation should split "bytes | str" into cross-references for
    # both "bytes" and "str", separated by a literal " | ".
    mixin = PyXrefMixin()

    result = mixin.make_xrefs(
        rolename='class',
        domain='py',
        target='bytes | str',
        innernode=nodes.emphasis,
        env=None,
    )

    text = ''.join(n.astext() for n in result)
    # Collect the cross-reference target names.
    xref_targets = [
        n.get('reftarget') for n in result
        if isinstance(n, nodes.Element) and n.get('reftarget')
    ]

    assert 'bytes' in xref_targets, f"bytes missing: {xref_targets}"
    assert 'str' in xref_targets, f"str missing: {xref_targets}"
    assert '|' in text, f"no pipe in output: {text!r}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
