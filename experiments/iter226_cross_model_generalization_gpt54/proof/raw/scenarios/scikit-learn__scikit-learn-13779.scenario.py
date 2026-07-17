from sklearn.ensemble import VotingClassifier
from sklearn.tree import DecisionTreeClassifier

model = VotingClassifier(
    estimators=[
        ("tree", DecisionTreeClassifier(random_state=0)),
        ("missing", None),
    ],
    voting="hard",
)

model.fit([[0], [1]], [0, 1], sample_weight=[1.0, 1.0])

print("RESULT=" + repr(len(model.estimators_)))
