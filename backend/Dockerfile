FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads

# Run migrations then start server
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed.seeder && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
