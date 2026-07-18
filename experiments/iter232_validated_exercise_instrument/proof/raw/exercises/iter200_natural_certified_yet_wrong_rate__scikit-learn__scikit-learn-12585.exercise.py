try:
    from sklearn.base import BaseEstimator, clone
    from sklearn.preprocessing import MinMaxScaler, StandardScaler

    class Holder(BaseEstimator):
        def __init__(self, estimator=None):
            self.estimator = estimator

    scaler_clone = clone(StandardScaler(with_mean=StandardScaler))
    holder_clone = clone(Holder(estimator=StandardScaler))
    nested_clone = clone(Holder(estimator=(StandardScaler, MinMaxScaler)))

    result = (
        "OK",
        scaler_clone.get_params(deep=False)["with_mean"] is StandardScaler,
        holder_clone.estimator is StandardScaler,
        nested_clone.estimator == (StandardScaler, MinMaxScaler),
        clone(StandardScaler, safe=False) is StandardScaler,
    )
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print("RESULT=" + repr(result))
