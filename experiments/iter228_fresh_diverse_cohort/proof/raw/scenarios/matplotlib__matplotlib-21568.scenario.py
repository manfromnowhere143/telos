import matplotlib

matplotlib.use("Agg", force=True)

from matplotlib.dates import _wrap_in_tex

print(f"RESULT={_wrap_in_tex('1 2')!r}")
