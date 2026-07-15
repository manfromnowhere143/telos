import numpy as np
from scipy import sparse
from sklearn.svm import SVR

X = sparse.csr_matrix(
    np.array(
        [
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )
)
y = np.array([0.04, 0.04, 0.10, 0.16])

model = SVR(
    C=316.227766017,
    epsilon=0.1,
    gamma=1.0,
    kernel="linear",
    max_iter=15000,
    tol=0.001,
)
model.fit(X, y)

coef = getattr(model, "dual_coef_", None)
result = None if coef is None else (tuple(coef.shape), coef.nnz)
print("RESULT=" + repr(result))
