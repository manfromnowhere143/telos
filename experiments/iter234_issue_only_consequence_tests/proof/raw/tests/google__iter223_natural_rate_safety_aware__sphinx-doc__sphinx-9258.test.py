from sphinx.domains.python import PythonDomain

def check_issue():
    # Find the parameter field from PythonDomain's directives which parses doc fields like :type:
    param_field = next((f for d in PythonDomain.directives.values()
                        if hasattr(d, 'doc_field_types')
                        for f in d.doc_field_types if f.name == 'parameter'), None)
    if not param_field:
        return ('FAIL', 'No parameter field found in PythonDomain directives')

    class MockCfg:
        def __getattr__(self, name): return False

    class MockEnv:
        name = 'py'
        config, domaindata, app, project, ref_context = MockCfg(), {'py': {}}, None, None, {}
        def get_domain(self, name): return self

    # Evaluate how the field parses a union type string like 'bytes | str'
    try:
        res = param_field.make_xref('class', 'py', 'bytes | str', env=MockEnv())
    except TypeError:
        # Fallback for older versions where make_xref might not accept 'env'
        res = param_field.make_xref('class', 'py', 'bytes | str')
    
    res = res if isinstance(res, list) else [res]
        
    def has_txt(nlist, text):
        for n in nlist:
            if isinstance(n, str) and n.strip() == text:
                return True
            if hasattr(n, 'astext') and n.astext().strip() == text:
                return True
            if has_txt(getattr(n, 'children', []), text):
                return True
        return False
        
    # If correctly implemented, the union is parsed and 'bytes' and 'str' are distinct node entities
    if has_txt(res, 'bytes') and has_txt(res, 'str'):
        return ('PASS',)
    
    astexts = [n.astext() if hasattr(n, 'astext') else str(n) for n in res]
    return ('FAIL', f'Union type not parsed properly. astexts: {astexts}')

if __name__ == '__main__':
    try:
        print(f"RESULT={check_issue()!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")
