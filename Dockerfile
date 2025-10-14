# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (netcat for entrypoint script)
RUN apt-get update && apt-get install -y netcat-openbsd

# Install python dependencies
COPY ./requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY ./entrypoint.sh /app/entrypoint.sh

# Copy project
COPY . /app/

# Run entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]