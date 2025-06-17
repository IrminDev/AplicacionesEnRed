FROM python:3.13.5-slim

WORKDIR /app
COPY client.py .

RUN pip install requests tqdm

CMD ["python", "client.py"]