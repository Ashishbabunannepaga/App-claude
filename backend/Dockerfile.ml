# ML worker: PaddleOCR + self-hosted embeddings (bge-m3). Runs the same Celery tasks as the main
# worker, with OCR_PROVIDER=paddle and EMBEDDING_PROVIDER=local. Python 3.10.11 per the tech-stack brief.
FROM python:3.10.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-hin libgomp1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-ml.txt
COPY . .

# Download the embedding model at build time so workers start fast and offline.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

RUN useradd --create-home appuser
USER appuser
ENV OCR_PROVIDER=paddle EMBEDDING_PROVIDER=local
CMD ["celery", "-A", "app.workers.celery_app", "worker", "-l", "info", "--concurrency", "2"]
