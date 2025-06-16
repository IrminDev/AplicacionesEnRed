FROM python:3.13.5-slim

RUN apt-get update && apt-get install -y \
    libssl-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install libtorrent requests

CMD ["python", "server.py"]