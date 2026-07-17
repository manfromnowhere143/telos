from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import CountVectorizer

vectorizer = CountVectorizer(vocabulary={"token": 0})
vectorizer.get_feature_names()
result = [row.tolist() for row in vectorizer.inverse_transform(csr_matrix([[1]]))]
print("RESULT=" + repr(result))
