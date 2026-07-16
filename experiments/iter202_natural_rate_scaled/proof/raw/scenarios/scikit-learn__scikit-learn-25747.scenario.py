import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

data = pd.DataFrame({"value": [1]}, index=pd.Index(["original"]))
result = _wrap_in_pandas_container(
    data,
    columns=None,
    index=pd.Index(["replacement"]),
)

print(f"RESULT={result.index.tolist()!r}")
