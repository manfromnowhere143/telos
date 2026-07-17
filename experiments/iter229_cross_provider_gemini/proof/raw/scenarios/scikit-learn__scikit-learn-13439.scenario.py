from sklearn.pipeline import Pipeline

pipeline = Pipeline([("step", "transformer")])
print("RESULT=" + repr(list(pipeline._iter())))
