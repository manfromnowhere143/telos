import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

data = pd.DataFrame({"x": [1]}, index=["original"])
result = _wrap_in_pandas_container(
    data, columns=None, index=pd.Index(["replacement"])
)

print(f"RESULT={repr((result.index.tolist(), 'index is ignored if' in _wrap_in_pandas_container.__doc__))}")
