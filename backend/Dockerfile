FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for compiling certain packages or postgres support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies including psycopg2-binary explicitly for production Postgres database connectivity
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir psycopg2-binary==2.9.9

COPY . .

EXPOSE 5000

ENV FLASK_ENV=production
ENV FLASK_DEBUG=False

CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
