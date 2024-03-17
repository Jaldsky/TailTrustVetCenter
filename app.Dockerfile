FROM python:3.9

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=main.settings
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV BOT_TOKEN={token}
ENV PROD=1

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
