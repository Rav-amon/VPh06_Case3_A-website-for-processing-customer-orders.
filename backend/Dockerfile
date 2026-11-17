FROM python:3.12-slim-bookworm

# Слушает сеть Docker. На хост этот порт не пробрасывается.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

COPY app ./app

USER 65534:65534

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
