
FROM python:3.9-slim

# Optimizaciones para construcción más rápida
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONPATH=/

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Puerto por defecto
ENV PORT_BE=8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
