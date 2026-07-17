from types import SimpleNamespace

from sphinx import addnodes
from sphinx.domains import python as py


env = SimpleNamespace(
    ref_context={},
    config=SimpleNamespace(python_display_short_literal_types=False),
)
directive = object.__new__(py.PyVariable)
directive.options = {'type': 'list[Widget]'}
directive.state = SimpleNamespace(
    document=SimpleNamespace(settings=SimpleNamespace(env=env))
)

signode = addnodes.desc_signature()
py.PyVariable.handle_signature(directive, 'sample', signode)

annotations = [
    child for child in signode.children
    if isinstance(child, addnodes.desc_annotation)
]
result = tuple(
    (
        annotation.astext(),
        tuple(
            xref.get('reftarget')
            for xref in annotation.findall(addnodes.pending_xref)
        ),
    )
    for annotation in annotations
)
print("RESULT=" + repr(result))
