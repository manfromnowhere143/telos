from sympy.printing.latex import LatexPrinter

printer = LatexPrinter({"mul_symbol": r"\;"})
print("RESULT=" + repr((
    printer._settings["mul_symbol_latex"],
    printer._settings["mul_symbol_latex_numbers"],
)))
