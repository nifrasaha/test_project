FROM python:3.11-slim-bullseye@sha256:<latest-sha>

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download medical models
RUN python -m spacy download en_core_web_md
RUN python -m spacy download en_ner_bc5cdr_md

# Copy application
COPY . .

# Set environment variables
ENV ENCRYPTION_KEY=your_encryption_key_here

# Expose port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "src/main.py", "--server.port=8501", "--server.address=0.0.0.0"]