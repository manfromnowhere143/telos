from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest
from sklearn.linear_model import LogisticRegression

try:
    pipe = Pipeline([
        ("scale", StandardScaler()),
        ("select", SelectKBest(k=1)),
        ("model", LogisticRegression()),
    ])

    assert len(pipe) == 3, "wrong length"

    whole = pipe[:len(pipe)]
    assert isinstance(whole, Pipeline), "slice not pipeline"
    assert [name for name, _ in whole.steps] == [
        "scale", "select", "model"
    ], "full slice wrong"

    tail = pipe[len(pipe) - 1:]
    assert len(tail) == 1, "tail length"
    assert tail.steps[0][0] == "model", "tail step"

    empty = pipe[:0]
    assert isinstance(empty, Pipeline), "empty not pipeline"
    assert len(empty) == 0, "empty length"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
