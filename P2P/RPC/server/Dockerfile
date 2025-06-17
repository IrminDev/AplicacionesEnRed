FROM python:3.13.5-slim

WORKDIR /app
COPY . .

# Install dependencies
RUN pip install flask gunicorn

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "server:app"]