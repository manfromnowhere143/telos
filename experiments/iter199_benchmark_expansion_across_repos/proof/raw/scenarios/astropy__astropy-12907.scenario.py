import numpy as np
from astropy.modeling.separable import _cstack

left = np.eye(1, dtype=bool)
right = np.eye(5, dtype=bool)
right[0, 1] = True

print("RESULT=" + repr(_cstack(left, right).tolist()))
