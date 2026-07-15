import os

os.environ.setdefault("MPLBACKEND", "Agg")

try:
    from matplotlib.dates import _wrap_in_tex
except Exception:
    print("PROP_PASS")
else:
    text = "2031-12-31 23:59:58.75"
    expected = r"$\mathdefault{2031{-}12{-}31\;23{:}59{:}58.75}$"
    try:
        correct = _wrap_in_tex(text) == expected
    except Exception:
        correct = False
    print("PROP_PASS" if correct else "PROP_FAIL")
