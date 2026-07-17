from sklearn.ensemble import VotingClassifier
from sklearn.tree import DecisionTreeClassifier

X = [[0], [1]]
y = [0, 1]

model = VotingClassifier(
    estimators=[
        ("removed", None),
        ("tree", DecisionTreeClassifier(random_state=0)),
    ]
)
model.fit(X, y, sample_weight=[1.0, 1.0])

print("RESULT=" + repr(model.predict(X).tolist()))
