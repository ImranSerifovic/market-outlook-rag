FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

# Copy app + ingestion utils + prebuilt Chroma index
COPY apps/api /app/apps/api
COPY ingestion /app/ingestion

ENV PYTHONPATH=/app
EXPOSE 8000

# Use Render's PORT if provided, otherwise 8000 for local
CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]