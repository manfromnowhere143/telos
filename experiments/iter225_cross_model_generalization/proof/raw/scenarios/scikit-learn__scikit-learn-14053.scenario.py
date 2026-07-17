from sklearn.tree import DecisionTreeClassifier, export_text

tree = DecisionTreeClassifier(random_state=0).fit([[0], [1]], [0, 0])
output = export_text(tree, feature_names=["x"])
print("RESULT=" + repr(output))
