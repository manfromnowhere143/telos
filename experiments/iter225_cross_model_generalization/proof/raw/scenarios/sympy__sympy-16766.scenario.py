from sympy import Indexed, Symbol, pycode

base = Symbol("A")
index = Symbol("i")
expr = Indexed(base, index)
result = pycode(expr, symbol_names={base: "mapped"})
print("RESULT={!r}".format(result))
