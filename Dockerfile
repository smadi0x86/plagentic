FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    libnspr4 \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libcups2 \
    libxfixes3 \
    libcairo2 \
    libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY . .

RUN uv pip install --system -e .[full]

RUN python -m playwright install chromium

# Create workspace directory but stay in /app
RUN mkdir -p /workspace

# (Not used yet, future web UI)
EXPOSE 8080

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Stay in /app directory for proper path resolution
WORKDIR /app

CMD ["plagentic", "--help"]