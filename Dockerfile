# Use a small Python image
FROM python:3.11-slim

# System deps (curl just for quick debugging)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Faster, cleaner Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install runtime deps directly (matches your project)
RUN pip install --no-cache-dir \
    psycopg2-binary>=2.9 \
    scikit-learn>=1.4 \
    pandas>=2.0 \
    joblib>=1.3 \
    requests>=2.31

# Copy project files
COPY cli.py /app/cli.py
COPY src /app/src
COPY model /app/model
COPY mock_flights /app/mock_flights
COPY schema.sql /app/schema.sql

# Default command: start the CLI
ENTRYPOINT ["python", "cli.py"]