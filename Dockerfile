FROM python:3.11-slim

# evitar archivos .pyc y habilitar salida de logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# instalar dependencias de python
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# copiar el resto del proyecto
COPY . .

# crear carpetas de datos si no existen
RUN mkdir -p data/raw data/interim data/processed

CMD ["python", "-m", "src.main"]
