from sphinx.domains.python import PyMethod

obj = object.__new__(PyMethod)
obj.options = {'property': None}
print("RESULT=%r" % obj.get_index_text('', ('bar', 'Foo')))
