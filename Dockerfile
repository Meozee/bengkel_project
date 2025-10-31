# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# --- Install system dependencies ---
# Includes WeasyPrint dependencies (Cairo, Pango, GDK, etc)
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    libpango-1.0-0 \
    libcairo2 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    fonts-liberation \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# --- Install python dependencies ---
COPY ./requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# --- Copy entrypoint script ---
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# --- Copy project ---
COPY . /app/

# --- Run entrypoint.sh ---
ENTRYPOINT ["/app/entrypoint.sh"]
