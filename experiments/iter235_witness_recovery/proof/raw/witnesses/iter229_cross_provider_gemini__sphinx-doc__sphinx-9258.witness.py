import types

try:
    import sphinx.domains.python as python_domain

    if not hasattr(python_domain, "PyObject"):
        raise AttributeError("PyObject")

    py_object = python_domain.PyObject
    env = types.SimpleNamespace(ref_context={})

    class Probe:
        pass

    probe = Probe()
    probe.env = env

    if not hasattr(py_object, "make_xref"):
        raise AttributeError("make_xref")
    Probe.make_xref = py_object.make_xref

    target = "bytes | or str"
    if hasattr(py_object, "make_xrefs"):
        output = py_object.make_xrefs(probe, "class", "py", target, env=env)
    else:
        output = [py_object.make_xref(probe, "class", "py", target, env=env)]

    refs = []
    for node in output:
        if hasattr(node, "get"):
            value = node.get("reftarget")
            if value is not None:
                refs.append(value)
    result = tuple(refs)
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print("RESULT=" + repr(result))
