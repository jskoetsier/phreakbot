FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for psycopg2, pycurl, and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x phreakbot.py install.py scripts/*.sh

# Set the entrypoint
ENTRYPOINT ["/app/scripts/startup.sh"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "phreakbot.py"]
