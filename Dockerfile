# DocTR Process Dockerfile with Tesseract and Poppler
FROM python:3.10-slim

# Install system dependencies: Tesseract and Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install the package
RUN pip install -e .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash doctr && \
    chown -R doctr:doctr /app
USER doctr

# Set up logging directory
RUN mkdir -p /app/logs

# Expose potential port for future web interface
EXPOSE 8080

# Default command - runs the CLI help
CMD ["doctr-process", "--version"]