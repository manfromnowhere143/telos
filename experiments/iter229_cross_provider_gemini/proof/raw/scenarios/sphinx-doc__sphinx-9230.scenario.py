from types import SimpleNamespace

from docutils import nodes
from sphinx.util.docfields import DocFieldTransformer, TypedField


class Env:
    def __init__(self):
        self.current_document = SimpleNamespace(default_domain=None)

    def get_domain(self, name):
        return None


class Directive:
    def __init__(self):
        self.env = Env()
        self.domain = None
        self.state = SimpleNamespace(inliner=None)
        self.doc_field_types = [
            TypedField(
                'param',
                names=('param',),
                typenames=('type',),
                label='Parameters',
                rolename=None,
                typerolename=None,
            )
        ]


field = nodes.field()
field += nodes.field_name('', 'param tuple[int, str] value')
body = nodes.field_body()
body += nodes.paragraph('', 'description')
field += body

field_list = nodes.field_list()
field_list += field
root = nodes.container()
root += field_list

DocFieldTransformer(Directive()).transform(field_list)

print('RESULT=' + repr(root.astext()))
