from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_union
from sklearn.datasets import load_iris
from sklearn import set_config

class AggTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        # Aggregate the data, returning a DataFrame with a different index and length
        return X[['sepal length (cm)']].groupby(X['group']).sum()

try:
    # Rely on sklearn's public API to obtain a pandas DataFrame without importing pandas
    iris = load_iris(as_frame=True)
    X = iris.data.head(4).copy()
    X['group'] = ['A', 'A', 'B', 'B']
    
    # Trigger the scenario from the issue
    set_config(transform_output="pandas")
    
    union = make_union(AggTransformer())
    
    # Prior to the fix, this raised a ValueError because the pandas output wrapper
    # attempted to force the original input's index (length 4) onto the output (length 2).
    res = union.fit_transform(X)
    
    # Assertions to ensure the aggregation and index are preserved correctly
    if res.shape[0] != 2:
        print(f"RESULT={('FAIL', f'Expected 2 rows after aggregation, got {res.shape[0]}')!r}")
    elif list(res.index) != ['A', 'B']:
        print(f"RESULT={('FAIL', f'Expected index [\"A\", \"B\"], got {list(res.index)}')!r}")
    else:
        print(f"RESULT={('PASS',)!r}")

except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
