# Use official Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create working directory
WORKDIR /app

# ------------------------------
# Install system dependencies
# ------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    libpango-1.0-0 \
    libcairo2 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libxml2 \
    libxslt1.1 \
    libffi-dev \
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
