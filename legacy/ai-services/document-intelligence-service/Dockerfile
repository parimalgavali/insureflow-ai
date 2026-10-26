FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml ./
COPY document_intelligence ./document_intelligence
RUN pip install --no-cache-dir .
EXPOSE 8002
CMD ["uvicorn", "document_intelligence.app:app", "--host", "0.0.0.0", "--port", "8002"]
