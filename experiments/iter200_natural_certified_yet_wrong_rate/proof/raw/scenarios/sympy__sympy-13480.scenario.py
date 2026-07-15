from sympy import Symbol, coth, log, tan

x = Symbol("x")
result = coth(log(tan(x))).subs(x, 2)
print("RESULT=" + repr(result))
