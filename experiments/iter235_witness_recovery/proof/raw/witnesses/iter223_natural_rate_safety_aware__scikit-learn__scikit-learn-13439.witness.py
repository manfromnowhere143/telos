try:
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression

    pipe = Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression()),
    ])

    if hasattr(pipe, "__len__"):
        count = len(pipe)
    else:
        count = len(pipe.steps)

    if hasattr(pipe, "__getitem__"):
        subset = pipe[:count]
        names = tuple(name for name, _ in subset.steps)
    else:
        names = tuple(name for name, _ in pipe.steps)

    print(f"RESULT={repr((count, names))}")
except Exception as exc:
    print(f"RESULT={repr(('ERROR', type(exc).__name__))}")
