from sklearn.ensemble import VotingClassifier
from sklearn.tree import DecisionTreeClassifier

model = VotingClassifier(
    estimators=[
        ("tree", DecisionTreeClassifier(random_state=0)),
        ("unused", None),
    ]
)

try:
    model.fit([[0], [1]], [0, 1], sample_weight=[1, 1])
    result = len(model.estimators_)
except Exception as exc:
    result = type(exc).__name__

print("RESULT=" + repr(result))
