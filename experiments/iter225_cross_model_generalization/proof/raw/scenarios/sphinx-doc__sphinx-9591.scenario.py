from types import SimpleNamespace

from sphinx import addnodes
from sphinx.domains.python import PyObject


class Options(dict):
    def __init__(self):
        super().__init__()
        self.type_calls = 0

    def get(self, key, default=None):
        if key == 'type':
            self.type_calls += 1
            return '[' if self.type_calls == 1 else default
        return super().get(key, default)


env = SimpleNamespace(ref_context={})
obj = PyObject.__new__(PyObject)
obj.state = SimpleNamespace(document=SimpleNamespace(settings=SimpleNamespace(env=env)))
try:
    obj.env = env
except AttributeError:
    pass
obj.options = Options()
obj.objtype = 'object'

signode = addnodes.desc_signature('', '')
obj.handle_signature('target', signode)

result = tuple(
    child.astext()
    for child in signode.children
    if isinstance(child, addnodes.desc_annotation)
)
print(f"RESULT={result!r}")
