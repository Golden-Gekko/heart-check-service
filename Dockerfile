FROM python:3.9-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Java 11 берём из готового образа Temurin.
COPY --from=eclipse-temurin:11-jre /opt/java/openjdk /opt/java/openjdk

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="/opt/java/openjdk/bin:${PATH}"

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Копирование зависимостей
COPY pyproject.toml uv.lock ./

# Установка production зависимостей
RUN uv sync --no-dev --no-install-project

# Копирование исходного кода и датасета для обучения
COPY app ./app
COPY scripts ./scripts
COPY dags ./dags
COPY data ./data

# Обучение heart-модели и регистрация в локальном MLflow (file backend).
RUN uv run --no-dev python scripts/train_heart.py

# Проверка работоспособности
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c 'import urllib.request; urllib.request.urlopen("http://localhost:8000/health", timeout=10)'

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
