import matplotlib

matplotlib.use("Agg")

from matplotlib.dates import _wrap_in_tex

print("RESULT=" + repr(_wrap_in_tex("1 2 3")))
