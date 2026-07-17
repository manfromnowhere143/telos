from sympy import I, Symbol

z = Symbol("z", zero=True)
y = Symbol("y", real=True)
expr = z + I*y

print("RESULT=" + repr(expr._eval_is_zero()))
