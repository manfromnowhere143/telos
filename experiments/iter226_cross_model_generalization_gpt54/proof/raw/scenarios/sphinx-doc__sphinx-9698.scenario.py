from types import SimpleNamespace

from sphinx.domains.python import PyMethod

obj = object.__new__(PyMethod)
obj.options = {'property': True}
obj.env = SimpleNamespace(config=SimpleNamespace(add_module_names=True))

result = obj.get_index_text('pkg', ('value', 'Widget'))
print('RESULT=' + repr(result))
