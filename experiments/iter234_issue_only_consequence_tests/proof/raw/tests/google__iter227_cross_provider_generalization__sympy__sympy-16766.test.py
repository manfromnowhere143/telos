import sympy as sp

def test_indexed_pycode():
    try:
        p = sp.IndexedBase("p")
        i, j = sp.symbols("i j")
        
        tests = [
            (p[0], "p[0]"),
            (p[0, 1], "p[0, 1]"),
            (p[i, j], "p[i, j]")
        ]
        
        for expr, expected in tests:
            code = sp.pycode(expr)
            
            # The issue indicates that an unsupported comment was previously included
            if "Not supported" in code:
                print(f"RESULT={('FAIL', f'Unsupported warning still present for {expected}')!r}")
                return
            
            # Accommodate minor formatting differences (e.g. spaces after commas)
            if code.replace(" ", "") != expected.replace(" ", ""):
                print(f"RESULT={('FAIL', f'Got {code!r}, expected {expected!r}')!r}")
                return
                
        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    test_indexed_pycode()
