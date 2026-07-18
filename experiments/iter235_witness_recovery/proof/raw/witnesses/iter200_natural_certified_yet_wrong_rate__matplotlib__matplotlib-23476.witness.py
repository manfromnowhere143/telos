try:
    import matplotlib

    matplotlib.use("Agg", force=True)
    from matplotlib.figure import Figure

    matplotlib.rcParams["figure.dpi"] = 123
    figure = Figure()
    figure.__dict__.pop("_original_dpi", None)

    if hasattr(figure, "__getstate__"):
        state = figure.__getstate__()
        result = ("OK", state.get("_dpi") == 123)
    else:
        result = ("ERROR", "AttributeError")
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
