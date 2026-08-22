FROM python:3.13-slim

WORKDIR /app

# Copy just the requirements file first so Docker caches this layer separately —
# rebuilds only reinstall dependencies when requirements.txt actually changes,
# not on every source code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
