from sympy import Product, symbols

n, k = symbols("n k")
result = Product(n + 1 / 2**k, (k, 0, n - 1)).doit()
print("RESULT=" + repr(result.subs(n, 2)))
