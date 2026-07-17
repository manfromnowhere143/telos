from sphinx.domains.python import PyMethod

obj = PyMethod.__new__(PyMethod)
obj.options = {'property': True}
result = obj.get_index_text('module', ('method', 'Class'))
print(f"RESULT={result!r}")
