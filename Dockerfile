FROM python:3.13-slim

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Скачиваем NLTK ресурсы
RUN python -m nltk.downloader -d /usr/share/nltk_data stopwords punkt wordnet omw-1.4 averaged_perceptron_tagger

ENV NLTK_DATA=/usr/share/nltk_data

