import matplotlib

matplotlib.use("Agg", force=True)

from matplotlib.figure import Figure

fig = Figure(dpi=123)
fig.__dict__.pop("_original_dpi", None)
state = fig.__getstate__()

print("RESULT=" + repr(state["_dpi"]))
