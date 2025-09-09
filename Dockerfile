# Dockerfile

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# TAMBAHKAN INI: Install netcat untuk memeriksa koneksi
RUN apt-get update && apt-get install -y netcat-openbsd

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# TAMBAHKAN INI: Salin skrip entrypoint
COPY ./entrypoint.sh /app/entrypoint.sh

COPY . /app/

# TAMBAHKAN INI: Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]