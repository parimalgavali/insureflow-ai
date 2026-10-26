FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml ./
COPY rag_service ./rag_service
RUN pip install --no-cache-dir .
EXPOSE 8003
CMD ["uvicorn", "rag_service.app:app", "--host", "0.0.0.0", "--port", "8003"]
