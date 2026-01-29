import nltk

REQUIRED = {
    "corpora/stopwords": "stopwords",
    "tokenizers/punkt": "punkt",
    "taggers/averaged_perceptron_tagger": "averaged_perceptron_tagger",
    "corpora/wordnet": "wordnet",
    "corpora/omw-1.4": "omw-1.4",
}

for resource_path, package_name in REQUIRED.items():
    try:
        nltk.data.find(resource_path)
    except LookupError:
        nltk.download(package_name)
