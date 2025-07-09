# Use a lightweight official Python base image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Install OS-level build dependencies (if you need them)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip & install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Optional: set PYTHONPATH to help with absolute imports
ENV PYTHONPATH=/app

# Expose FastAPI default port
EXPOSE 8000

# Run the FastAPI app
# Update `app.main:app` if your entry file or variable name is different!
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7001"]
