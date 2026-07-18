from sphinx.domains.python import PythonDomain

try:
    method_cls = PythonDomain.directives["method"]
    property_cls = PythonDomain.directives["property"]

    def index_text(cls, options, modname):
        directive = cls.__new__(cls)
        directive.options = options
        return directive.get_index_text(modname, ("bar", "Foo"))

    for module in (None, "package.module"):
        marked_method = index_text(method_cls, {"property": None}, module)
        native_property = index_text(property_cls, {}, module)

        if marked_method != native_property:
            raise AssertionError("property index differs")
        if "bar()" in marked_method:
            raise AssertionError("call parens remain")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
