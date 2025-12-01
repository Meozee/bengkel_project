#!/bin/sh

# Cek apakah variabel environment tersedia
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
    echo "❌ ERROR: DB_HOST atau DB_PORT tidak di-set. Periksa file .env kamu!"
    exit 1
fi

echo "🔄 Menunggu PostgreSQL di $DB_HOST:$DB_PORT ..."

# Tunggu sampai PostgreSQL siap
while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.5
done

echo "✅ PostgreSQL sudah siap!"

# Jalankan migrate
echo "🚀 Jalankan migrate..."
python manage.py migrate --noinput

# Jalankan perintah utama (runserver)
echo "✨ Menjalankan server..."
exec "$@"
