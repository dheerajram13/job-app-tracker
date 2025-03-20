FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy model
RUN pip install --no-cache-dir spacy && \
    python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Make the start script executable
COPY start.sh .
RUN chmod +x start.sh

# Command to run the application
CMD ["./start.sh"]