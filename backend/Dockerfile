FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (build-essential, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application and migration scripts into backend package directory
COPY . backend/

# Expose port
EXPOSE 8000

# Run migrations and start uvicorn
CMD ["sh", "-c", "cd /app/backend && alembic upgrade head && cd /app && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
