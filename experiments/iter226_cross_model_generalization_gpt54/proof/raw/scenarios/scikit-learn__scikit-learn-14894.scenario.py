import warnings

import numpy as np
from scipy import sparse
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

X = sparse.csr_matrix([[0.0], [1.0]])
y = np.array([0, 1])
clf = SVC(kernel="linear")
clf.fit(X, y, sample_weight=np.zeros(2))

print("RESULT=" + repr(clf.dual_coef_.shape))
