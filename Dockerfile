FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for compiling packages if necessary
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure entrypoint script is executable
RUN chmod +x entrypoint.sh

ENV PORT=8000
EXPOSE ${PORT}

CMD ["./entrypoint.sh"]
