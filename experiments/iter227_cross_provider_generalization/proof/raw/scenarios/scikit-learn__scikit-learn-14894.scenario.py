import warnings
import numpy as np
import scipy.sparse as sp
from sklearn.svm import SVC
import sklearn.svm.base as svm_base

warnings.simplefilter("ignore")

def empty_sparse_train(*args, **kwargs):
    values = (
        np.empty(0, dtype=np.int32),
        sp.csr_matrix((0, 2), dtype=np.float64),
        np.empty(0, dtype=np.float64),
        np.zeros(3, dtype=np.float64),
        np.zeros(3, dtype=np.int32),
        np.empty(0, dtype=np.float64),
        np.empty(0, dtype=np.float64),
        0,
    )
    return values

svm_base.libsvm_sparse.libsvm_sparse_train = empty_sparse_train

X = sp.csr_matrix(np.eye(3, 2, dtype=np.float64))
y = np.array([0, 1, 2])
model = SVC(kernel="linear").fit(X, y)

print("RESULT=" + repr(model.dual_coef_.shape))
