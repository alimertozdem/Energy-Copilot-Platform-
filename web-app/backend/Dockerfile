# EnergyLens backend — FastAPI + pyodbc (Fabric SQL via ODBC Driver 18)
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# --- System deps: Microsoft ODBC Driver 18 (for pyodbc -> Fabric SQL endpoint) ---
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl gnupg ca-certificates apt-transport-https build-essential libffi-dev unixodbc-dev \
 && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng tesseract-ocr-tur \
 && apt-get purge -y --auto-remove curl gnupg apt-transport-https \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# App source
COPY . .

EXPOSE 8000
# Start directly (no start.sh dependency — avoids CRLF/truncation issues with the script file).
# Migrations are best-effort; then exec uvicorn so it becomes PID 1 and receives signals.
CMD ["sh", "-c", "alembic upgrade head || echo '[start] alembic skipped (continuing)'; exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
