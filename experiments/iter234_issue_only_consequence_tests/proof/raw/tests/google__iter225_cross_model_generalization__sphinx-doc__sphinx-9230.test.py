from sphinx.util.docfields import DocFieldTransformer, nodes
from sphinx.domains.python import PyObject

def test_docfield_parsing():
    class MockConfig:
        python_use_unqualified_type_names = False

    class MockApp:
        config = MockConfig()

    class MockEnv:
        def __init__(self):
            self.app = MockApp()
            self.ref_context = {}
            self.domaindata = {}
            self.config = MockConfig()

        def get_domain(self, name):
            class MockDomain:
                name = 'py'
            return MockDomain()

    class MockDirective:
        def __init__(self):
            self.env = MockEnv()
            self.domain = 'py'
            self.doc_field_types = PyObject.doc_field_types
            self.state = None

        def get_source_info(self):
            return ('<string>', 1)

    node = nodes.field_list()
    field = nodes.field()
    # The problematic input which triggered the parsing bug.
    field += nodes.field_name('', 'param dict(str, str) opc_meta')
    field_body = nodes.field_body()
    field_body += nodes.paragraph('', '(optional)')
    field += field_body
    node += field
    
    transformer = DocFieldTransformer(MockDirective())
    transformer.transform_all(node)
    
    # After transformation, find the parameter name which is rendered in strong emphasis.
    strong_nodes = list(node.findall(nodes.strong)) if hasattr(node, 'findall') else list(node.traverse(nodes.strong))
    if not strong_nodes:
        raise AssertionError("No strong node found. The field list was not transformed properly.")
        
    param_name = strong_nodes[0].astext()
    
    # Assert that the type and parameter name were correctly split.
    if param_name == "opc_meta":
        print(f"RESULT={('PASS',)!r}")
    elif param_name == "str) opc_meta":
        print(f"RESULT={('FAIL', 'Field name improperly split: parsed as `str) opc_meta`')!r}")
    else:
        print(f"RESULT={('FAIL', f'Unexpected parameter name: {param_name}')!r}")

if __name__ == "__main__":
    try:
        test_docfield_parsing()
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")
