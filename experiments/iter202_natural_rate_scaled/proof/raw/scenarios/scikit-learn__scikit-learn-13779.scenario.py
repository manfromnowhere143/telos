from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression

X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
y = [0, 0, 1, 1]

estimator = VotingClassifier(
    estimators=[
        ("lr", LogisticRegression(solver="liblinear")),
        ("disabled", None),
    ]
)
estimator.fit(X, y, sample_weight=[1.0, 1.0, 1.0, 1.0])

print("RESULT=" + repr("fit-ok"))
