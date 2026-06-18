FROM python:3.13-alpine

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system utilities needed for compiling metrics dependencies (psutil)
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    musl-dev \
    python3-dev \
    linux-headers

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clean up compile packages to minimize image footprint
RUN apk del .build-deps

# Copy source and configurations
COPY src/ ./src
COPY config/ ./config
COPY extensions/ ./extensions

# Copy and set entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose the API port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
