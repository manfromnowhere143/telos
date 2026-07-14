import numpy as np
import pandas as pd
from xarray.core.variable import as_compatible_data


class DistinctDataFrame(pd.DataFrame):
    @property
    def values(self):
        return np.array([["from_values"]], dtype=object)

    def __array__(self, dtype=None, copy=None):
        return np.array([["from_array"]], dtype=dtype if dtype is not None else object)


result = as_compatible_data(DistinctDataFrame([[0]]))
print("RESULT=" + repr(result.tolist()))
