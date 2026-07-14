from sklearn.feature_extraction.text import CountVectorizer

vectorizer = CountVectorizer(vocabulary=("zeta", "alpha"))
print("RESULT=" + repr(vectorizer.get_feature_names()))
