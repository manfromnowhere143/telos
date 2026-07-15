from docutils import nodes
from docutils.utils import new_document
from sphinx.builders.html.transforms import KeyboardTransform

document = new_document("")
node = nodes.literal("", "A-\nB", classes=["kbd"])
document += node

KeyboardTransform(document).run()

def observe(item):
    if isinstance(item, nodes.Element):
        return (
            item.tagname,
            tuple(item.get("classes", ())),
            tuple(observe(child) for child in item.children),
        )
    return str(item)

print("RESULT=" + repr(observe(node)))
