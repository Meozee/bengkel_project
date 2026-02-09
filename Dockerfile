# Use official Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc & Enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create working directory
WORKDIR /app

# ------------------------------
# Install system dependencies
# ------------------------------
# netcat: untuk cek database
# build-essential & libpq-dev: untuk compile python/postgres driver
# library grafis (pango, cairo, dll): WAJIB untuk WeasyPrint PDF
# libusb: untuk printer thermal
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    build-essential \
    libpq-dev \
    python3-dev \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    libusb-1.0-0 \
    libusb-1.0-0-dev \
    usbutils \
    fonts-liberation \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# Install python dependencies
# ------------------------------
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ------------------------------
# Copy entrypoint script
# ------------------------------
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# ------------------------------
# Copy project
# ------------------------------
COPY . /app/

# ------------------------------
# Entry point
# ------------------------------
ENTRYPOINT ["/app/entrypoint.sh"]