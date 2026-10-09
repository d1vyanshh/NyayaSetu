FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY precedent_module/requirements.txt /app/precedent_module/requirements.txt
RUN pip install --no-cache-dir -r /app/precedent_module/requirements.txt

COPY precedent_module /app/precedent_module
COPY case_corpus /app/case_corpus

WORKDIR /app/precedent_module

EXPOSE 8501

CMD ["/bin/sh", "-c", "if [ ! -f data/bm25_index.pkl ]; then python index_cases.py --reset || exit 1; fi; streamlit run app.py --server.address=0.0.0.0 --server.port=8501"]
