FROM python:3.9.18-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE 'app.settings'
COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

WORKDIR /code
COPY src ./src
WORKDIR /code/src