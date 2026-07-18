from sklearn.base import BaseEstimator, clone
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

class ClassParamEstimator(BaseEstimator):
    """A dummy estimator that takes classes as parameters."""
    def __init__(self, my_class_param=None):
        self.my_class_param = my_class_param

def run_test():
    try:
        # Test 1: Single class param
        # The clone function should not attempt to call get_params on the class
        est1 = ClassParamEstimator(my_class_param=StandardScaler)
        cloned1 = clone(est1)
        if cloned1.my_class_param is not StandardScaler:
            return "FAIL", "Single class param not preserved"
            
        # Test 2: List of class params
        # clone recursively processes lists
        est2 = ClassParamEstimator(my_class_param=[StandardScaler, LogisticRegression])
        cloned2 = clone(est2)
        if cloned2.my_class_param != [StandardScaler, LogisticRegression]:
            return "FAIL", "List of class params not preserved"

        # Test 3: Tuple of class params
        # clone recursively processes tuples
        est3 = ClassParamEstimator(my_class_param=(StandardScaler, LogisticRegression))
        cloned3 = clone(est3)
        if cloned3.my_class_param != (StandardScaler, LogisticRegression):
            return "FAIL", "Tuple of class params not preserved"
            
        return "PASS",
    except Exception as e:
        return "ERROR", type(e).__name__

if __name__ == "__main__":
    res = run_test()
    print(f"RESULT={res!r}")
