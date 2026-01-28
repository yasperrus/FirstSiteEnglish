FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# установить postgresql-client
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# сделать entrypoint исполняемым
RUN chmod +x entrypoint.sh

# собрать статику (если нужно)
RUN python manage.py collectstatic --noinput

# запуск через entrypoint
ENTRYPOINT ["./entrypoint.sh"]
