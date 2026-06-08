FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install poetry==1.8.0
RUN poetry config virtualenvs.create false

# Dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Source code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Non-root user
RUN useradd -m -u 1000 brujula && chown -R brujula:brujula /app
USER brujula

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
