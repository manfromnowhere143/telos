try:
    from sklearn.svm import SVC
    from sklearn.feature_selection import SelectKBest, f_regression
    from sklearn.pipeline import Pipeline

    anova = SelectKBest(f_regression, k=5)
    clf = SVC(kernel='linear')
    pipe = Pipeline([('anova', anova), ('svc', clf)])

    n = len(pipe)
    if n != 2:
        print(f"RESULT={('FAIL', 'len should be 2 got ' + str(n))!r}")
    else:
        sub = pipe[:len(pipe)]
        if not isinstance(sub, Pipeline):
            print(f"RESULT={('FAIL', 'slice not Pipeline')!r}")
        elif len(sub) != 2:
            print(f"RESULT={('FAIL', 'sliced len ' + str(len(sub)))!r}")
        else:
            names = [name for name, _ in sub.steps]
            if names != ['anova', 'svc']:
                print(f"RESULT={('FAIL', 'names ' + str(names))!r}")
            else:
                pipe3 = Pipeline([('a', SelectKBest(f_regression, k=3)),
                                  ('b', SelectKBest(f_regression, k=4)),
                                  ('c', SVC())])
                if len(pipe3) != 3:
                    print(f"RESULT={('FAIL', 'len3 ' + str(len(pipe3)))!r}")
                elif len(pipe3[:2]) != 2:
                    print(f"RESULT={('FAIL', 'slice2 len')!r}")
                else:
                    print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
