FROM python:3.10-slim-bookworm

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Remove build tools to reduce vulnerabilities
RUN apt-get purge -y gcc && apt-get autoremove -y

COPY . .

CMD ["streamlit", "run", "src/main.py", "--server.port=8501", "--server.address=0.0.0.0"]