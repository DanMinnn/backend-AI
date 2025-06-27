
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first để tận dụng Docker layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]