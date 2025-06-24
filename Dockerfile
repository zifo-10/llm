FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Optional: set PYTHONPATH to use absolute imports like `from app.knowledge_base...`
ENV PYTHONPATH=/app

# Expose FastAPI default port
EXPOSE 8000

# Run the FastAPI app (note: `app.main:app`, not `main:app`)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7001"]
