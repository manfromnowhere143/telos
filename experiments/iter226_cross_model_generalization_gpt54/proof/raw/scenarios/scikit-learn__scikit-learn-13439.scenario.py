from sklearn.pipeline import Pipeline

pipeline = Pipeline([("step", "active")])
print("RESULT=" + repr(list(pipeline._iter())))
