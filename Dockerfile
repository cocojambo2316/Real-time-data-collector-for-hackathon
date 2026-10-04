FROM python:3.11-slim

WORKDIR /app

# Set environment variable to ensure Python output is sent straight to terminal (unbuffered)
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "vacum.py"]