try:
    from sphinx import addnodes
    from sphinx.domains.python import PyFunction
    from sphinx.util.docfields import DocFieldTransformer

    nodes = addnodes.nodes

    class Domain:
        def role(self, name):
            def make_role(*args, **kwargs):
                return ([nodes.Text(args[2])], [])
            return make_role

    class State:
        inliner = None

    class Directive:
        doc_field_types = PyFunction.doc_field_types
        state = State()

    fields = nodes.field_list()
    field = nodes.field()
    field += nodes.field_name("", "param dict(str, str) opc_meta")
    field += nodes.field_body("", nodes.paragraph("", "(optional)"))
    fields += field

    container = nodes.container("", fields)
    DocFieldTransformer(Directive(), Domain(), None).transform(fields)
    observed = container.astext()
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
