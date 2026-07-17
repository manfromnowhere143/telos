from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

pipeline = Pipeline(
    [("skip_passthrough", "passthrough"), ("skip_none", None), ("scale", StandardScaler())]
)

print("RESULT=" + repr(list(pipeline._iter())))
