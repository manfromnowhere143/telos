from sphinx.domains.python import PyXRefRole

nodes = PyXRefRole().make_xrefs("class", "py", "Alpha | Beta")
print("RESULT=" + repr(nodes))
