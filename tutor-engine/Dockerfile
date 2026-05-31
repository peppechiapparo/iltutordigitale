# syntax=docker/dockerfile:1.6
# ARM64 / ARMv7-compatible image for Raspberry Pi.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Europe/Rome

# Minimal runtime deps (lxml needs libxml2/libxslt at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libxml2 \
        libxslt1.1 \
        tzdata \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

# Non-root user
RUN groupadd -r tutor && useradd -r -g tutor -m -d /home/tutor tutor

WORKDIR /app

# Install dependencies first for better layer caching
COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations

# Build deps required only at install time (then purged)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc libxml2-dev libxslt1-dev \
    && pip install --upgrade pip \
    && pip install . \
    && apt-get purge -y build-essential gcc libxml2-dev libxslt1-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/data /app/secrets && chown -R tutor:tutor /app
USER tutor

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8765/healthz || exit 1

ENTRYPOINT ["tutor"]
CMD ["serve"]
