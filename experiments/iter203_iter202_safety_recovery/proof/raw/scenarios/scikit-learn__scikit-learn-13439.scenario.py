from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("none", None),
    ("passthrough", "passthrough"),
    ("kept", "kept"),
])

result = (list(pipe._iter()), len(pipe), Pipeline.__len__.__doc__)
print("RESULT=" + repr(result))
