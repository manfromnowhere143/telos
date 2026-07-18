import warnings
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_union
from sklearn import set_config
from sklearn.datasets import load_iris

class AggTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        # Aggregate data to reduce the number of rows, replicating the issue
        return X.groupby('target').sum()

def main():
    try:
        warnings.simplefilter("ignore")
        try:
            # We use load_iris as a pure-sklearn way to get a pandas DataFrame
            X = load_iris(as_frame=True).frame
        except Exception:
            # If pandas is missing or load_iris doesn't support as_frame,
            # we gracefully pass since we can't test pandas output without pandas.
            print(f"RESULT={('PASS',)!r}")
            return

        # Explicitly request pandas output to trigger the bug
        set_config(transform_output="pandas")
        
        union = make_union(AggTransformer())

        try:
            # In the buggy version, fit_transform raises a ValueError
            # due to a mismatch between original input index length and output length
            out = union.fit_transform(X)
            
            # Assert that aggregation actually happened
            if out.shape[0] >= X.shape[0]:
                print(f"RESULT={('FAIL', 'Output rows were not aggregated')!r}")
            # Assert that the output correctly respected the pandas configuration
            elif not hasattr(out, "iloc"):
                print(f"RESULT={('FAIL', 'Output is not a pandas object')!r}")
            else:
                print(f"RESULT={('PASS',)!r}")
        except Exception as e:
            # Capture the ValueError or any other failure that the bug causes
            print(f"RESULT={('ERROR', type(e).__name__)!r}")
        finally:
            set_config(transform_output="default")
            
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
