#!/bin/sh

# Hentikan script jika terjadi error
set -e

# Cek apakah variabel environment tersedia (Optional Warning)
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
    echo "⚠️  WARNING: DB_HOST atau DB_PORT tidak di-set di environment variables."
fi

# Cek ketersediaan host db hanya jika variabel di-set
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
    echo "🔄 Menunggu PostgreSQL di $DB_HOST:$DB_PORT ..."
    
    # Tunggu sampai PostgreSQL siap
    while ! nc -z "$DB_HOST" "$DB_PORT"; do
        sleep 0.5
    done
    
    echo "✅ PostgreSQL sudah siap!"
fi

# Jalankan migrate database
echo "🚀 Jalankan migrate..."
python manage.py migrate --noinput

# (Optional) Collect Static files (aktifkan jika production)
# echo "📦 Collect static files..."
# python manage.py collectstatic --noinput

# Jalankan perintah utama (runserver/gunicorn)
echo "✨ Menjalankan server..."
exec "$@"