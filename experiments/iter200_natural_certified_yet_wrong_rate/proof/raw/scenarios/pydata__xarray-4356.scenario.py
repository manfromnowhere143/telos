import numpy as np
from xarray.core.nanops import _maybe_null_out

_reads = [0]


class FlakyArray(np.ndarray):
    @property
    def ndim(self):
        _reads[0] += 1
        return 1 if _reads[0] == 1 else 0


result = np.asarray([10, 20]).view(FlakyArray)
mask = np.ones((2, 2, 2), dtype=bool)

output = _maybe_null_out(result, axis=(0, 1), mask=mask, min_count=1)
print("RESULT=" + repr(np.asarray(output)))
