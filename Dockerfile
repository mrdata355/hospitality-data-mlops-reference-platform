FROM python:3.11-slim
WORKDIR /app
RUN useradd -m appuser
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY artifacts/models ./artifacts/models
ENV PYTHONPATH=/app/src
USER appuser
EXPOSE 8080
CMD ["uvicorn", "hospitality_data_platform.api:app", "--host", "0.0.0.0", "--port", "8080"]
