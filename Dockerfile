# Hugging Face Spaces & Production Dockerfile for Instagram Video Downloader
FROM python:3.11-slim

# Install system dependencies (FFmpeg for video/audio remuxing & transcoding)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up user for Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user:user . .

# Ensure app directory & downloads folder have write permissions
RUN mkdir -p /app/downloads && chmod -R 777 /app

USER user

# Hugging Face Spaces listens on port 7860 by default
ENV PORT=7860
EXPOSE 7860

# Run FastAPI with Uvicorn
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
