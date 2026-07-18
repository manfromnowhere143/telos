import sympy as sp

def test():
    try:
        m, n = sp.symbols('m n')
        eq = n**4 + m**4 - 2**4 - 3**4
        expected = {(-3, -2), (-3, 2), (-2, -3), (-2, 3), (2, -3), (2, 3), (3, -2), (3, 2)}
        
        res1 = sp.diophantine(eq, syms=(m, n), permute=True)
        res2 = sp.diophantine(eq, syms=(n, m), permute=True)
        
        if res1 != expected:
            print(f"RESULT={('FAIL', f'syms=(m,n) returned {len(res1)} elements, expected 8')!r}")
            return
            
        if res2 != expected:
            print(f"RESULT={('FAIL', f'syms=(n,m) returned {len(res2)} elements, expected 8')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    test()
