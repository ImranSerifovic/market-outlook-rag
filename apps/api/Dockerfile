FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

# Copy app + ingestion utils + data
COPY apps/api /app/apps/api
COPY ingestion /app/ingestion
COPY data /app/data

# Copy startup script and make it executable
COPY apps/api/start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV PYTHONPATH=/app
EXPOSE 8000

# Create storage directory
RUN mkdir -p /app/storage/chroma

# Use startup script that builds index if needed
CMD ["/app/start.sh"]