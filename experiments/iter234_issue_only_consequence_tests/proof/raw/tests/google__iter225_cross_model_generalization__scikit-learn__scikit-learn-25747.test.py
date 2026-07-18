import warnings
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_union
from sklearn.datasets import load_iris
from sklearn import set_config

class RowReducer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None, **kwargs):
        return self

    def transform(self, X, y=None):
        # Group by the first column to aggregate data and reduce the number of rows.
        # This will return a new DataFrame with a different index length than X.
        return X.groupby(X.columns[0]).sum()

def main():
    try:
        # load_iris with as_frame=True yields a pandas DataFrame
        dataset = load_iris(as_frame=True)
        # Take a subset so that groupby strictly reduces the number of rows
        X = dataset.data.iloc[:20]
        
        # Configure transform_output to pandas, which triggered the issue
        set_config(transform_output="pandas")
        
        # Create a FeatureUnion with our custom row-reducing transformer
        union = make_union(RowReducer())
        
        # In the buggy version, this raises a ValueError because it tries 
        # to assign the original X's index (length 20) to the aggregated output.
        out = union.fit_transform(X)
        
        # Validation to ensure it actually ran and reduced rows
        if out is None or len(out) == 0:
            print(f"RESULT={('FAIL', 'Output is empty')!r}")
            return
            
        if len(out) == len(X):
            print(f"RESULT={('FAIL', 'Rows were not reduced')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
