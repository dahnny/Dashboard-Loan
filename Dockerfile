FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client --no-install-recommends \
    gcc build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8000

RUN chmod +x scripts/*.sh start.sh

# Default command (API)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]