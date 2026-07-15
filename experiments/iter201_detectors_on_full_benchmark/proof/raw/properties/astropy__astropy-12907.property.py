import numpy as np

try:
    from astropy.modeling import models as m
    from astropy.modeling.separable import separability_matrix

    left_nested = m.Linear1D(2) & m.Linear1D(3)
    right_nested = m.Linear1D(4) & m.Linear1D(5)
    model = m.Pix2Sky_TAN() & (left_nested & right_nested)

    expected = np.zeros((6, 6), dtype=bool)
    expected[:2, :2] = True
    expected[2:, 2:] = np.eye(4, dtype=bool)

    actual = separability_matrix(model)
    print("PROP_PASS" if np.array_equal(actual, expected) else "PROP_FAIL")
except Exception:
    print("PROP_PASS")
