#!/bin/sh

# Cek apakah variabel DB_HOST dan DB_PORT sudah ada
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
  echo "Error: DB_HOST or DB_PORT is not set. Please check your .env file."
  exit 1
fi

echo "Waiting for postgres..."

# Loop sampai koneksi ke database berhasil
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done

echo "PostgreSQL started"

# Jalankan perintah utama dari Dockerfile (misal: python manage.py runserver)
exec "$@"