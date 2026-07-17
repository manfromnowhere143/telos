import pandas as pd
from xarray.core.variable import as_compatible_data

result = as_compatible_data(pd.Index([1, 2]))
print("RESULT=" + repr(result))
