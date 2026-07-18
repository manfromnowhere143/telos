from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin

class DummyTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return X

class DummyEstimator(BaseEstimator):
    def fit(self, X, y=None):
        return self
    def predict(self, X):
        return X

def main():
    pipe = Pipeline([
        ('t1', DummyTransformer()),
        ('t2', DummyTransformer()),
        ('est', DummyEstimator())
    ])
    
    try:
        n_steps = len(pipe)
    except Exception as e:
        return ('FAIL', f"len(pipe) raised {type(e).__name__}")

    if n_steps != 3:
        return ('FAIL', f"Expected length 3, got {n_steps}")
        
    try:
        sliced_pipe = pipe[:n_steps]
    except Exception as e:
        return ('FAIL', f"Slicing pipe[:len(pipe)] raised {type(e).__name__}")
        
    if len(sliced_pipe) != 3:
        return ('FAIL', f"Sliced length expected 3, got {len(sliced_pipe)}")

    pipe_short = Pipeline([('est', DummyEstimator())])
    if len(pipe_short) != 1:
        return ('FAIL', f"Expected length 1 for 1-step pipeline, got {len(pipe_short)}")

    return ('PASS',)

try:
    result = main()
    print(f"RESULT={result!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
