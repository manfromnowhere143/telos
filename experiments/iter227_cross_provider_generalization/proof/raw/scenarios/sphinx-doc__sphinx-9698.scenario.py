from sphinx.domains.python import PyMethod

directive = PyMethod.__new__(PyMethod)
directive.options = {'property': None}
result = directive.get_index_text('pkg', ('Class', 'value'))
print('RESULT=' + repr(result))
