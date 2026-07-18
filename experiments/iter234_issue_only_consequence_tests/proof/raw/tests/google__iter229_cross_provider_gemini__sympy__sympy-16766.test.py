import sympy

def main():
    try:
        p = sympy.IndexedBase("p")
        i = sympy.Symbol("i")
        j = sympy.Symbol("j")
        
        # Test 1D index
        out1 = sympy.pycode(p[0])
        if "Not supported" in out1:
            print(f"RESULT={('FAIL', 'Comment about not supported still present in 1D index')!r}")
            return
        if out1 != "p[0]":
            print(f"RESULT={('FAIL', f'Expected p[0], got {out1}')!r}")
            return
            
        # Test 2D index
        out2 = sympy.pycode(p[i, j])
        if "Not supported" in out2:
            print(f"RESULT={('FAIL', 'Comment about not supported still present in 2D index')!r}")
            return
        if out2 not in ("p[i, j]", "p[(i, j)]"):
            print(f"RESULT={('FAIL', f'Expected p[i, j], got {out2}')!r}")
            return

        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
