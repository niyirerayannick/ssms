#!/bin/bash

set -e

echo "=========================================="
echo "SIMS - Starting Application"
echo "=========================================="

# Use environment variables with defaults
DB_ENGINE=${DB_ENGINE:-django.db.backends.sqlite3}
DB_HOST=${DB_HOST:-db}
DB_USER=${DB_USER:-sims_user}
DB_NAME=${DB_NAME:-sims_db}

# Only wait for PostgreSQL if using PostgreSQL database
if [[ "$DB_ENGINE" == *"postgresql"* ]]; then
  echo "Waiting for PostgreSQL to be ready..."
  echo "Host: $DB_HOST, User: $DB_USER, Database: $DB_NAME"

  # Wait for PostgreSQL (with timeout)
  timeout=60
  counter=0
  while ! pg_isready -h $DB_HOST -U $DB_USER -d $DB_NAME 2>/dev/null; do
    if [ $counter -ge $timeout ]; then
      echo "ERROR: PostgreSQL not available after $timeout seconds"
      exit 1
    fi
    echo "Waiting for PostgreSQL... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
  done

  echo "✓ PostgreSQL is ready!"
else
  echo "Using SQLite database (no external database required)"
fi

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py makemigrations --noinput || echo "  → No new migrations to create"
python manage.py migrate --noinput || {
    echo "  ⚠ Migration failed, but continuing..."
}

# Setup groups and permissions
echo ""
echo "Setting up user groups and permissions..."
python manage.py setup_groups || echo "  ⚠ Groups setup skipped (may already exist)"

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "  ⚠ Static files collection skipped"

# Build Tailwind CSS (if needed)
echo ""
echo "Building Tailwind CSS..."
python manage.py tailwind build || echo "  ⚠ Tailwind build skipped (may need manual setup)"

# Create superuser if it doesn't exist (for development)
if [ "$CREATE_SUPERUSER" = "true" ]; then
  echo ""
  echo "Creating default superuser..."
  python manage.py shell << EOF || echo "  ⚠ Superuser creation skipped"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('  ✓ Superuser created: admin/admin123')
else:
    print('  → Superuser already exists')
EOF
fi

echo ""
echo "=========================================="
echo "✓ Setup complete! Starting application..."
echo "=========================================="
echo ""

# Execute the command passed to the container
exec "$@"

