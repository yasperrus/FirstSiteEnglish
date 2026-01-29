import nltk

REQUIRED = [
    "stopwords",
    "punkt",
    "averaged_perceptron_tagger",
    "wordnet",
    "omw-1.4",
]

for pkg in REQUIRED:
    try:
        nltk.data.find(pkg)
    except LookupError:
        nltk.download(pkg)
