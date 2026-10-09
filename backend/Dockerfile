FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY . /app
RUN mkdir -p /app/backend/corpus \
    && if [ -d /app/corpus ]; then cp -R /app/corpus/. /app/backend/corpus/; fi

WORKDIR /app/backend

EXPOSE 5555

CMD ["gunicorn", "--bind", "0.0.0.0:5555", "--workers", "2", "--worker-class", "gthread", "--threads", "4", "--timeout", "120", "app:app"]
