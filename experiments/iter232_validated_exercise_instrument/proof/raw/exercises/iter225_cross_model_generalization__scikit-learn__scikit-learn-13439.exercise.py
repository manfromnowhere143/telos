try:
    from sklearn.pipeline import Pipeline
    from sklearn.feature_selection import SelectKBest, f_regression
    from sklearn.svm import SVC

    pipe = Pipeline([
        ("anova", SelectKBest(f_regression, k=5)),
        ("svc", SVC(kernel="linear")),
    ])
    full_slice = pipe[:len(pipe)]
    observed = (
        len(pipe),
        type(full_slice).__name__,
        tuple(name for name, _ in full_slice.steps),
        type(pipe[-1]).__name__,
    )
except Exception as exc:
    observed = ("ERROR", type(exc).__name__)

print(f"RESULT={observed!r}")
