import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
collection = ax.hexbin(
    [0.0, 0.0],
    [0.0, 0.0],
    C=[1.0, 3.0],
    gridsize=2,
    mincnt=2,
)
print("RESULT=" + repr(collection.get_array().tolist()))
