FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for pycurl and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x phreakbot.py install.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "phreakbot.py"]
