import warnings
warnings.filterwarnings("ignore")

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import StandardScaler
from sklearn import set_config

class AggTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
        
    def transform(self, X, y=None):
        # Aggregates data, returning a DataFrame with fewer rows than input X
        return X.groupby("x1")[["x0"]].sum()
        
    def get_feature_names_out(self, input_features=None):
        return ["x0"]

try:
    # Globally configure output as pandas, just as the issue describes
    set_config(transform_output="pandas")
    
    # We use StandardScaler to generate a pandas DataFrame without importing pandas directly.
    # By default, for a 2D array, the features are named 'x0' and 'x1'.
    scaler = StandardScaler(with_mean=False, with_std=False)
    data = scaler.fit_transform([
        [10.0, 0.0], [20.0, 0.0], 
        [10.0, 1.0], [20.0, 1.0], 
        [10.0, 2.0], [20.0, 2.0]
    ])
    
    # FeatureUnion combines the transformers.
    # The bug attempts to overwrite the aggregated output's index with the original 
    # input's index, throwing a ValueError due to length mismatch.
    union = FeatureUnion([("agg", AggTransformer())])
    res = union.fit_transform(data)
    
    # Assertions to verify correct behaviour post-fix
    if len(res) != 3:
        raise AssertionError(f"Expected 3 rows in aggregated result, got {len(res)}")
        
    idx = [int(x) for x in res.index]
    if idx != [0, 1, 2]:
        raise AssertionError(f"Index mismatch: expected [0, 1, 2], got {idx}")
        
    if "agg__x0" not in res.columns:
        raise AssertionError(f"Missing column 'agg__x0', got columns: {list(res.columns)}")
        
    vals = [int(x) for x in res["agg__x0"]]
    if vals != [30, 30, 30]:
        raise AssertionError(f"Value mismatch: expected [30, 30, 30], got {vals}")
        
    print(f"RESULT={('PASS',)!r}")
    
except AssertionError as e:
    print(f"RESULT={('FAIL', str(e))!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
