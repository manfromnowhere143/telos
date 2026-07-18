try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.base import clone

    # Cloning an estimator that has a class (type) as a parameter value
    original = StandardScaler(with_mean=StandardScaler)
    cloned = clone(original)

    detail = None

    # The class parameter should be preserved as the same class object
    params = cloned.get_params(deep=False)
    if params.get("with_mean") is not StandardScaler:
        detail = "class param not preserved"

    # The clone should be a distinct object but equal in params
    if detail is None and cloned is original:
        detail = "clone returned same object"

    # A class parameter passed directly to clone(safe=False) should be returned as-is
    if detail is None:
        result = clone(StandardScaler, safe=False)
        if result is not StandardScaler:
            detail = "class not returned unchanged"

    # Regular cloning still works for nested estimator instances
    if detail is None:
        nested = StandardScaler(with_mean=StandardScaler(with_std=False))
        c2 = clone(nested)
        inner = c2.get_params(deep=False)["with_mean"]
        if not isinstance(inner, StandardScaler):
            detail = "nested instance not cloned"
        elif inner.with_std is not False:
            detail = "nested param lost"

    if detail is None:
        print(f"RESULT={('PASS',)!r}")
    else:
        print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
