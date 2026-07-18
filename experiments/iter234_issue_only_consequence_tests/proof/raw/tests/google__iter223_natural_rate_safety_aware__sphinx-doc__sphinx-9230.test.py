from sphinx.util.docfields import DocFieldTransformer, nodes
from sphinx.domains.python import PyObject

def test():
    class MockEnv:
        ref_context = {}
        config = type('MockConfig', (), {
            'strip_signature_backslash': False, 
            'add_function_parentheses': True
        })()
        def get_domain(self, name):
            return type('MockDomain', (), {'name': 'py'})()

    class MockDirective:
        domain, name, objtype = 'py', 'function', 'function'
        env = MockEnv()
        state = type('MockState', (), {
            'document': type('MockDoc', (), {
                'current_source': 'test.py', 
                'current_line': 1, 
                'settings': type('Settings', (), {'language_code': 'en'})()
            })()
        })()
        def get_field_type_map(self):
            return {n: f for f in PyObject.doc_field_types for n in f.names}

    transformer = DocFieldTransformer(MockDirective())
    
    field_list = nodes.field_list()
    field_list.document = MockDirective.state.document
    
    field = nodes.field()
    # The docutils-parsed field name for `:param dict(str, str) opc_meta:`
    field += nodes.field_name('', 'param dict(str, str) opc_meta')
    field += nodes.field_body('', nodes.paragraph('', '(optional)'))
    field_list += field
    
    transformer.transform_all(field_list)
    
    txt = field_list.astext().replace('\n', ' ')
    
    if 'str) opc_meta' in txt or 'dict(str,' in txt:
        return ('FAIL', f"Incorrect parse: {txt}")
    if 'dict(str, str)' not in txt:
        return ('FAIL', f"Type missing or malformed: {txt}")
    if 'opc_meta' not in txt:
        return ('FAIL', f"Name missing: {txt}")
        
    return ('PASS',)

try:
    print(f"RESULT={test()!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
