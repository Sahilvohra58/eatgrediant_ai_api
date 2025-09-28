# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and directories
COPY main.py .
COPY utils/ ./utils/
COPY prompts/ ./prompts/

# Expose the port that Cloud Run will use
EXPOSE 8080

# Set environment variable for port (Cloud Run uses 8080 by default)
ENV PORT=8080

# Command to run the application
CMD ["python", "main.py"]
