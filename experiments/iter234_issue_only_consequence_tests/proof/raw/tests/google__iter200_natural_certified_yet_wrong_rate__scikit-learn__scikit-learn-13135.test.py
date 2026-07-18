import warnings

def run_tests():
    from sklearn.preprocessing import KBinsDiscretizer
    
    datasets = [
        [[0], [0.5], [2], [3], [9], [10]],
        [[4], [1], [9], [3], [0], [8], [2], [5], [7], [6]],
        [[12.5], [1.2], [5.5], [7.3], [0.5], [9.1], [8.8], [10.4], [2.3], [3.4]]
    ]
    
    for i, X in enumerate(datasets):
        for n_bins in [3, 4, 5, 6, 8]:
            if n_bins > len(X):
                continue
                
            est = KBinsDiscretizer(n_bins=n_bins, strategy='kmeans', encode='ordinal')
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    est.fit_transform(X)
                except ValueError as e:
                    if "monotonically" in str(e).lower() or "sorted" in str(e).lower():
                        return "FAIL", f"ValueError with n_bins {n_bins}: {e}"
                    raise e
                    
            edges = est.bin_edges_[0]
            if not all(edges[k] <= edges[k+1] for k in range(len(edges)-1)):
                return "FAIL", f"Unsorted bin_edges_ found: {edges}"

    return "PASS", ""

try:
    res, msg = run_tests()
    if res == "PASS":
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', msg)!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
