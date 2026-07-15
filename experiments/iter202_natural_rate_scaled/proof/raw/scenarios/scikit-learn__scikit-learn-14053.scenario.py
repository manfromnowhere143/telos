from sklearn.tree import DecisionTreeClassifier, export_text


class FeatureNames(list):
    def __init__(self):
        super().__init__(["sentinel"])
        self.calls = 0

    def __bool__(self):
        self.calls += 1
        return self.calls == 1


tree = DecisionTreeClassifier(random_state=0).fit([[0], [1]], [0, 1])
print("RESULT=" + repr(export_text(tree, feature_names=FeatureNames())))
