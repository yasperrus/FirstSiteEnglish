import os
import nltk

# Определяем корень проекта (один уровень выше apps/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NLTK_DATA_DIR = os.path.join(BASE_DIR, "nltk_data")

# Добавляем папку nltk_data в путь поиска
nltk.data.path.append(NLTK_DATA_DIR)

# Список необходимых ресурсов
REQUIRED = ["stopwords", "punkt", "averaged_perceptron_tagger", "wordnet", "omw-1.4"]

# Проверяем, что все ресурсы есть
for pkg in REQUIRED:
    try:
        if pkg in ["stopwords", "wordnet", "omw-1.4"]:
            nltk.data.find(f"corpora/{pkg}")
        elif pkg == "punkt":
            nltk.data.find(f"tokenizers/{pkg}")
        else:
            nltk.data.find(f"taggers/{pkg}")
    except LookupError:
        raise RuntimeError(f"NLTK пакет {pkg} не найден в {NLTK_DATA_DIR}")
