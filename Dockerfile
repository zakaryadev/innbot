FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables to avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Auto-create DB and start bot
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
