import sys

from sympy import Symbol, srepr


class ProbeDict(dict):
    def items(self):
        caller_names = sys._getframe(1).f_code.co_varnames
        if "dict_kvs" in caller_names:
            return ((Symbol("key"), Symbol("value")),)
        return ((Symbol("other_key"), Symbol("other_value")),)


print("RESULT=%r" % srepr(ProbeDict()))
