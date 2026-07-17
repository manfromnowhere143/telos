from sphinx.domains.python import PyObject


class Env:
    ref_context = {}


class Probe:
    make_xref = PyObject.make_xref


env = Env()
probe = Probe()
probe.env = env

result = PyObject.make_xrefs(probe, "class", "py", "A|or B", env=env)
observable = [
    (
        type(node).__name__,
        node.astext(),
        node.get("reftarget") if hasattr(node, "get") else None,
    )
    for node in result
]
print("RESULT=" + repr(observable))
