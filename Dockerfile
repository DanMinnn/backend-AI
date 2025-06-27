
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first để tận dụng Docker layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir --no-deps \
    fastapi uvicorn python-dotenv pypdf \
    && pip install --no-cache-dir \
    langchain langchain-community langchain-groq langchain-huggingface \
    faiss-cpu sentence-transformers

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]