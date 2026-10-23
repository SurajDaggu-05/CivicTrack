FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DB_PATH=/data/civictrack.db

WORKDIR /app
RUN groupadd --system appuser && useradd --system --gid appuser --home-dir /app appuser \
    && mkdir -p /data && chown -R appuser:appuser /app /data

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates ./templates
COPY static ./static
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)" || exit 1
CMD ["python", "app.py"]
