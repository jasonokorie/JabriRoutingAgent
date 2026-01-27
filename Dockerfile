# -----------------------------
# Base image
# -----------------------------
FROM python:3.11-slim

# -----------------------------
# Environment setup
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# NOTE: Do NOT bake secrets into the image. Pass keys at runtime instead
# Use `docker run -e GOOGLE_API_KEY=...` or `--env-file .env` when starting the container.

# Set working directory inside container
WORKDIR /app

# -----------------------------
# Install system dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Install Python dependencies
# -----------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Copy project files
# -----------------------------
COPY . .

# Copy entrypoint for debug + run
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# -----------------------------
# Expose ADK Web UI port
# -----------------------------
EXPOSE 8000

# -----------------------------
# Default command
# -----------------------------
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
# Bind to 0.0.0.0 so the service is reachable from the host
CMD ["adk", "web", ".", "--host", "0.0.0.0", "--port", "8000"]
