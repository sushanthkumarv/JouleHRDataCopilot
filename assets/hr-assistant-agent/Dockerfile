FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

# Set working directory to app for execution
WORKDIR /app/app

EXPOSE 5000

CMD ["python", "main.py"]
