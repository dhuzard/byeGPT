# backend/Dockerfile
FROM python:3.11-slim

# Install system dependencies for Playwright / Chromium
RUN apt-get update && apt-get install -y \
    libgbm-dev \
    libnss3 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium for Playwright
RUN pip install playwright && playwright install chromium

# Copy the byeGPT source so the core/converter and src/byegpt packages are available
# Note: build context is the repo root (set in docker-compose.yml)
COPY src ./src
COPY core ./core

# Copy the backend application code
COPY . .

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
