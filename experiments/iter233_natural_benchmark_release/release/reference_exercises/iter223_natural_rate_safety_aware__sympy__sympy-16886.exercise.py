import sympy.crypto.crypto as crypto

try:
    samples = ["1", "0", "2", "A1B", "----", ".----"]
    result = tuple((s, crypto.encode_morse(s)) for s in samples)
    print("RESULT=" + repr(result))
except Exception as e:
    print("RESULT=" + repr(("ERROR", type(e).__name__)))
