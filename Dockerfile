FROM python:3.9.18-slim-bullseye

ENV PYTHONUNBUFFERED 1

WORKDIR /code
COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .