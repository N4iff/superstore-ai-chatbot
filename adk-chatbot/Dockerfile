FROM python:3.11-slim-bookworm

WORKDIR /app

# Install CPU-only torch first (saves ~1.5GB vs full torch)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Remove files that shouldn't be in the image
RUN rm -rf .adk_env .DS_Store __pycache__

EXPOSE 8000

CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000"]
