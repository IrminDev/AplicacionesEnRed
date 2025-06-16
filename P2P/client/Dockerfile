FROM python:3.13.5-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    libssl-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Install required packages
RUN pip install libtorrent requests

# Start client
CMD ["python", "client.py"]