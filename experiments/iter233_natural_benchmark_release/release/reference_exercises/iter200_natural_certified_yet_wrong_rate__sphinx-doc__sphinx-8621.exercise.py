from sphinx.builders.html.transforms import KeyboardTransform

try:
    samples = ("-", "+", "^", "Shift-+", "Alt+^",
               "Ctrl-+-Shift", "Ctrl-^-Shift", "Ctrl---Shift")
    result = tuple((value, tuple(KeyboardTransform.pattern.split(value)))
                   for value in samples)
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
