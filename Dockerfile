FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
# WeasyPrint/Pango dependencies for Debian 12 (Bookworm)
# Note: package names must match Bookworm repositories
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libgobject-2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libxcb1 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
