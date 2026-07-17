from types import SimpleNamespace

from sphinx import addnodes
from sphinx.domains.python import PyVariable


class Config:
    def __getattr__(self, name):
        return False


env = SimpleNamespace(ref_context={}, config=Config())
state = SimpleNamespace(
    document=SimpleNamespace(settings=SimpleNamespace(env=env))
)

directive = PyVariable.__new__(PyVariable)
directive.state = state
directive.options = {"type": "int"}

signode = addnodes.desc_signature("", "")
directive.handle_signature("x", signode)

print("RESULT=" + repr(signode.astext()))
