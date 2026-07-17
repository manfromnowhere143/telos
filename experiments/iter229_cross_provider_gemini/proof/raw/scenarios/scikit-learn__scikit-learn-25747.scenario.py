import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

data = pd.DataFrame({"value": [1]}, index=["preserved"])
wrapped = _wrap_in_pandas_container(data, index=["replacement"])

print(f"RESULT={wrapped.index.tolist()!r}")
