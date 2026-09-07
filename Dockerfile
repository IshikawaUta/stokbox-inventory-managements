FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create uploads directory
RUN mkdir -p static/uploads/barang static/uploads/users static/uploads/settings

ENV PORT=8000
EXPOSE ${PORT}

CMD ["sh", "-c", "fenrir run app:app --host 0.0.0.0 --port ${PORT} --workers 4 --disable-dashboard"]
