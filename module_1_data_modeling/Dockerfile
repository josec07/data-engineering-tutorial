FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    psycopg2-binary==2.9.7 \
    sqlalchemy==2.0.20

# Copy application files
COPY . .

# Default command runs tests
CMD ["python", "test_module1.py"]
