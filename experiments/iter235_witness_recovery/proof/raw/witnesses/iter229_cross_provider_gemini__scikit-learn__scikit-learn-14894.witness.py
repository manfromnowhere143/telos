import numpy as np
from scipy import sparse
from sklearn.svm import SVC

try:
    if not hasattr(SVC, "fit"):
        raise AttributeError("fit")

    X = sparse.csr_matrix(np.eye(3, dtype=float))
    y = np.array([0, 1, 2])
    sample_weight = np.zeros(3, dtype=float)

    model = SVC(kernel="linear", C=1.0)
    if not hasattr(model, "fit"):
        raise AttributeError("fit")

    model.fit(X, y, sample_weight=sample_weight)

    if not hasattr(model, "dual_coef_"):
        raise AttributeError("dual_coef_")

    result = (model.dual_coef_.shape, model.dual_coef_.nnz)
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
