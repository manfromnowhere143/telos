import matplotlib

matplotlib.use("Agg", force=True)

from matplotlib.figure import Figure

ax = Figure().subplots()
collection = ax.hexbin(
    [0.0],
    [0.0],
    C=[7.0],
    gridsize=(1, 1),
    extent=(-1.0, 1.0, -1.0, 1.0),
    mincnt=1,
    reduce_C_function=sum,
)

print(f"RESULT={tuple(float(value) for value in collection.get_array())!r}")
