from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

try:
    pipe = Pipeline([("scale", StandardScaler()), ("svc", SVC())])
    full_slice = pipe[:len(pipe)]
    empty = Pipeline([])
    empty_slice = empty[:len(empty)]
    print("RESULT=%r" % (
        len(pipe),
        type(full_slice).__name__,
        tuple(name for name, _ in full_slice.steps),
        len(empty),
        type(empty_slice).__name__,
        tuple(empty_slice.steps),
    ))
except Exception as exc:
    print("RESULT=%r" % (("ERROR", type(exc).__name__),))
