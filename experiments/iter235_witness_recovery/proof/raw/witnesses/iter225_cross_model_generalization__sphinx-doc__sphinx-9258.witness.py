try:
    from types import SimpleNamespace
    from sphinx.domains.python import PyObject

    if not hasattr(PyObject, "make_xrefs"):
        raise RuntimeError("make_xrefs unavailable")

    obj = object.__new__(PyObject)
    env = SimpleNamespace(ref_context={})
    nodes = obj.make_xrefs("class", "py", "bytes|or str", env=env)

    observed = []
    for node in nodes:
        text = node.astext() if hasattr(node, "astext") else str(node)
        target = node.get("reftarget") if hasattr(node, "get") else None
        observed.append((type(node).__name__, text, target))
    result = observed
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
