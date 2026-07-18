try:
    from types import SimpleNamespace
    from sphinx.domains.python import PyObject

    env = SimpleNamespace(ref_context={})
    probe = object.__new__(PyObject)
    inputs = ("bytes | str", "bytes|str", "list[bytes | str]", "bytes | str | None")
    observed = tuple(
        (
            target,
            tuple(
                (type(node).__name__, node.astext())
                for node in PyObject.make_xrefs(probe, "class", "py", target, env=env)
            ),
        )
        for target in inputs
    )
    print(f"RESULT={observed!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
