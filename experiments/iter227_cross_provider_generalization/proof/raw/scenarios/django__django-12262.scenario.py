from django.template.library import parse_bits


class MinimalParser:
    def compile_filter(self, token):
        return "compiled:" + token


try:
    result = parse_bits(
        MinimalParser(),
        ["flag=1"],
        [],
        None,
        None,
        [],
        ["flag"],
        {"flag": "default"},
        False,
        "probe",
    )
except Exception as exc:
    result = ("raised", type(exc).__name__, str(exc))

print("RESULT=" + repr(result))
