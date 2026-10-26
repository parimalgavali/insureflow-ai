FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml ./
COPY triage_service ./triage_service
RUN pip install --no-cache-dir .
EXPOSE 8001
CMD ["uvicorn", "triage_service.app:app", "--host", "0.0.0.0", "--port", "8001"]
