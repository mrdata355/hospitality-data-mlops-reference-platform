FROM python:3.14-slim

ARG SERVICE_VERSION=1.1.0
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="Hospitality Member Risk API" \
      org.opencontainers.image.description="Production-style member risk scoring service" \
      org.opencontainers.image.source="https://github.com/mrdata355/hospitality-data-mlops-reference-platform" \
      org.opencontainers.image.version="${SERVICE_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src \
    APP_ENV=container \
    SERVICE_VERSION=${SERVICE_VERSION} \
    BUILD_SHA=${VCS_REF}

WORKDIR /app

RUN useradd --create-home --uid 10001 --user-group appuser
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY artifacts/models ./artifacts/models

USER 10001:10001
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/ready', timeout=3)"

CMD ["uvicorn", "hospitality_data_platform.api:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--no-server-header"]
